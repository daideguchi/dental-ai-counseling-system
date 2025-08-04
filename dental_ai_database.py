#!/usr/bin/env python3
"""
歯科カウンセリングAIツール - データベース中心版
予約CSV → 音声データ突合 → 全会話記録 → DB保存 → SOAP変換 → DB保存
"""

import sqlite3
import csv
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

class DentalCounselingDatabase:
    def __init__(self, db_path: str = "dental_counseling.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        
        # データベースが既に存在するかチェック
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
        exists = cursor.fetchone()
        
        if not exists:
            # スキーマファイルを読み込んで実行
            if os.path.exists('database_schema.sql'):
                with open('database_schema.sql', 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                    conn.executescript(schema_sql)
                print(f"✅ データベース初期化完了: {self.db_path}")
            else:
                print(f"⚠️ スキーマファイルが見つかりません")
        else:
            print(f"✅ 既存データベースを使用: {self.db_path}")
        
        conn.close()
    
    def load_appointments_from_csv(self, csv_file: str) -> List[Dict]:
        """予約システムCSVを読み込んでデータベースに保存"""
        appointments = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                appointments = list(reader)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 既存データをクリア（デモ用）
            cursor.execute("DELETE FROM appointments")
            
            # 新しいデータを挿入
            for apt in appointments:
                cursor.execute("""
                    INSERT INTO appointments 
                    (appointment_id, patient_id, patient_name, doctor_id, doctor_name, 
                     scheduled_datetime, treatment_type, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'scheduled')
                """, (
                    apt['予約ID'], apt['患者ID'], apt['患者名'], 
                    apt['担当医ID'], apt['担当医名'], apt['予約日時'], apt['治療内容']
                ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ 予約データをデータベースに保存: {len(appointments)}件")
            return appointments
            
        except FileNotFoundError:
            print(f"❌ ファイルが見つかりません: {csv_file}")
            return []
    
    def create_counseling_session(self, recording_metadata: Dict) -> Optional[str]:
        """カウンセリングセッションを作成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 予約データから患者・医師を特定
        recording_time = datetime.strptime(recording_metadata['start_time'], "%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            SELECT appointment_id, patient_id, patient_name, doctor_id, doctor_name
            FROM appointments 
            WHERE doctor_id = ? 
            AND ABS((julianday(scheduled_datetime) - julianday(?)) * 24 * 60) <= 5
        """, (recording_metadata['doctor_id'], recording_metadata['start_time']))
        
        appointment = cursor.fetchone()
        
        if not appointment:
            print("❌ 該当する予約が見つかりませんでした")
            conn.close()
            return None
        
        # セッション作成
        session_id = f"SESSION_{uuid.uuid4().hex[:8]}"
        
        cursor.execute("""
            INSERT INTO counseling_sessions 
            (session_id, appointment_id, patient_id, doctor_id, 
             recording_start_time, audio_file_path, device_id, session_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'in_progress')
        """, (
            session_id, appointment[0], appointment[1], appointment[3],
            recording_metadata['start_time'], 
            recording_metadata.get('audio_file', ''),
            recording_metadata.get('device_id', '')
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ セッション作成: {session_id}")
        print(f"   患者: {appointment[2]} (ID: {appointment[1]})")
        print(f"   医師: {appointment[4]} (ID: {appointment[3]})")
        
        return session_id
    
    def save_conversation_records(self, session_id: str, transcript_data: List[Dict]) -> bool:
        """会話記録を全てデータベースに保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for i, record in enumerate(transcript_data):
                cursor.execute("""
                    INSERT INTO conversation_records 
                    (session_id, sequence_number, speaker, speaker_name, 
                     timestamp_start, timestamp_end, original_text, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id, i + 1,
                    'patient' if record['speaker'] == '患者' else 'doctor',
                    record['speaker'],
                    record.get('timestamp', ''),
                    record.get('timestamp_end', ''),
                    record['text'],
                    record.get('confidence', 0.95)  # デフォルト信頼度
                ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ 会話記録をデータベースに保存: {len(transcript_data)}発言")
            return True
            
        except Exception as e:
            print(f"❌ 会話記録保存エラー: {e}")
            conn.close()
            return False
    
    def generate_and_save_soap(self, session_id: str) -> Optional[Dict]:
        """データベースから会話記録を読み込んでSOAP形式に変換・保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 会話記録を取得
        cursor.execute("""
            SELECT speaker, original_text, sequence_number
            FROM conversation_records 
            WHERE session_id = ?
            ORDER BY sequence_number
        """, (session_id,))
        
        records = cursor.fetchall()
        
        if not records:
            print("❌ 会話記録が見つかりません")
            conn.close()
            return None
        
        # SOAP要素を抽出
        soap_elements = self._extract_soap_from_records(records)
        
        # SOAPデータをデータベースに保存
        soap_id = f"SOAP_{uuid.uuid4().hex[:8]}"
        
        cursor.execute("""
            INSERT INTO soap_records 
            (soap_id, session_id, subjective_text, objective_text, 
             assessment_text, plan_text, generation_method, reviewed_by_doctor)
            VALUES (?, ?, ?, ?, ?, ?, 'ai_generated', FALSE)
        """, (
            soap_id, session_id,
            soap_elements['S'], soap_elements['O'],
            soap_elements['A'], soap_elements['P']
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ SOAP記録をデータベースに保存: {soap_id}")
        
        return {
            'soap_id': soap_id,
            'session_id': session_id,
            'soap_note': soap_elements
        }
    
    def _extract_soap_from_records(self, records: List[Tuple]) -> Dict:
        """データベースの会話記録からSOAP要素を抽出"""
        soap = {'S': [], 'O': [], 'A': [], 'P': []}
        
        # 歯科専門用語キーワード
        keywords = {
            'subjective': ['痛い', 'しみる', '違和感', '気になる', '腫れ', 'ズキズキ', 'キーン'],
            'objective': ['う蝕', '歯髄', '打診痛', '冷水痛', '歯肉', '歯石', '動揺', '認める'],
            'assessment': ['診断', '虫歯', '歯周病', '根尖病変', '咬合', '深い', '神経'],
            'plan': ['治療', '充填', '抜歯', '根管治療', '予約', 'CR', 'インレー', '次回']
        }
        
        for speaker, text, seq_num in records:
            # S: 患者の主観的症状
            if speaker == 'patient':
                for keyword in keywords['subjective']:
                    if keyword in text:
                        soap['S'].append(text)
                        break
            
            # O: 医師の客観的所見
            elif speaker == 'doctor':
                for keyword in keywords['objective']:
                    if keyword in text:
                        soap['O'].append(text)
                        break
                
                # A: 診断・評価
                for keyword in keywords['assessment']:
                    if keyword in text:
                        soap['A'].append(text)
                        break
                
                # P: 治療計画
                for keyword in keywords['plan']:
                    if keyword in text:
                        soap['P'].append(text)
                        break
        
        # 要素をまとめる
        return {
            'S': '; '.join(soap['S'][:3]) if soap['S'] else '特記事項なし',
            'O': '; '.join(soap['O'][:3]) if soap['O'] else '特記事項なし',
            'A': '; '.join(soap['A'][:2]) if soap['A'] else '要追加診断',
            'P': '; '.join(soap['P'][:3]) if soap['P'] else '要治療計画策定'
        }
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """セッションの全情報を取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # セッション基本情報
        cursor.execute("""
            SELECT cs.session_id, cs.patient_id, cs.doctor_id, cs.recording_start_time,
                   a.patient_name, a.doctor_name, a.treatment_type
            FROM counseling_sessions cs
            JOIN appointments a ON cs.appointment_id = a.appointment_id
            WHERE cs.session_id = ?
        """, (session_id,))
        
        session_info = cursor.fetchone()
        
        if not session_info:
            conn.close()
            return None
        
        # 会話記録
        cursor.execute("""
            SELECT speaker, speaker_name, original_text, timestamp_start
            FROM conversation_records 
            WHERE session_id = ?
            ORDER BY sequence_number
        """, (session_id,))
        
        conversation = cursor.fetchall()
        
        # SOAP記録
        cursor.execute("""
            SELECT soap_id, subjective_text, objective_text, assessment_text, plan_text,
                   reviewed_by_doctor, created_at
            FROM soap_records 
            WHERE session_id = ?
        """, (session_id,))
        
        soap_data = cursor.fetchone()
        
        conn.close()
        
        return {
            'session_info': {
                'session_id': session_info[0],
                'patient_id': session_info[1],
                'patient_name': session_info[4],
                'doctor_id': session_info[2],
                'doctor_name': session_info[5],
                'recording_time': session_info[3],
                'treatment_type': session_info[6]
            },
            'conversation': [
                {
                    'speaker': conv[0],
                    'speaker_name': conv[1],
                    'text': conv[2],
                    'timestamp': conv[3]
                } for conv in conversation
            ],
            'soap_record': {
                'soap_id': soap_data[0] if soap_data else None,
                'S': soap_data[1] if soap_data else None,
                'O': soap_data[2] if soap_data else None,
                'A': soap_data[3] if soap_data else None,
                'P': soap_data[4] if soap_data else None,
                'reviewed': soap_data[5] if soap_data else False,
                'created_at': soap_data[6] if soap_data else None
            } if soap_data else None
        }
    
    def search_sessions(self, patient_id: str = None, doctor_id: str = None, 
                       date_from: str = None, date_to: str = None) -> List[Dict]:
        """セッション検索"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT cs.session_id, cs.patient_id, cs.doctor_id, cs.recording_start_time,
                   a.patient_name, a.doctor_name, a.treatment_type
            FROM counseling_sessions cs
            JOIN appointments a ON cs.appointment_id = a.appointment_id
            WHERE 1=1
        """
        params = []
        
        if patient_id:
            query += " AND cs.patient_id = ?"
            params.append(patient_id)
        
        if doctor_id:
            query += " AND cs.doctor_id = ?"
            params.append(doctor_id)
        
        if date_from:
            query += " AND cs.recording_start_time >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND cs.recording_start_time <= ?"
            params.append(date_to)
        
        query += " ORDER BY cs.recording_start_time DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'session_id': row[0],
                'patient_id': row[1],
                'patient_name': row[4],
                'doctor_id': row[2],
                'doctor_name': row[5],
                'recording_time': row[3],
                'treatment_type': row[6]
            } for row in results
        ]
    
    def export_session_data(self, session_id: str, format: str = 'json') -> str:
        """セッションデータをエクスポート"""
        session_data = self.get_session_summary(session_id)
        
        if not session_data:
            return None
        
        if format == 'json':
            filename = f"output/session_{session_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        elif format == 'csv':
            filename = f"output/session_{session_id}.csv"
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # ヘッダー
                writer.writerow(['患者ID', '患者名', '医師ID', '医師名', '録音時刻', 
                               'S_主観', 'O_客観', 'A_評価', 'P_計画'])
                
                # データ
                info = session_data['session_info']
                soap = session_data['soap_record']
                writer.writerow([
                    info['patient_id'], info['patient_name'],
                    info['doctor_id'], info['doctor_name'],
                    info['recording_time'],
                    soap['S'] if soap else '',
                    soap['O'] if soap else '',
                    soap['A'] if soap else '',
                    soap['P'] if soap else ''
                ])
        
        print(f"✅ データエクスポート完了: {filename}")
        return filename

def parse_transcript_txt(file_path: str) -> List[Dict]:
    """TXT形式の文字起こしを解析"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.strip().split('\n\n')
    parsed = []
    
    for line in lines:
        if ':' in line:
            speaker, text = line.split(':', 1)
            parsed.append({
                'speaker': speaker.strip(),
                'text': text.strip(),
                'timestamp': None
            })
    
    return parsed

def main():
    """データベース中心のメイン処理"""
    print("🦷 歯科カウンセリングAIツール - データベース中心版")
    print("=" * 60)
    
    # データベース初期化
    db = DentalCounselingDatabase()
    
    # 1. 予約CSVをデータベースに読み込み
    print("\n📅 Step 1: 予約データをデータベースに保存")
    db.load_appointments_from_csv('sample_data/appointment_schedule.csv')
    
    # 2. 録音メタデータ
    recording_metadata = {
        'start_time': '2025-01-26 10:31:00',
        'doctor_id': 'D001',
        'device_id': 'plaud_001',
        'audio_file': 'sample_audio_20250126_1031.mp3'
    }
    
    # 3. セッション作成（予約データとの突合）
    print("\n🎯 Step 2: セッション作成・患者医師特定")
    session_id = db.create_counseling_session(recording_metadata)
    
    if not session_id:
        print("❌ セッション作成に失敗しました")
        return
    
    # 4. 文字起こしデータを全てデータベースに保存
    print("\n💬 Step 3: 全会話記録をデータベースに保存")
    transcript_data = parse_transcript_txt('sample_data/plaud_transcript.txt')
    db.save_conversation_records(session_id, transcript_data)
    
    # 5. データベースからSOAP形式に変換・保存
    print("\n📝 Step 4: SOAP形式変換・データベース保存")
    soap_result = db.generate_and_save_soap(session_id)
    
    # 6. セッション全体のサマリー表示
    print("\n📊 Step 5: セッションサマリー表示")
    session_summary = db.get_session_summary(session_id)
    
    if session_summary:
        print("\n" + "=" * 60)
        print("📋 セッションサマリー")
        print("=" * 60)
        
        info = session_summary['session_info']
        print(f"👤 患者: {info['patient_name']} (ID: {info['patient_id']})")
        print(f"👨‍⚕️ 医師: {info['doctor_name']} (ID: {info['doctor_id']})")
        print(f"📅 録音時刻: {info['recording_time']}")
        print(f"🏥 治療内容: {info['treatment_type']}")
        
        print(f"\n💬 会話記録: {len(session_summary['conversation'])}発言")
        
        if session_summary['soap_record']:
            soap = session_summary['soap_record']
            print(f"\n📝 SOAP記録 (ID: {soap['soap_id']}):")
            print(f"  S: {soap['S'][:100]}...")
            print(f"  O: {soap['O'][:100]}...")
            print(f"  A: {soap['A'][:100]}...")
            print(f"  P: {soap['P'][:100]}...")
    
    # 7. データエクスポート
    print("\n💾 Step 6: データエクスポート")
    os.makedirs('output', exist_ok=True)
    db.export_session_data(session_id, 'json')
    db.export_session_data(session_id, 'csv')
    
    # 8. 検索機能デモ
    print("\n🔍 Step 7: 検索機能デモ")
    search_results = db.search_sessions(doctor_id='D001')
    print(f"医師D001のセッション: {len(search_results)}件")
    
    for result in search_results:
        print(f"  - {result['session_id']}: {result['patient_name']} ({result['recording_time']})")
    
    print("\n✅ データベース中心処理完了!")
    print(f"📁 データベースファイル: {db.db_path}")
    print("📁 エクスポートファイル: output/")

if __name__ == "__main__":
    main()
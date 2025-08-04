#!/usr/bin/env python3
"""
歯科カウンセリング音声記録AIツール - プロトタイプ
PLAUD NOTEやNottaの出力からSOAP形式への変換デモ
"""

import csv
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

class DentalCounselingAI:
    def __init__(self):
        self.appointments = []
        self.soap_templates = {
            'dental_keywords': {
                'subjective': ['痛い', 'しみる', '違和感', '気になる', '腫れ', 'ズキズキ', 'キーン'],
                'objective': ['う蝕', '歯髄', '打診痛', '冷水痛', '歯肉', '歯石', '動揺'],
                'assessment': ['診断', '虫歯', '歯周病', '根尖病変', '咬合'],
                'plan': ['治療', '充填', '抜歯', '根管治療', '予約', 'CR', 'インレー']
            }
        }
    
    def load_appointments(self, csv_file: str) -> None:
        """予約システムのCSVファイルを読み込み"""
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.appointments = list(reader)
            print(f"✅ 予約データを読み込みました: {len(self.appointments)}件")
        except FileNotFoundError:
            print(f"❌ ファイルが見つかりません: {csv_file}")
    
    def identify_patient_doctor(self, recording_start: str, doctor_id: str) -> Optional[Dict]:
        """録音開始時刻と医師IDから患者を特定"""
        recording_time = datetime.strptime(recording_start, "%Y-%m-%d %H:%M:%S")
        
        for appointment in self.appointments:
            apt_time = datetime.strptime(appointment['予約日時'], "%Y-%m-%d %H:%M:%S")
            time_diff = abs((recording_time - apt_time).total_seconds() / 60)  # 分単位
            
            # 時間範囲±5分、担当医IDが一致
            if time_diff <= 5 and appointment['担当医ID'] == doctor_id:
                print(f"✅ 患者特定成功: {appointment['患者名']} (ID: {appointment['患者ID']})")
                return appointment
        
        print("❌ 該当する予約が見つかりませんでした")
        return None
    
    def parse_transcript_txt(self, file_path: str) -> List[Dict]:
        """TXT形式の文字起こしを解析"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 発言者と内容を分離
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
    
    def parse_transcript_srt(self, file_path: str) -> List[Dict]:
        """SRT形式の文字起こしを解析"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # SRTブロックを分離
        blocks = content.strip().split('\n\n')
        parsed = []
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                # タイムスタンプ行
                timestamp_line = lines[1]
                # テキスト行（複数行の場合もある）
                text_lines = lines[2:]
                text = ' '.join(text_lines)
                
                if ':' in text:
                    speaker, content = text.split(':', 1)
                    parsed.append({
                        'speaker': speaker.strip(),
                        'text': content.strip(),
                        'timestamp': timestamp_line
                    })
        
        return parsed
    
    def extract_soap_elements(self, transcript: List[Dict]) -> Dict:
        """文字起こしからSOAP要素を抽出"""
        soap = {
            'S': [],  # Subjective - 患者の主観的訴え
            'O': [],  # Objective - 医師の客観的所見
            'A': [],  # Assessment - 診断・評価
            'P': []   # Plan - 治療計画
        }
        
        keywords = self.soap_templates['dental_keywords']
        
        for entry in transcript:
            text = entry['text']
            speaker = entry['speaker']
            
            # S: 患者の主観的症状
            if speaker == '患者':
                for keyword in keywords['subjective']:
                    if keyword in text:
                        soap['S'].append(text)
                        break
            
            # O: 医師の客観的所見
            elif speaker == '医師':
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
        
        return soap
    
    def format_soap_note(self, soap_elements: Dict, patient_info: Dict) -> Dict:
        """SOAP要素を整理してフォーマット"""
        formatted_soap = {
            'patient_id': patient_info['患者ID'],
            'patient_name': patient_info['患者名'],
            'doctor_id': patient_info['担当医ID'],
            'doctor_name': patient_info['担当医名'],
            'date': patient_info['予約日時'].split()[0],
            'soap_note': {
                'S': self._summarize_subjective(soap_elements['S']),
                'O': self._summarize_objective(soap_elements['O']),
                'A': self._summarize_assessment(soap_elements['A']),
                'P': self._summarize_plan(soap_elements['P'])
            }
        }
        
        return formatted_soap
    
    def _summarize_subjective(self, subjective_list: List[str]) -> str:
        """主観的情報をまとめる"""
        if not subjective_list:
            return "特記事項なし"
        
        # 重複を除去し、主要な症状をまとめる
        symptoms = []
        for text in subjective_list:
            if '痛' in text or 'しみ' in text:
                symptoms.append(text)
        
        return '; '.join(symptoms[:3]) if symptoms else subjective_list[0]
    
    def _summarize_objective(self, objective_list: List[str]) -> str:
        """客観的所見をまとめる"""
        if not objective_list:
            return "特記事項なし"
        
        findings = []
        for text in objective_list:
            if 'う蝕' in text or '歯髄' in text or '痛' in text:
                findings.append(text)
        
        return '; '.join(findings[:3]) if findings else objective_list[0]
    
    def _summarize_assessment(self, assessment_list: List[str]) -> str:
        """診断・評価をまとめる"""
        if not assessment_list:
            return "要追加診断"
        
        return '; '.join(assessment_list[:2])
    
    def _summarize_plan(self, plan_list: List[str]) -> str:
        """治療計画をまとめる"""
        if not plan_list:
            return "要治療計画策定"
        
        return '; '.join(plan_list[:3])
    
    def process_recording(self, transcript_file: str, recording_metadata: Dict) -> Dict:
        """録音データの全体処理"""
        print(f"\n🎯 録音データ処理開始: {transcript_file}")
        
        # 1. 患者・医師特定
        patient_info = self.identify_patient_doctor(
            recording_metadata['start_time'],
            recording_metadata['doctor_id']
        )
        
        if not patient_info:
            return {'error': '患者特定に失敗しました'}
        
        # 2. 文字起こし解析
        if transcript_file.endswith('.txt'):
            transcript = self.parse_transcript_txt(transcript_file)
        elif transcript_file.endswith('.srt'):
            transcript = self.parse_transcript_srt(transcript_file)
        else:
            return {'error': 'サポートされていないファイル形式です'}
        
        print(f"✅ 文字起こし解析完了: {len(transcript)}発言")
        
        # 3. SOAP要素抽出
        soap_elements = self.extract_soap_elements(transcript)
        print(f"✅ SOAP要素抽出完了")
        
        # 4. SOAP形式フォーマット
        formatted_soap = self.format_soap_note(soap_elements, patient_info)
        print(f"✅ SOAP形式変換完了")
        
        return formatted_soap

def main():
    """メイン処理 - デモンストレーション"""
    print("🦷 歯科カウンセリングAIツール - プロトタイプ")
    print("=" * 50)
    
    # AIツール初期化
    ai_tool = DentalCounselingAI()
    
    # 予約データ読み込み
    ai_tool.load_appointments('sample_data/appointment_schedule.csv')
    
    # サンプル録音メタデータ（実際はPLAUD NOTEから取得）
    recording_metadata = {
        'start_time': '2025-01-26 10:31:00',  # 録音開始時刻
        'doctor_id': 'D001',                  # ログイン医師ID
        'device_id': 'plaud_001'              # デバイスID
    }
    
    # TXT形式のテスト
    print("\n📄 TXT形式テスト")
    result_txt = ai_tool.process_recording(
        'sample_data/plaud_transcript.txt',
        recording_metadata
    )
    
    if 'error' not in result_txt:
        print("\n📋 生成されたSOAPノート (TXT版):")
        print(json.dumps(result_txt, ensure_ascii=False, indent=2))
    
    # SRT形式のテスト
    print("\n" + "=" * 50)
    print("📄 SRT形式テスト")
    result_srt = ai_tool.process_recording(
        'sample_data/notta_transcript.srt',
        recording_metadata
    )
    
    if 'error' not in result_srt:
        print("\n📋 生成されたSOAPノート (SRT版):")
        print(json.dumps(result_srt, ensure_ascii=False, indent=2))
    
    # レセコン投入用データ生成
    if 'error' not in result_txt:
        print("\n" + "=" * 50)
        print("💾 レセコン投入用データ生成")
        
        # CSV形式でエクスポート
        csv_data = {
            '患者ID': result_txt['patient_id'],
            '患者名': result_txt['patient_name'],
            '診療日': result_txt['date'],
            '担当医': result_txt['doctor_name'],
            'S_主観的情報': result_txt['soap_note']['S'],
            'O_客観的所見': result_txt['soap_note']['O'],
            'A_評価診断': result_txt['soap_note']['A'],
            'P_治療計画': result_txt['soap_note']['P']
        }
        
        # CSVファイル出力
        with open('output/soap_for_rececon.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_data.keys())
            writer.writeheader()
            writer.writerow(csv_data)
        
        print("✅ レセコン投入用CSVファイルを生成しました: output/soap_for_rececon.csv")

if __name__ == "__main__":
    # 出力ディレクトリ作成
    os.makedirs('output', exist_ok=True)
    main()
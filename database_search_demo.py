#!/usr/bin/env python3
"""
データベース検索・分析機能のデモンストレーション
"""

import sqlite3
import json
from datetime import datetime, timedelta
from dental_ai_database import DentalCounselingDatabase

def search_demo():
    """検索機能のデモンストレーション"""
    print("🔍 データベース検索・分析デモ")
    print("=" * 50)
    
    # 既存のデータベースを使用
    db = DentalCounselingDatabase()
    
    # 既存データベースの場合はスキーマ初期化をスキップ
    print("✅ 既存データベースを使用")
    
    # 追加のサンプルデータを作成（デモ用）
    create_additional_sample_data(db)
    
    print("\n📊 検索機能テスト")
    
    # 1. 全セッション検索
    print("\n1️⃣ 全セッション検索:")
    all_sessions = db.search_sessions()
    for session in all_sessions:
        print(f"  - {session['session_id']}: {session['patient_name']} → {session['doctor_name']} ({session['recording_time']})")
    
    # 2. 患者別検索
    print("\n2️⃣ 患者別検索 (P12345):")
    patient_sessions = db.search_sessions(patient_id='P12345')
    for session in patient_sessions:
        print(f"  - {session['session_id']}: {session['treatment_type']} ({session['recording_time']})")
    
    # 3. 医師別検索
    print("\n3️⃣ 医師別検索 (D001):")
    doctor_sessions = db.search_sessions(doctor_id='D001')
    for session in doctor_sessions:
        print(f"  - {session['session_id']}: {session['patient_name']} - {session['treatment_type']}")
    
    # 4. 期間検索
    print("\n4️⃣ 期間検索 (2025-01-26):")
    date_sessions = db.search_sessions(date_from='2025-01-26 00:00:00', date_to='2025-01-26 23:59:59')
    for session in date_sessions:
        print(f"  - {session['session_id']}: {session['patient_name']} ({session['recording_time']})")
    
    # 5. 詳細分析
    print("\n📈 詳細分析機能")
    analyze_sessions(db)

def create_additional_sample_data(db):
    """追加のサンプルデータを作成"""
    print("📝 追加サンプルデータ作成中...")
    
    # 追加の録音メタデータ
    additional_recordings = [
        {
            'start_time': '2025-01-26 11:01:00',
            'doctor_id': 'D002',
            'device_id': 'plaud_002',
            'audio_file': 'sample_audio_20250126_1101.mp3'
        },
        {
            'start_time': '2025-01-26 14:02:00',
            'doctor_id': 'D001',
            'device_id': 'plaud_001',
            'audio_file': 'sample_audio_20250126_1402.mp3'
        }
    ]
    
    # サンプル会話データ
    sample_conversations = [
        [
            {'speaker': '医師', 'text': 'こんにちは。定期検診にいらっしゃいましたね。'},
            {'speaker': '患者', 'text': 'はい、よろしくお願いします。特に問題はないと思います。'},
            {'speaker': '医師', 'text': '歯石が少し付いていますね。クリーニングしましょう。'},
            {'speaker': '患者', 'text': 'お願いします。'},
            {'speaker': '医師', 'text': 'きれいになりました。次回は6ヶ月後にお越しください。'}
        ],
        [
            {'speaker': '医師', 'text': 'インプラント治療についてご相談ですね。'},
            {'speaker': '患者', 'text': 'はい、左下の奥歯を抜歯したので、インプラントを検討しています。'},
            {'speaker': '医師', 'text': '骨の状態を確認しましたが、インプラント可能です。'},
            {'speaker': '患者', 'text': '費用はどのくらいでしょうか？'},
            {'speaker': '医師', 'text': '1本あたり35万円程度です。治療期間は3-4ヶ月です。'}
        ]
    ]
    
    # セッション作成とデータ保存
    for i, (recording, conversation) in enumerate(zip(additional_recordings, sample_conversations)):
        session_id = db.create_counseling_session(recording)
        if session_id:
            db.save_conversation_records(session_id, conversation)
            db.generate_and_save_soap(session_id)
    
    print("✅ 追加サンプルデータ作成完了")

def analyze_sessions(db):
    """セッションデータの分析"""
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    # 1. 医師別セッション数
    print("\n📊 医師別セッション数:")
    cursor.execute("""
        SELECT a.doctor_name, COUNT(*) as session_count
        FROM counseling_sessions cs
        JOIN appointments a ON cs.appointment_id = a.appointment_id
        GROUP BY cs.doctor_id, a.doctor_name
        ORDER BY session_count DESC
    """)
    
    for doctor_name, count in cursor.fetchall():
        print(f"  - {doctor_name}: {count}セッション")
    
    # 2. 治療内容別分析
    print("\n🏥 治療内容別分析:")
    cursor.execute("""
        SELECT a.treatment_type, COUNT(*) as count
        FROM counseling_sessions cs
        JOIN appointments a ON cs.appointment_id = a.appointment_id
        GROUP BY a.treatment_type
        ORDER BY count DESC
    """)
    
    for treatment, count in cursor.fetchall():
        print(f"  - {treatment}: {count}件")
    
    # 3. 会話量分析
    print("\n💬 会話量分析:")
    cursor.execute("""
        SELECT cs.session_id, a.patient_name, a.doctor_name, COUNT(cr.record_id) as conversation_count
        FROM counseling_sessions cs
        JOIN appointments a ON cs.appointment_id = a.appointment_id
        LEFT JOIN conversation_records cr ON cs.session_id = cr.session_id
        GROUP BY cs.session_id, a.patient_name, a.doctor_name
        ORDER BY conversation_count DESC
    """)
    
    for session_id, patient, doctor, conv_count in cursor.fetchall():
        print(f"  - {patient} → {doctor}: {conv_count}発言 ({session_id})")
    
    # 4. SOAP生成状況
    print("\n📝 SOAP生成状況:")
    cursor.execute("""
        SELECT 
            COUNT(cs.session_id) as total_sessions,
            COUNT(sr.soap_id) as soap_generated,
            COUNT(CASE WHEN sr.reviewed_by_doctor = 1 THEN 1 END) as reviewed_count
        FROM counseling_sessions cs
        LEFT JOIN soap_records sr ON cs.session_id = sr.session_id
    """)
    
    total, generated, reviewed = cursor.fetchone()
    print(f"  - 総セッション数: {total}")
    print(f"  - SOAP生成済み: {generated}")
    print(f"  - 医師確認済み: {reviewed}")
    print(f"  - 生成率: {generated/total*100:.1f}%")
    
    conn.close()

def export_analysis_report(db):
    """分析レポートをエクスポート"""
    print("\n📄 分析レポート生成中...")
    
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    # 総合レポートデータ収集
    cursor.execute("""
        SELECT 
            cs.session_id,
            a.patient_name,
            a.doctor_name,
            a.treatment_type,
            cs.recording_start_time,
            COUNT(cr.record_id) as conversation_count,
            CASE WHEN sr.soap_id IS NOT NULL THEN 'Generated' ELSE 'Not Generated' END as soap_status,
            sr.reviewed_by_doctor
        FROM counseling_sessions cs
        JOIN appointments a ON cs.appointment_id = a.appointment_id
        LEFT JOIN conversation_records cr ON cs.session_id = cr.session_id
        LEFT JOIN soap_records sr ON cs.session_id = sr.session_id
        GROUP BY cs.session_id, a.patient_name, a.doctor_name, a.treatment_type, 
                 cs.recording_start_time, sr.soap_id, sr.reviewed_by_doctor
        ORDER BY cs.recording_start_time DESC
    """)
    
    report_data = []
    for row in cursor.fetchall():
        report_data.append({
            'session_id': row[0],
            'patient_name': row[1],
            'doctor_name': row[2],
            'treatment_type': row[3],
            'recording_time': row[4],
            'conversation_count': row[5],
            'soap_status': row[6],
            'reviewed': bool(row[7]) if row[7] is not None else False
        })
    
    conn.close()
    
    # JSONレポート出力
    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_sessions': len(report_data),
            'soap_generated': len([r for r in report_data if r['soap_status'] == 'Generated']),
            'reviewed_count': len([r for r in report_data if r['reviewed']])
        },
        'sessions': report_data
    }
    
    with open('output/analysis_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("✅ 分析レポート生成完了: output/analysis_report.json")

if __name__ == "__main__":
    search_demo()
    
    # 分析レポート生成
    db = DentalCounselingDatabase()
    export_analysis_report(db)
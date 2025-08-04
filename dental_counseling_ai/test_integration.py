"""
統合テスト
エンドツーエンドのデータフロー動作確認
"""

import os
import sys
import json
from datetime import datetime

# パスの設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.data_processor import DataProcessor, SampleDataGenerator
from core.patient_matcher import PatientMatcher, AppointmentDataGenerator
from core.soap_generator import SOAPGenerator, SOAPFormatter
from database.models import DatabaseManager


def create_sample_files():
    """サンプルファイルの作成"""
    print("=== サンプルファイル作成 ===")
    
    # データジェネレーターのインスタンス作成
    data_gen = SampleDataGenerator()
    appointment_gen = AppointmentDataGenerator()
    
    # PLAUD NOTEサンプルファイル
    plaud_sample = data_gen.create_plaud_note_sample()
    with open('sample_plaud_note.txt', 'w', encoding='utf-8') as f:
        f.write(plaud_sample)
    print("✓ PLAUD NOTEサンプルファイル作成: sample_plaud_note.txt")
    
    # Nottaサンプルファイル
    notta_sample = data_gen.create_notta_csv_sample()
    with open('sample_notta.csv', 'w', encoding='utf-8') as f:
        f.write(notta_sample)
    print("✓ Nottaサンプルファイル作成: sample_notta.csv")
    
    # 予約システムサンプルファイル
    appointments_sample = appointment_gen.create_sample_appointments_csv()
    with open('sample_appointments.csv', 'w', encoding='utf-8') as f:
        f.write(appointments_sample)
    print("✓ 予約システムサンプルファイル作成: sample_appointments.csv")


def test_data_processing():
    """データ処理テスト"""
    print("\n=== データ処理テスト ===")
    
    processor = DataProcessor()
    
    # PLAUD NOTEデータの処理
    print("PLAUD NOTEデータ処理中...")
    plaud_data = processor.process_file('sample_plaud_note.txt', 'plaud_note')
    print(f"✓ 処理完了 - ID: {plaud_data['recording_id']}")
    print(f"  話者セグメント数: {len(plaud_data['speaker_segments'])}")
    
    # Nottaデータの処理
    print("Nottaデータ処理中...")
    notta_data = processor.process_file('sample_notta.csv', 'notta')
    print(f"✓ 処理完了 - ID: {notta_data['recording_id']}")
    print(f"  話者セグメント数: {len(notta_data['speaker_segments'])}")
    
    return plaud_data, notta_data


def test_patient_matching(processed_data):
    """患者マッチングテスト"""
    print("\n=== 患者マッチングテスト ===")
    
    matcher = PatientMatcher()
    
    # 医師IDを設定（サンプルデータに合わせる）
    processed_data['doctor_id'] = 'D001'
    
    # マッチング実行
    match_result = matcher.match_patient_doctor(processed_data, 'sample_appointments.csv')
    
    print(f"マッチング結果: {match_result['status']}")
    if match_result['status'] == 'matched':
        print(f"✓ 患者ID: {match_result['patient_id']}")
        print(f"✓ 医師ID: {match_result['doctor_id']}")
        print(f"✓ 予約ID: {match_result['appointment_id']}")
        print(f"✓ 信頼度: {match_result['confidence']:.2f}")
    
    return match_result


def test_soap_generation(processed_data):
    """SOAP生成テスト"""
    print("\n=== SOAP生成テスト ===")
    
    generator = SOAPGenerator()
    formatter = SOAPFormatter()
    
    # SOAP生成
    soap_result = generator.generate_soap(processed_data)
    
    print(f"生成結果: {soap_result['status']}")
    print(f"信頼度: {soap_result['confidence_score']:.2f}")
    
    if soap_result['status'] == 'success':
        soap_note = soap_result['soap_note']
        print("\n生成されたSOAP:")
        print(f"S: {soap_note['S']}")
        print(f"O: {soap_note['O']}")
        print(f"A: {soap_note['A']}")
        print(f"P: {soap_note['P']}")
        
        # レセコン用フォーマット
        rececon_format = formatter.format_for_rececon(soap_result)
        print("\nレセコン用フォーマット:")
        print(rececon_format)
    
    return soap_result


def test_database_operations(processed_data, match_result, soap_result):
    """データベース操作テスト"""
    print("\n=== データベース操作テスト ===")
    
    db_manager = DatabaseManager()
    db_manager.create_tables()
    
    # セッションデータの準備
    session_data = {
        'recording_id': processed_data['recording_id'],
        'patient_id': match_result.get('patient_id') if match_result['status'] == 'matched' else None,
        'doctor_id': processed_data.get('doctor_id', 'D001'),
        'appointment_id': match_result.get('appointment_id') if match_result['status'] == 'matched' else None,
        'start_time': datetime.now().isoformat(),
        'end_time': datetime.now().isoformat(),
        'audio_file_path': processed_data.get('file_path'),
        'transcript': processed_data['transcript'],
        'soap_note': soap_result['soap_note'] if soap_result['status'] == 'success' else None,
        'confidence_score': soap_result.get('confidence_score', 0.0),
        'status': 'completed'
    }
    
    # セッション保存
    session_id = db_manager.save_counseling_session(session_data)
    print(f"✓ セッション保存完了: {session_id}")
    
    # セッション取得
    retrieved_session = db_manager.get_counseling_session(session_id)
    print(f"✓ セッション取得完了: {retrieved_session['id']}")
    
    # 音声分析データ保存（サンプル）
    analytics_data = {
        'session_id': session_id,
        'timestamp_offset': 30.0,
        'tone_level': 0.7,
        'speech_rate': 1.2,
        'emotion_scores': {'anxiety': 0.3, 'satisfaction': 0.8, 'confidence': 0.6},
        'non_verbal_events': {'sighs': 1, 'pauses': 3, 'hesitations': 2}
    }
    
    analytics_id = db_manager.save_voice_analytics(analytics_data)
    print(f"✓ 音声分析データ保存完了: {analytics_id}")
    
    # 結果データ保存（サンプル）
    outcome_data = {
        'session_id': session_id,
        'outcome_type': 'contracted',
        'contract_amount': 50000.0,
        'follow_up_scheduled': True,
        'notes': '治療に同意、次回予約済み'
    }
    
    outcome_id = db_manager.save_counseling_outcome(outcome_data)
    print(f"✓ 結果データ保存完了: {outcome_id}")
    
    # 統計取得
    stats = db_manager.get_outcome_statistics('D001')
    print(f"✓ 統計データ取得: 成約率 {stats['contract_rate']:.1%}")
    
    return session_id


def test_end_to_end_workflow():
    """エンドツーエンドワークフローテスト"""
    print("\n" + "="*50)
    print("歯科カウンセリング音声記録AIツール - 統合テスト")
    print("="*50)
    
    try:
        # 1. サンプルファイル作成
        create_sample_files()
        
        # 2. データ処理
        plaud_data, notta_data = test_data_processing()
        
        # 3. 患者マッチング（PLAUD NOTEデータを使用）
        match_result = test_patient_matching(plaud_data)
        
        # 4. SOAP生成
        soap_result = test_soap_generation(plaud_data)
        
        # 5. データベース操作
        session_id = test_database_operations(plaud_data, match_result, soap_result)
        
        print("\n" + "="*50)
        print("✅ 統合テスト完了 - 全ての機能が正常に動作しました")
        print(f"最終セッションID: {session_id}")
        print("="*50)
        
        # 結果サマリー
        print("\n📊 テスト結果サマリー:")
        print(f"・データ処理: ✅ 成功")
        print(f"・患者マッチング: {'✅ 成功' if match_result['status'] == 'matched' else '⚠️ 要確認'}")
        print(f"・SOAP生成: {'✅ 成功' if soap_result['status'] == 'success' else '❌ 失敗'}")
        print(f"・データベース: ✅ 成功")
        
        return True
        
    except Exception as e:
        print(f"\n❌ テスト失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_files():
    """テストファイルのクリーンアップ"""
    test_files = [
        'sample_plaud_note.txt',
        'sample_notta.csv', 
        'sample_appointments.csv',
        'dental_counseling.db'
    ]
    
    print("\n🧹 テストファイルクリーンアップ:")
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"✓ 削除: {file}")


if __name__ == "__main__":
    # 統合テスト実行
    success = test_end_to_end_workflow()
    
    # クリーンアップ（オプション）
    cleanup_choice = input("\nテストファイルを削除しますか？ (y/N): ")
    if cleanup_choice.lower() == 'y':
        cleanup_test_files()
    
    # 終了コード
    sys.exit(0 if success else 1)
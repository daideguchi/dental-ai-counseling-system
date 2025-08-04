#!/usr/bin/env python3
"""
歯科カウンセリングAIツール - 統合デモンストレーション
PLAUD NOTE/Notta → SOAP変換 → 感情分析 → レセコン投入の全工程
"""

import json
import os
from dental_ai_prototype import DentalCounselingAI
from voice_emotion_analyzer import VoiceEmotionAnalyzer

def integrated_demo():
    """統合デモンストレーション"""
    print("🦷 歯科カウンセリングAIツール - 統合デモ")
    print("=" * 60)
    print("📋 処理フロー:")
    print("1. 予約データ読み込み")
    print("2. 音声文字起こし解析")
    print("3. 患者・医師特定")
    print("4. SOAP形式変換")
    print("5. 音声感情分析")
    print("6. レセコン投入データ生成")
    print("7. 成約率予測・改善提案")
    print("=" * 60)
    
    # ツール初期化
    ai_tool = DentalCounselingAI()
    emotion_analyzer = VoiceEmotionAnalyzer()
    
    # 1. 予約データ読み込み
    print("\n📅 Step 1: 予約データ読み込み")
    ai_tool.load_appointments('sample_data/appointment_schedule.csv')
    
    # 2. 録音メタデータ（実際はPLAUD NOTEから取得）
    recording_metadata = {
        'start_time': '2025-01-26 10:31:00',
        'doctor_id': 'D001',
        'device_id': 'plaud_001',
        'audio_file': 'sample_audio_20250126_1031.mp3'
    }
    
    print(f"🎙️  録音開始: {recording_metadata['start_time']}")
    print(f"👨‍⚕️  担当医: {recording_metadata['doctor_id']}")
    
    # 3. SOAP変換処理
    print("\n📝 Step 2-4: 文字起こし → SOAP変換")
    soap_result = ai_tool.process_recording(
        'sample_data/plaud_transcript.txt',
        recording_metadata
    )
    
    if 'error' in soap_result:
        print(f"❌ エラー: {soap_result['error']}")
        return
    
    # 4. 音声感情分析
    print("\n🎵 Step 5: 音声感情分析")
    transcript_data = ai_tool.parse_transcript_txt('sample_data/plaud_transcript.txt')
    emotion_result = emotion_analyzer.analyze_voice_emotion(
        recording_metadata['audio_file'],
        transcript_data
    )
    
    # 5. 統合結果生成
    print("\n📊 Step 6-7: 統合分析結果生成")
    integrated_result = {
        'session_info': {
            'patient_id': soap_result['patient_id'],
            'patient_name': soap_result['patient_name'],
            'doctor_id': soap_result['doctor_id'],
            'doctor_name': soap_result['doctor_name'],
            'date': soap_result['date'],
            'recording_metadata': recording_metadata
        },
        'clinical_record': soap_result['soap_note'],
        'emotion_analysis': emotion_result['overall_analysis'],
        'success_prediction': emotion_result['counseling_success_prediction'],
        'recommendations': generate_integrated_recommendations(
            soap_result, emotion_result
        )
    }
    
    # 結果表示
    display_integrated_results(integrated_result)
    
    # 6. 各種出力ファイル生成
    print("\n💾 Step 8: 出力ファイル生成")
    generate_output_files(integrated_result, soap_result, emotion_result)
    
    print("\n✅ 統合デモ完了!")
    print("📁 生成されたファイル:")
    print("  - output/soap_for_rececon.csv (レセコン投入用)")
    print("  - output/emotion_analysis.json (感情分析結果)")
    print("  - output/integrated_report.json (統合レポート)")

def generate_integrated_recommendations(soap_result, emotion_result):
    """統合分析に基づく推奨アクションを生成"""
    recommendations = []
    
    # SOAP内容に基づく推奨
    soap_note = soap_result['soap_note']
    if '深い' in soap_note['O'] and '虫歯' in soap_note['A']:
        recommendations.append({
            'type': 'clinical',
            'priority': 'high',
            'message': '深在性う蝕のため、神経保護処置を検討してください'
        })
    
    # 感情分析に基づく推奨
    success_prob = emotion_result['counseling_success_prediction']['success_probability']
    if success_prob < 0.6:
        recommendations.append({
            'type': 'communication',
            'priority': 'medium',
            'message': '患者の不安軽減のため、治療手順をより詳しく説明することを推奨'
        })
    
    # 患者の感情状態に基づく推奨
    patient_emotions = emotion_result['overall_analysis']['patient_emotional_state']
    if patient_emotions.get('anxiety', 0) > 0.5:
        recommendations.append({
            'type': 'patient_care',
            'priority': 'medium',
            'message': '患者の不安レベルが高いため、リラックスできる環境作りを心がけてください'
        })
    
    return recommendations

def display_integrated_results(result):
    """統合結果を見やすく表示"""
    print("\n" + "=" * 60)
    print("📋 統合分析結果")
    print("=" * 60)
    
    # セッション情報
    session = result['session_info']
    print(f"👤 患者: {session['patient_name']} (ID: {session['patient_id']})")
    print(f"👨‍⚕️ 担当医: {session['doctor_name']} (ID: {session['doctor_id']})")
    print(f"📅 診療日: {session['date']}")
    
    # SOAP要約
    print(f"\n📝 SOAP要約:")
    soap = result['clinical_record']
    print(f"  S: {soap['S'][:100]}...")
    print(f"  O: {soap['O'][:100]}...")
    print(f"  A: {soap['A'][:100]}...")
    print(f"  P: {soap['P'][:100]}...")
    
    # 感情分析サマリー
    print(f"\n🎵 感情分析サマリー:")
    emotion = result['emotion_analysis']
    patient_emotions = emotion['patient_emotional_state']
    print(f"  患者の主要感情:")
    print(f"    - 不安度: {patient_emotions.get('anxiety', 0):.1%}")
    print(f"    - 信頼度: {patient_emotions.get('trust', 0):.1%}")
    print(f"    - ストレス: {patient_emotions.get('stress', 0):.1%}")
    
    # 成功予測
    print(f"\n🎯 カウンセリング成功予測:")
    prediction = result['success_prediction']
    print(f"  成功確率: {prediction['success_probability']:.1%}")
    print(f"  信頼度: {prediction['confidence_level']}")
    print(f"  推奨: {prediction['recommendation']}")
    
    # 統合推奨事項
    print(f"\n💡 統合推奨事項:")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"  {i}. [{rec['priority'].upper()}] {rec['message']}")

def generate_output_files(integrated_result, soap_result, emotion_result):
    """各種出力ファイルを生成"""
    os.makedirs('output', exist_ok=True)
    
    # 1. 統合レポート
    with open('output/integrated_report.json', 'w', encoding='utf-8') as f:
        json.dump(integrated_result, f, ensure_ascii=False, indent=2)
    
    # 2. 感情分析詳細
    with open('output/emotion_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(emotion_result, f, ensure_ascii=False, indent=2)
    
    # 3. レセコン投入用CSV（既に dental_ai_prototype.py で生成済み）
    
    print("✅ 出力ファイル生成完了")

if __name__ == "__main__":
    integrated_demo()
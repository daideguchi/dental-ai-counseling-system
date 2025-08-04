#!/usr/bin/env python3
"""
実際の出力形式に対応した統合歯科カウンセリングAIシステム
PLAUD NOTE/Nottaの正確な出力形式に基づいた実装
"""

import sqlite3
import json
import os
from datetime import datetime
from realistic_output_parser import RealisticOutputParser
from dental_ai_database import DentalCounselingDatabase

class RealisticIntegratedSystem:
    """実際の出力形式に対応した統合システム"""
    
    def __init__(self, db_path: str = "realistic_dental_counseling.db"):
        self.db = DentalCounselingDatabase(db_path)
        self.parser = RealisticOutputParser()
        self.supported_inputs = {
            'plaud_note': {
                'transcript': ['txt'],
                'summary': ['md', 'markdown'],
                'audio': ['mp3', 'wav']
            },
            'notta': {
                'transcript': ['csv', 'xlsx', 'txt', 'srt'],
                'audio': ['mp3', 'wav']
            }
        }
    
    def process_plaud_note_session(self, session_config: dict) -> dict:
        """
        PLAUD NOTEセッションの完全処理
        
        Args:
            session_config: {
                'recording_metadata': {...},
                'transcript_file': 'path/to/transcript.txt',
                'summary_file': 'path/to/summary.md' (optional),
                'audio_file': 'path/to/audio.mp3' (optional)
            }
        """
        print(f"\n🎯 PLAUD NOTEセッション処理開始")
        
        # 1. セッション作成
        session_id = self.db.create_counseling_session(session_config['recording_metadata'])
        if not session_id:
            return {'error': 'セッション作成に失敗しました'}
        
        # 2. 文字起こしデータの解析・保存
        transcript_file = session_config['transcript_file']
        if transcript_file.endswith('.txt'):
            parsed_transcript = self.parser.parse_plaud_note_txt(transcript_file)
        else:
            return {'error': f'サポートされていない文字起こし形式: {transcript_file}'}
        
        # 統一フォーマットに変換
        unified_data = self.parser.convert_to_unified_format(parsed_transcript)
        
        # データベースに保存
        self._save_unified_conversation(session_id, unified_data)
        
        # 3. 要約データの処理（オプション）
        summary_data = None
        if 'summary_file' in session_config and session_config['summary_file']:
            summary_file = session_config['summary_file']
            if summary_file.endswith(('.md', '.markdown')):
                parsed_summary = self.parser.parse_plaud_note_markdown(summary_file)
                summary_data = parsed_summary['structured_data']
                self._save_summary_data(session_id, summary_data)
        
        # 4. SOAP形式生成・保存
        soap_result = self.db.generate_and_save_soap(session_id)
        
        # 5. 結果をまとめて返す
        return {
            'session_id': session_id,
            'source_system': 'plaud_note',
            'processed_segments': len(unified_data['conversation']),
            'has_summary': summary_data is not None,
            'soap_generated': soap_result is not None,
            'metadata': unified_data['metadata']
        }
    
    def process_notta_session(self, session_config: dict) -> dict:
        """
        Nottaセッションの完全処理
        
        Args:
            session_config: {
                'recording_metadata': {...},
                'transcript_file': 'path/to/transcript.csv',
                'audio_file': 'path/to/audio.mp3' (optional)
            }
        """
        print(f"\n🎯 Nottaセッション処理開始")
        
        # 1. セッション作成
        session_id = self.db.create_counseling_session(session_config['recording_metadata'])
        if not session_id:
            return {'error': 'セッション作成に失敗しました'}
        
        # 2. 文字起こしデータの解析・保存
        transcript_file = session_config['transcript_file']
        
        if transcript_file.endswith('.csv'):
            parsed_transcript = self.parser.parse_notta_csv(transcript_file)
        elif transcript_file.endswith('.xlsx'):
            parsed_transcript = self.parser.parse_notta_xlsx_simulation(transcript_file)
        else:
            return {'error': f'サポートされていない文字起こし形式: {transcript_file}'}
        
        # 統一フォーマットに変換
        unified_data = self.parser.convert_to_unified_format(parsed_transcript)
        
        # データベースに保存
        self._save_unified_conversation(session_id, unified_data)
        
        # 3. SOAP形式生成・保存
        soap_result = self.db.generate_and_save_soap(session_id)
        
        # 4. 結果をまとめて返す
        return {
            'session_id': session_id,
            'source_system': 'notta',
            'processed_segments': len(unified_data['conversation']),
            'has_timestamps': unified_data['metadata']['has_timestamps'],
            'has_confidence_scores': 'confidence_score' in unified_data['conversation'][0],
            'soap_generated': soap_result is not None,
            'metadata': unified_data['metadata']
        }
    
    def _save_unified_conversation(self, session_id: str, unified_data: dict) -> bool:
        """統一フォーマットの会話データをデータベースに保存"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        try:
            for segment in unified_data['conversation']:
                cursor.execute("""
                    INSERT INTO conversation_records 
                    (session_id, sequence_number, speaker, speaker_name, 
                     timestamp_start, timestamp_end, original_text, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    segment['sequence'],
                    segment['speaker'],
                    segment['speaker_label'],
                    segment['timestamp_start'],
                    segment['timestamp_end'],
                    segment['text'],
                    segment['confidence_score']
                ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ 統一フォーマット会話記録をデータベースに保存: {len(unified_data['conversation'])}発言")
            return True
            
        except Exception as e:
            print(f"❌ 会話記録保存エラー: {e}")
            conn.close()
            return False
    
    def _save_summary_data(self, session_id: str, summary_data: dict) -> bool:
        """要約データをデータベースに保存"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        try:
            # 要約データを追加のテーブルに保存（簡易実装）
            cursor.execute("""
                INSERT OR REPLACE INTO soap_records 
                (soap_id, session_id, subjective_text, objective_text, 
                 assessment_text, plan_text, generation_method, reviewed_by_doctor)
                VALUES (?, ?, ?, ?, ?, ?, 'plaud_summary', FALSE)
            """, (
                f"SUMMARY_{session_id}",
                session_id,
                summary_data.get('chief_complaint', ''),
                summary_data.get('findings', ''),
                summary_data.get('diagnosis', ''),
                summary_data.get('treatment_plan', '')
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ 要約データをデータベースに保存")
            return True
            
        except Exception as e:
            print(f"❌ 要約データ保存エラー: {e}")
            conn.close()
            return False
    
    def compare_processing_results(self, plaud_result: dict, notta_result: dict) -> dict:
        """PLAUD NOTEとNottaの処理結果を比較分析"""
        comparison = {
            'processing_comparison': {
                'plaud_note': {
                    'segments': plaud_result.get('processed_segments', 0),
                    'has_summary': plaud_result.get('has_summary', False),
                    'source_advantages': [
                        '要約データ自動生成',
                        'マインドマップ対応',
                        'シンプルな出力形式'
                    ],
                    'limitations': [
                        '話者区別なし（推定ベース）',
                        'タイムスタンプなし',
                        '信頼度情報なし'
                    ]
                },
                'notta': {
                    'segments': notta_result.get('processed_segments', 0),
                    'has_timestamps': notta_result.get('has_timestamps', False),
                    'has_confidence': notta_result.get('has_confidence_scores', False),
                    'source_advantages': [
                        '明確な話者区別',
                        '詳細なタイムスタンプ',
                        '信頼度スコア',
                        '多様な出力形式'
                    ],
                    'limitations': [
                        '要約機能は別途必要',
                        'ファイルサイズが大きい'
                    ]
                }
            },
            'recommendation': self._generate_usage_recommendation(plaud_result, notta_result)
        }
        
        return comparison
    
    def _generate_usage_recommendation(self, plaud_result: dict, notta_result: dict) -> dict:
        """使用場面別の推奨事項を生成"""
        return {
            'plaud_note_recommended_for': [
                '簡単な記録・要約が必要な場合',
                '医師が一人で使用する場合',
                'ストレージ容量を節約したい場合',
                '即座に要約が欲しい場合'
            ],
            'notta_recommended_for': [
                '詳細な分析が必要な場合',
                '複数話者の正確な区別が重要な場合',
                'タイムスタンプベースの検索が必要な場合',
                '高精度な文字起こしが必要な場合'
            ],
            'hybrid_approach': [
                'PLAUD NOTEで録音・要約生成',
                'Nottaで詳細分析・検証',
                '両方のデータを統合してデータベースに保存'
            ]
        }
    
    def export_comprehensive_report(self, session_ids: list) -> str:
        """複数セッションの包括的レポートを生成"""
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'sessions_analyzed': len(session_ids),
            'sessions': []
        }
        
        for session_id in session_ids:
            session_summary = self.db.get_session_summary(session_id)
            if session_summary:
                report_data['sessions'].append(session_summary)
        
        # レポートファイル出力
        os.makedirs('output/comprehensive_reports', exist_ok=True)
        report_file = f'output/comprehensive_reports/comprehensive_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 包括的レポート生成完了: {report_file}")
        return report_file

def demo_realistic_integrated_system():
    """実際の出力形式対応統合システムのデモ"""
    print("🏥 実際の出力形式対応 - 歯科カウンセリングAI統合システム")
    print("=" * 70)
    
    system = RealisticIntegratedSystem()
    
    # PLAUD NOTEセッション処理
    plaud_config = {
        'recording_metadata': {
            'start_time': '2025-01-26 10:31:00',
            'doctor_id': 'D001',
            'device_id': 'plaud_001',
            'audio_file': 'realistic_sample_data/plaud_audio.mp3'
        },
        'transcript_file': 'realistic_sample_data/plaud_note_transcript.txt',
        'summary_file': 'realistic_sample_data/plaud_note_summary.md'
    }
    
    print("\n📱 PLAUD NOTEセッション処理:")
    plaud_result = system.process_plaud_note_session(plaud_config)
    
    if 'error' not in plaud_result:
        print(f"  ✅ セッションID: {plaud_result['session_id']}")
        print(f"  📊 処理セグメント数: {plaud_result['processed_segments']}")
        print(f"  📝 要約データ: {'あり' if plaud_result['has_summary'] else 'なし'}")
        print(f"  🏥 SOAP生成: {'成功' if plaud_result['soap_generated'] else '失敗'}")
    
    # Nottaセッション処理
    notta_config = {
        'recording_metadata': {
            'start_time': '2025-01-26 11:01:00',
            'doctor_id': 'D002',
            'device_id': 'notta_app',
            'audio_file': 'realistic_sample_data/notta_audio.mp3'
        },
        'transcript_file': 'realistic_sample_data/notta_transcript.csv'
    }
    
    print("\n📊 Nottaセッション処理:")
    notta_result = system.process_notta_session(notta_config)
    
    if 'error' not in notta_result:
        print(f"  ✅ セッションID: {notta_result['session_id']}")
        print(f"  📊 処理セグメント数: {notta_result['processed_segments']}")
        print(f"  ⏰ タイムスタンプ: {'あり' if notta_result['has_timestamps'] else 'なし'}")
        print(f"  🎯 信頼度スコア: {'あり' if notta_result['has_confidence_scores'] else 'なし'}")
        print(f"  🏥 SOAP生成: {'成功' if notta_result['soap_generated'] else '失敗'}")
    
    # 比較分析
    if 'error' not in plaud_result and 'error' not in notta_result:
        print("\n📈 処理結果比較分析:")
        comparison = system.compare_processing_results(plaud_result, notta_result)
        
        print("  PLAUD NOTE:")
        for advantage in comparison['processing_comparison']['plaud_note']['source_advantages']:
            print(f"    ✅ {advantage}")
        
        print("  Notta:")
        for advantage in comparison['processing_comparison']['notta']['source_advantages']:
            print(f"    ✅ {advantage}")
        
        print("\n💡 推奨使用場面:")
        rec = comparison['recommendation']
        print("  PLAUD NOTE推奨:")
        for item in rec['plaud_note_recommended_for'][:2]:
            print(f"    • {item}")
        
        print("  Notta推奨:")
        for item in rec['notta_recommended_for'][:2]:
            print(f"    • {item}")
        
        # 包括的レポート生成
        session_ids = [plaud_result['session_id'], notta_result['session_id']]
        report_file = system.export_comprehensive_report(session_ids)
        
        print(f"\n📄 包括的レポート: {report_file}")
    
    print("\n✅ 実際の出力形式対応システムデモ完了!")

if __name__ == "__main__":
    demo_realistic_integrated_system()
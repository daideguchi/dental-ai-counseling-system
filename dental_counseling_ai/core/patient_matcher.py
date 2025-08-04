"""
患者・医師特定ロジック
録音データと予約システムデータを照合して患者を特定
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json


class PatientMatcher:
    """患者・医師の特定を行うクラス"""
    
    def __init__(self):
        self.time_tolerance_minutes = 5  # 時間照合の許容範囲（分）
    
    def match_patient_doctor(self, recording_data: Dict, appointments_csv_path: str) -> Dict:
        """
        録音データと予約データを照合して患者・医師を特定
        
        Args:
            recording_data: 録音データ（統一形式）
            appointments_csv_path: 予約システムCSVファイルのパス
            
        Returns:
            マッチング結果
        """
        try:
            # 予約データの読み込み
            appointments_df = pd.read_csv(appointments_csv_path)
            
            # 録音データから必要な情報を抽出
            recording_time = self._parse_recording_time(recording_data)
            doctor_id = recording_data.get('doctor_id', 'unknown')
            
            # 候補の絞り込み
            candidates = self._filter_appointments(
                appointments_df, 
                recording_time, 
                doctor_id
            )
            
            # 最適なマッチを選択
            best_match = self._select_best_match(candidates, recording_time)
            
            if best_match is not None:
                return {
                    'status': 'matched',
                    'patient_id': best_match['patient_id'],
                    'doctor_id': best_match['doctor_id'],
                    'appointment_id': best_match['appointment_id'],
                    'appointment_time': best_match['appointment_time'],
                    'confidence': best_match['confidence'],
                    'recording_id': recording_data['recording_id']
                }
            else:
                return {
                    'status': 'no_match',
                    'recording_id': recording_data['recording_id'],
                    'candidates_count': len(candidates),
                    'requires_manual_review': True
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error_message': str(e),
                'recording_id': recording_data['recording_id'],
                'requires_manual_review': True
            }
    
    def _parse_recording_time(self, recording_data: Dict) -> datetime:
        """録音データから開始時刻を抽出"""
        # recording_idから時刻を抽出（例: rec_20250126_1030）
        recording_id = recording_data['recording_id']
        
        if 'rec_' in recording_id:
            try:
                time_part = recording_id.split('_')[1] + '_' + recording_id.split('_')[2]
                return datetime.strptime(time_part, '%Y%m%d_%H%M')
            except:
                pass
        
        # processed_atから推定
        if 'processed_at' in recording_data:
            return datetime.fromisoformat(recording_data['processed_at'].replace('Z', '+00:00'))
        
        # デフォルトは現在時刻
        return datetime.now()
    
    def _filter_appointments(self, appointments_df: pd.DataFrame, 
                           recording_time: datetime, doctor_id: str) -> pd.DataFrame:
        """予約データから候補を絞り込み"""
        
        # 時間範囲での絞り込み
        time_start = recording_time - timedelta(minutes=self.time_tolerance_minutes)
        time_end = recording_time + timedelta(minutes=self.time_tolerance_minutes)
        
        # 予約時刻の形式を統一（複数の形式に対応）
        appointments_df['appointment_datetime'] = pd.to_datetime(
            appointments_df['appointment_date'] + ' ' + appointments_df['appointment_time'],
            errors='coerce'
        )
        
        # 時間範囲でフィルタ
        time_filtered = appointments_df[
            (appointments_df['appointment_datetime'] >= time_start) &
            (appointments_df['appointment_datetime'] <= time_end)
        ]
        
        # 医師IDでフィルタ（unknown以外の場合）
        if doctor_id != 'unknown':
            doctor_filtered = time_filtered[
                time_filtered['doctor_id'] == doctor_id
            ]
            if not doctor_filtered.empty:
                return doctor_filtered
        
        return time_filtered
    
    def _select_best_match(self, candidates: pd.DataFrame, 
                          recording_time: datetime) -> Optional[Dict]:
        """候補から最適なマッチを選択"""
        
        if candidates.empty:
            return None
        
        if len(candidates) == 1:
            # 候補が1つの場合
            match = candidates.iloc[0]
            time_diff = abs((match['appointment_datetime'] - recording_time).total_seconds() / 60)
            
            return {
                'patient_id': match['patient_id'],
                'doctor_id': match['doctor_id'],
                'appointment_id': match['appointment_id'],
                'appointment_time': match['appointment_datetime'].isoformat(),
                'confidence': max(0.5, 1.0 - (time_diff / self.time_tolerance_minutes) * 0.5)
            }
        
        # 複数候補がある場合、最も時間が近いものを選択
        candidates['time_diff_minutes'] = candidates['appointment_datetime'].apply(
            lambda x: abs((x - recording_time).total_seconds() / 60)
        )
        
        best_candidate = candidates.loc[candidates['time_diff_minutes'].idxmin()]
        time_diff = best_candidate['time_diff_minutes']
        
        return {
            'patient_id': best_candidate['patient_id'],
            'doctor_id': best_candidate['doctor_id'],
            'appointment_id': best_candidate['appointment_id'],
            'appointment_time': best_candidate['appointment_datetime'].isoformat(),
            'confidence': max(0.3, 1.0 - (time_diff / self.time_tolerance_minutes) * 0.7)
        }


class AppointmentDataGenerator:
    """予約システムのサンプルデータ生成クラス"""
    
    @staticmethod
    def create_sample_appointments_csv() -> str:
        """サンプル予約データCSVを生成"""
        
        sample_data = """appointment_id,patient_id,doctor_id,patient_name,appointment_date,appointment_time,treatment_type,status
APT-001,P12345,D001,田中太郎,2025-01-26,10:30,カウンセリング,scheduled
APT-002,P12346,D002,佐藤花子,2025-01-26,11:00,定期検診,scheduled
APT-003,P12347,D001,鈴木次郎,2025-01-26,11:30,治療,scheduled
APT-004,P12348,D003,山田美咲,2025-01-26,14:00,カウンセリング,scheduled
APT-005,P12349,D001,高橋健一,2025-01-26,14:30,治療,scheduled
APT-006,P12350,D002,渡辺由美,2025-01-26,15:00,定期検診,scheduled
APT-007,P12351,D001,中村大輔,2025-01-26,15:30,カウンセリング,scheduled"""
        
        return sample_data
    
    @staticmethod
    def create_sample_recording_data() -> Dict:
        """サンプル録音データを生成"""
        
        return {
            'recording_id': 'rec_20250126_1030',
            'source': 'plaud_note',
            'doctor_id': 'D001',
            'processed_at': '2025-01-26T10:35:00',
            'transcript': '患者: おはようございます。右上の奥歯が痛くて来ました...',
            'speaker_segments': [
                {'speaker': 'patient', 'text': 'おはようございます。右上の奥歯が痛くて来ました。'},
                {'speaker': 'doctor', 'text': 'おはようございます。いつ頃からの痛みでしょうか？'}
            ]
        }


def test_patient_matching():
    """患者マッチング機能のテスト"""
    
    # サンプルデータの作成
    generator = AppointmentDataGenerator()
    
    # 予約データCSVファイルの作成
    with open('sample_appointments.csv', 'w', encoding='utf-8') as f:
        f.write(generator.create_sample_appointments_csv())
    
    # 録音データの作成
    recording_data = generator.create_sample_recording_data()
    
    # マッチング実行
    matcher = PatientMatcher()
    result = matcher.match_patient_doctor(recording_data, 'sample_appointments.csv')
    
    print("患者マッチング結果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


if __name__ == "__main__":
    test_patient_matching()
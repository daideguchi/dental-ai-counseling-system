"""
音声・テキストデータの統一処理モジュール
PLAUD NOTEやNottaなど異なる形式のデータを統一形式に変換
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path
import docx

# 音声系ライブラリは任意依存。Python 3.13 では pyaudioop が無い環境があり得るためガードする
AUDIO_AVAILABLE = False
try:
    from pydub import AudioSegment  # type: ignore
    AUDIO_AVAILABLE = True
except Exception as _e:
    # ログのみ。テキスト/CSV処理は継続可能
    print(f"[data_processor] Optional audio libs unavailable, fallback to text-only mode: {_e}")


class DataProcessor:
    """データ処理の統一インターフェース"""
    
    def __init__(self):
        self.supported_formats = {
            'plaud_note': ['txt', 'srt', 'docx', 'pdf', 'mp3', 'wav', 'md'],
            'notta': ['txt', 'docx', 'srt', 'pdf', 'csv', 'xlsx', 'mp3', 'wav']
        }
    
    def process_file(self, file_path: str, source: str = 'auto') -> Dict:
        """
        ファイルを処理して統一形式に変換
        
        Args:
            file_path: 処理するファイルのパス
            source: データソース ('plaud_note', 'notta', 'auto')
            
        Returns:
            統一形式のデータ辞書
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower().lstrip('.')
        
        if source == 'auto':
            source = self._detect_source(file_path)
        
        # ファイル形式に応じた処理
        if extension in ['txt']:
            content = self._process_text_file(file_path)
        elif extension in ['srt']:
            content = self._process_srt_file(file_path)
        elif extension in ['docx']:
            content = self._process_docx_file(file_path)
        elif extension in ['csv']:
            content = self._process_csv_file(file_path)
        elif extension in ['mp3', 'wav']:
            content = self._process_audio_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")
        
        # 統一形式に変換
        unified_data = self._create_unified_format(content, source, file_path)
        
        return unified_data
    
    def _detect_source(self, file_path: Path) -> str:
        """ファイル名やメタデータからソースを推定"""
        filename = file_path.name.lower()
        
        if 'plaud' in filename or 'plaud_note' in filename:
            return 'plaud_note'
        elif 'notta' in filename:
            return 'notta'
        else:
            return 'unknown'
    
    def _process_text_file(self, file_path: Path) -> Dict:
        """テキストファイルの処理"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            'type': 'transcript',
            'content': content,
            'speaker_segments': self._extract_speaker_segments(content)
        }
    
    def _process_srt_file(self, file_path: Path) -> Dict:
        """SRTファイル（字幕形式）の処理"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        segments = []
        blocks = content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                timestamp = lines[1]
                text = ' '.join(lines[2:])
                
                segments.append({
                    'timestamp': timestamp,
                    'text': text,
                    'speaker': self._detect_speaker(text)
                })
        
        return {
            'type': 'transcript_with_timestamps',
            'content': '\n'.join([seg['text'] for seg in segments]),
            'speaker_segments': segments
        }
    
    def _process_docx_file(self, file_path: Path) -> Dict:
        """DOCXファイルの処理"""
        doc = docx.Document(file_path)
        content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        
        return {
            'type': 'transcript',
            'content': content,
            'speaker_segments': self._extract_speaker_segments(content)
        }
    
    def _process_csv_file(self, file_path: Path) -> Dict:
        """CSVファイルの処理（Notta形式）"""
        df = pd.read_csv(file_path)
        
        # Nottaの一般的なCSV形式を想定
        if 'Speaker' in df.columns and 'Text' in df.columns:
            segments = []
            for _, row in df.iterrows():
                segments.append({
                    'speaker': row.get('Speaker', 'unknown'),
                    'text': row.get('Text', ''),
                    'timestamp': row.get('Timestamp', '')
                })
            
            content = '\n'.join([f"{seg['speaker']}: {seg['text']}" for seg in segments])
            
            return {
                'type': 'transcript_with_speakers',
                'content': content,
                'speaker_segments': segments
            }
        else:
            # 一般的なCSV形式
            content = df.to_string()
            return {
                'type': 'data',
                'content': content,
                'speaker_segments': []
            }
    
    def _process_audio_file(self, file_path: Path) -> Dict:
        """音声ファイルの処理（任意依存が無い場合はダミー情報にフォールバック）"""
        duration = None
        if AUDIO_AVAILABLE:
            try:
                audio = AudioSegment.from_file(file_path)  # noqa: F401
                duration = len(audio)
            except Exception as e:
                print(f"[data_processor] audio load failed, fallback to dummy: {e}")
        else:
            print("[data_processor] AUDIO_AVAILABLE is False; skipping actual audio parsing")
        
        return {
            'type': 'audio',
            'content': f"Audio file: {file_path.name}",
            'duration_ms': duration,
            'file_path': str(file_path),
            'speaker_segments': []
        }
    
    def _extract_speaker_segments(self, content: str) -> List[Dict]:
        """テキストから話者セグメントを抽出"""
        segments = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            speaker = self._detect_speaker(line)
            segments.append({
                'speaker': speaker,
                'text': line,
                'timestamp': ''
            })
        
        return segments
    
    def _detect_speaker(self, text: str) -> str:
        """テキストから話者を推定"""
        text_lower = text.lower()
        
        # 患者の発言パターン
        patient_keywords = ['痛い', 'しみる', '気になる', '不安', 'お願いします', 'はい、']
        # 医師の発言パターン  
        doctor_keywords = ['診察', '治療', '処置', 'では', 'そうですね', '確認', '検査']
        
        patient_score = sum(1 for keyword in patient_keywords if keyword in text_lower)
        doctor_score = sum(1 for keyword in doctor_keywords if keyword in text_lower)
        
        if patient_score > doctor_score:
            return 'patient'
        elif doctor_score > patient_score:
            return 'doctor'
        else:
            return 'unknown'
    
    def _create_unified_format(self, content: Dict, source: str, file_path: Path) -> Dict:
        """統一形式のデータ構造を作成"""
        return {
            'recording_id': f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'source': source,
            'file_path': str(file_path),
            'file_type': content['type'],
            'processed_at': datetime.now().isoformat(),
            'transcript': content['content'],
            'speaker_segments': content['speaker_segments'],
            'metadata': {
                'duration_ms': content.get('duration_ms'),
                'original_filename': file_path.name
            }
        }


class SampleDataGenerator:
    """サンプルデータ生成クラス"""
    
    @staticmethod
    def create_plaud_note_sample() -> str:
        """PLAUD NOTE形式のサンプルテキストを生成"""
        sample_text = """患者: おはようございます。右上の奥歯が痛くて来ました。

医師: おはようございます。いつ頃からの痛みでしょうか？

患者: 2週間くらい前からです。冷たいものを飲むとしみるんです。

医師: そうですね。では診察させていただきます。右上の第一大臼歯ですね。深いう蝕が見られます。

患者: 虫歯ですか？

医師: はい、虫歯です。神経に近いところまで進んでいますが、まだ神経は生きているようです。

患者: 治療はどのようになりますか？

医師: 虫歯の部分を削って、白い詰め物をする治療になります。1回で終わる予定です。

患者: 痛みはありますか？

医師: 麻酔をしますので、治療中の痛みはありません。

患者: わかりました。お願いします。

医師: では次回、治療を行いましょう。来週の同じ時間はいかがですか？

患者: はい、大丈夫です。"""
        
        return sample_text
    
    @staticmethod
    def create_notta_csv_sample() -> str:
        """Notta CSV形式のサンプルデータを生成"""
        csv_content = """Speaker,Text,Timestamp
Patient,おはようございます。右上の奥歯が痛くて来ました。,00:00:05
Doctor,おはようございます。いつ頃からの痛みでしょうか？,00:00:10
Patient,2週間くらい前からです。冷たいものを飲むとしみるんです。,00:00:15
Doctor,そうですね。では診察させていただきます。右上の第一大臼歯ですね。深いう蝕が見られます。,00:00:25
Patient,虫歯ですか？,00:00:35
Doctor,はい、虫歯です。神経に近いところまで進んでいますが、まだ神経は生きているようです。,00:00:40
Patient,治療はどのようになりますか？,00:00:50
Doctor,虫歯の部分を削って、白い詰め物をする治療になります。1回で終わる予定です。,00:00:55
Patient,痛みはありますか？,00:01:05
Doctor,麻酔をしますので、治療中の痛みはありません。,00:01:10
Patient,わかりました。お願いします。,00:01:15
Doctor,では次回、治療を行いましょう。来週の同じ時間はいかがですか？,00:01:20
Patient,はい、大丈夫です。,00:01:25"""
        
        return csv_content


if __name__ == "__main__":
    # テスト用のサンプルデータ作成
    generator = SampleDataGenerator()
    
    # PLAUD NOTEサンプル
    with open('sample_plaud_note.txt', 'w', encoding='utf-8') as f:
        f.write(generator.create_plaud_note_sample())
    
    # Nottaサンプル
    with open('sample_notta.csv', 'w', encoding='utf-8') as f:
        f.write(generator.create_notta_csv_sample())
    
    # データ処理テスト
    processor = DataProcessor()
    
    # PLAUD NOTEデータの処理
    plaud_data = processor.process_file('sample_plaud_note.txt', 'plaud_note')
    print("PLAUD NOTE処理結果:")
    print(json.dumps(plaud_data, ensure_ascii=False, indent=2))
    
    # Nottaデータの処理
    notta_data = processor.process_file('sample_notta.csv', 'notta')
    print("\nNotta処理結果:")
    print(json.dumps(notta_data, ensure_ascii=False, indent=2))
#!/usr/bin/env python3
"""
NottaとPLAUD NOTEの実際の出力形式に対応したパーサー
正確な出力形式に基づいた処理を実装
"""

import csv
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

class RealisticOutputParser:
    """実際の出力形式に対応したパーサークラス"""
    
    def __init__(self):
        self.supported_formats = {
            'plaud_note': ['txt', 'srt', 'docx', 'pdf', 'md'],
            'notta': ['txt', 'docx', 'srt', 'pdf', 'csv', 'xlsx']
        }
    
    def parse_plaud_note_txt(self, file_path: str) -> Dict:
        """
        PLAUD NOTE TXT形式の解析
        特徴: 話者区別なし、段落区切りで発言を分離
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # 段落で分割（PLAUD NOTEの特徴）
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        parsed_data = {
            'source': 'plaud_note',
            'format': 'txt',
            'total_segments': len(paragraphs),
            'has_speaker_labels': False,
            'has_timestamps': False,
            'segments': []
        }
        
        # 話者を推定（医師/患者の交互パターンを仮定）
        for i, paragraph in enumerate(paragraphs):
            # 簡単な話者推定ロジック
            speaker = self._estimate_speaker_from_content(paragraph, i)
            
            parsed_data['segments'].append({
                'sequence': i + 1,
                'speaker': speaker,
                'speaker_label': f"Speaker {1 if speaker == 'doctor' else 2}",
                'text': paragraph,
                'timestamp_start': None,
                'timestamp_end': None,
                'confidence': 0.85  # PLAUD NOTEの推定信頼度
            })
        
        return parsed_data
    
    def parse_plaud_note_markdown(self, file_path: str) -> Dict:
        """
        PLAUD NOTE Markdown形式の解析（要約データ）
        特徴: 構造化された要約情報
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Markdownの構造を解析
        sections = self._parse_markdown_sections(content)
        
        return {
            'source': 'plaud_note',
            'format': 'markdown_summary',
            'sections': sections,
            'is_summary': True,
            'structured_data': self._extract_structured_summary(sections)
        }
    
    def parse_notta_csv(self, file_path: str) -> Dict:
        """
        Notta CSV形式の解析
        特徴: Speaker, Start Time, End Time, Duration, Text列を持つ
        """
        parsed_data = {
            'source': 'notta',
            'format': 'csv',
            'has_speaker_labels': True,
            'has_timestamps': True,
            'segments': []
        }
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                # Nottaの標準的なCSV列名に対応
                speaker_raw = row.get('Speaker', f'Speaker {i % 2 + 1}')
                start_time = row.get('Start Time', '')
                end_time = row.get('End Time', '')
                duration = row.get('Duration', '')
                text = row.get('Text', '')
                
                # 話者をdoctor/patientに変換
                speaker = self._convert_notta_speaker(speaker_raw, text)
                
                parsed_data['segments'].append({
                    'sequence': i + 1,
                    'speaker': speaker,
                    'speaker_label': speaker_raw,
                    'text': text,
                    'timestamp_start': start_time,
                    'timestamp_end': end_time,
                    'duration': duration,
                    'confidence': 0.92  # Nottaの平均信頼度
                })
        
        parsed_data['total_segments'] = len(parsed_data['segments'])
        return parsed_data
    
    def parse_notta_xlsx_simulation(self, file_path: str) -> Dict:
        """
        Notta XLSX形式のシミュレーション解析
        実際のXLSXファイルの代わりにテキストファイルから解析
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # テキストからデータ行を抽出
        rows = []
        for line in content.split('\n'):
            if line.startswith('Row '):
                # "Row 1: Speaker 1, 00:00:05, ..." の形式を解析
                parts = line.split(': ', 1)[1].split(', ')
                if len(parts) >= 6:
                    rows.append({
                        'Speaker': parts[0],
                        'Start Time': parts[1],
                        'End Time': parts[2],
                        'Duration': parts[3],
                        'Text': parts[4],
                        'Confidence Score': float(parts[5]) if parts[5].replace('.', '').isdigit() else 0.9
                    })
        
        parsed_data = {
            'source': 'notta',
            'format': 'xlsx',
            'has_speaker_labels': True,
            'has_timestamps': True,
            'has_confidence_scores': True,
            'segments': []
        }
        
        for i, row in enumerate(rows):
            speaker = self._convert_notta_speaker(row['Speaker'], row['Text'])
            
            parsed_data['segments'].append({
                'sequence': i + 1,
                'speaker': speaker,
                'speaker_label': row['Speaker'],
                'text': row['Text'],
                'timestamp_start': row['Start Time'],
                'timestamp_end': row['End Time'],
                'duration': row['Duration'],
                'confidence': row['Confidence Score']
            })
        
        parsed_data['total_segments'] = len(parsed_data['segments'])
        return parsed_data
    
    def _estimate_speaker_from_content(self, text: str, sequence: int) -> str:
        """
        テキスト内容から話者を推定
        PLAUD NOTEは話者ラベルがないため、内容から推定
        """
        # 医師らしい表現
        doctor_patterns = [
            r'診察', r'検査', r'治療', r'処置', r'薬', r'症状', r'診断',
            r'では.*ましょう', r'.*ですね', r'.*認めます', r'.*と思われます',
            r'局所麻酔', r'う蝕', r'歯髄', r'充填', r'抜歯'
        ]
        
        # 患者らしい表現
        patient_patterns = [
            r'痛い', r'しみる', r'気になる', r'心配', r'不安',
            r'いつ頃', r'どのくらい', r'お願いします', r'分かりました',
            r'.*んです', r'.*でしょうか'
        ]
        
        doctor_score = sum(1 for pattern in doctor_patterns if re.search(pattern, text))
        patient_score = sum(1 for pattern in patient_patterns if re.search(pattern, text))
        
        if doctor_score > patient_score:
            return 'doctor'
        elif patient_score > doctor_score:
            return 'patient'
        else:
            # スコアが同じ場合は交互パターンを仮定
            return 'doctor' if sequence % 2 == 0 else 'patient'
    
    def _convert_notta_speaker(self, speaker_label: str, text: str) -> str:
        """
        NottaのSpeaker 1/2を医師/患者に変換
        """
        # テキスト内容も考慮して判定
        if 'Speaker 1' in speaker_label:
            # Speaker 1が医師の可能性が高い場合の判定
            if any(word in text for word in ['診察', '治療', '薬', '症状', '診断']):
                return 'doctor'
            else:
                # 内容から判断できない場合はSpeaker 1を医師と仮定
                return 'doctor'
        else:
            return 'patient'
    
    def _parse_markdown_sections(self, content: str) -> Dict:
        """Markdownの構造を解析"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line[3:].strip()
                current_content = []
            elif line.startswith('# '):
                sections['title'] = line[2:].strip()
            else:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _extract_structured_summary(self, sections: Dict) -> Dict:
        """要約から構造化データを抽出"""
        structured = {
            'chief_complaint': '',
            'findings': '',
            'diagnosis': '',
            'treatment_plan': '',
            'patient_instructions': ''
        }
        
        # セクション名から対応する項目にマッピング
        section_mapping = {
            '主な内容': 'chief_complaint',
            '診察所見': 'findings',
            '診断': 'diagnosis',
            '治療計画': 'treatment_plan',
            '患者指導': 'patient_instructions'
        }
        
        for section_name, content in sections.items():
            if section_name in section_mapping:
                structured[section_mapping[section_name]] = content
        
        return structured
    
    def convert_to_unified_format(self, parsed_data: Dict) -> Dict:
        """
        各形式のデータを統一フォーマットに変換
        データベース保存用の標準形式
        """
        unified = {
            'metadata': {
                'source_system': parsed_data['source'],
                'original_format': parsed_data['format'],
                'total_segments': parsed_data.get('total_segments', 0),
                'has_timestamps': parsed_data.get('has_timestamps', False),
                'has_speaker_labels': parsed_data.get('has_speaker_labels', False),
                'processing_timestamp': datetime.now().isoformat()
            },
            'conversation': [],
            'summary_data': parsed_data.get('structured_data', {})
        }
        
        # セグメントを統一形式に変換
        for segment in parsed_data.get('segments', []):
            unified_segment = {
                'sequence': segment['sequence'],
                'speaker': segment['speaker'],
                'speaker_label': segment.get('speaker_label', ''),
                'text': segment['text'],
                'timestamp_start': segment.get('timestamp_start'),
                'timestamp_end': segment.get('timestamp_end'),
                'duration': segment.get('duration'),
                'confidence_score': segment.get('confidence', 0.9)
            }
            unified['conversation'].append(unified_segment)
        
        return unified

def demo_realistic_parsing():
    """実際の出力形式を使ったデモンストレーション"""
    print("🎯 実際の出力形式対応パーサー - デモ")
    print("=" * 60)
    
    parser = RealisticOutputParser()
    
    # 1. PLAUD NOTE TXT形式
    print("\n📄 PLAUD NOTE TXT形式の解析:")
    plaud_txt = parser.parse_plaud_note_txt('realistic_sample_data/plaud_note_transcript.txt')
    print(f"  - 総セグメント数: {plaud_txt['total_segments']}")
    print(f"  - 話者ラベル: {plaud_txt['has_speaker_labels']}")
    print(f"  - タイムスタンプ: {plaud_txt['has_timestamps']}")
    
    # 2. PLAUD NOTE Markdown要約
    print("\n📝 PLAUD NOTE Markdown要約の解析:")
    plaud_md = parser.parse_plaud_note_markdown('realistic_sample_data/plaud_note_summary.md')
    print(f"  - セクション数: {len(plaud_md['sections'])}")
    print(f"  - 構造化データ: {len(plaud_md['structured_data'])}項目")
    
    # 3. Notta CSV形式
    print("\n📊 Notta CSV形式の解析:")
    notta_csv = parser.parse_notta_csv('realistic_sample_data/notta_transcript.csv')
    print(f"  - 総セグメント数: {notta_csv['total_segments']}")
    print(f"  - 話者ラベル: {notta_csv['has_speaker_labels']}")
    print(f"  - タイムスタンプ: {notta_csv['has_timestamps']}")
    
    # 4. Notta XLSX形式（シミュレーション）
    print("\n📈 Notta XLSX形式の解析:")
    notta_xlsx = parser.parse_notta_xlsx_simulation('realistic_sample_data/notta_transcript.xlsx')
    print(f"  - 総セグメント数: {notta_xlsx['total_segments']}")
    print(f"  - 信頼度スコア: {notta_xlsx['has_confidence_scores']}")
    
    # 5. 統一フォーマットへの変換
    print("\n🔄 統一フォーマットへの変換:")
    unified_plaud = parser.convert_to_unified_format(plaud_txt)
    unified_notta = parser.convert_to_unified_format(notta_csv)
    
    print(f"  - PLAUD NOTE統一形式: {len(unified_plaud['conversation'])}発言")
    print(f"  - Notta統一形式: {len(unified_notta['conversation'])}発言")
    
    # 6. 結果をJSONで出力
    os.makedirs('output/realistic_parsing', exist_ok=True)
    
    with open('output/realistic_parsing/plaud_unified.json', 'w', encoding='utf-8') as f:
        json.dump(unified_plaud, f, ensure_ascii=False, indent=2)
    
    with open('output/realistic_parsing/notta_unified.json', 'w', encoding='utf-8') as f:
        json.dump(unified_notta, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 解析結果をJSONファイルに出力:")
    print("  - output/realistic_parsing/plaud_unified.json")
    print("  - output/realistic_parsing/notta_unified.json")
    
    # 7. 比較分析
    print("\n📊 形式別比較分析:")
    print(f"  PLAUD NOTE TXT:")
    print(f"    - 利点: シンプル、軽量")
    print(f"    - 欠点: 話者区別なし、タイムスタンプなし")
    print(f"    - 推定精度: 中程度（内容ベース推定）")
    
    print(f"  Notta CSV:")
    print(f"    - 利点: 話者区別、タイムスタンプ、構造化")
    print(f"    - 欠点: 信頼度情報なし")
    print(f"    - 推定精度: 高（明示的ラベル）")
    
    print(f"  Notta XLSX:")
    print(f"    - 利点: 全情報含有、信頼度スコア")
    print(f"    - 欠点: ファイルサイズ大、処理複雑")
    print(f"    - 推定精度: 最高（全データ利用可能）")

if __name__ == "__main__":
    demo_realistic_parsing()
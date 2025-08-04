"""
SOAP形式変換エンジン
文字起こしテキストからSOAP形式のカルテを生成
"""

import re
import json
from typing import Dict, List, Optional
from datetime import datetime


class SOAPGenerator:
    """SOAP形式のカルテを生成するクラス"""
    
    def __init__(self):
        # 歯科専門用語辞書
        self.dental_terms = {
            'symptoms': ['痛い', 'しみる', '腫れ', '出血', '違和感', 'ズキズキ', 'ジンジン'],
            'teeth_numbers': ['右上', '左上', '右下', '左下', '前歯', '奥歯', '犬歯', '臼歯'],
            'conditions': ['う蝕', '虫歯', '歯周病', '歯肉炎', '歯髄炎', '根尖病変'],
            'treatments': ['充填', '抜歯', '根管治療', '歯石除去', 'クリーニング', '被せ物']
        }
        
        # SOAPセクション識別パターン
        self.soap_patterns = {
            'subjective': ['痛い', '気になる', '不安', '希望', '要望', '感じる'],
            'objective': ['診察', '所見', '確認', '検査', '状態', '認める'],
            'assessment': ['診断', '評価', '判断', '考えられる', '疑われる'],
            'plan': ['治療', '計画', '予定', '次回', 'お願い', '指導']
        }
    
    def generate_soap(self, transcript_data: Dict) -> Dict:
        """
        文字起こしデータからSOAP形式のカルテを生成
        
        Args:
            transcript_data: 統一形式の文字起こしデータ
            
        Returns:
            SOAP形式のカルテデータ
        """
        try:
            # 話者セグメントの分析
            patient_statements = self._extract_patient_statements(transcript_data)
            doctor_statements = self._extract_doctor_statements(transcript_data)
            
            # SOAP各セクションの生成
            subjective = self._generate_subjective(patient_statements)
            objective = self._generate_objective(doctor_statements)
            assessment = self._generate_assessment(doctor_statements)
            plan = self._generate_plan(doctor_statements)
            
            # SOAP形式でまとめ
            soap_note = {
                'S': subjective,
                'O': objective,
                'A': assessment,
                'P': plan
            }
            
            return {
                'status': 'success',
                'recording_id': transcript_data.get('recording_id'),
                'generated_at': datetime.now().isoformat(),
                'soap_note': soap_note,
                'confidence_score': self._calculate_confidence(soap_note),
                'raw_transcript': transcript_data.get('transcript', '')
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error_message': str(e),
                'recording_id': transcript_data.get('recording_id'),
                'soap_note': self._generate_default_soap()
            }
    
    def _extract_patient_statements(self, transcript_data: Dict) -> List[str]:
        """患者の発言を抽出"""
        patient_statements = []
        
        for segment in transcript_data.get('speaker_segments', []):
            if segment.get('speaker') == 'patient':
                patient_statements.append(segment.get('text', ''))
        
        # 話者分離ができていない場合の代替処理
        if not patient_statements:
            transcript = transcript_data.get('transcript', '')
            patient_statements = self._extract_patient_from_text(transcript)
        
        return patient_statements
    
    def _extract_doctor_statements(self, transcript_data: Dict) -> List[str]:
        """医師の発言を抽出"""
        doctor_statements = []
        
        for segment in transcript_data.get('speaker_segments', []):
            if segment.get('speaker') == 'doctor':
                doctor_statements.append(segment.get('text', ''))
        
        # 話者分離ができていない場合の代替処理
        if not doctor_statements:
            transcript = transcript_data.get('transcript', '')
            doctor_statements = self._extract_doctor_from_text(transcript)
        
        return doctor_statements
    
    def _extract_patient_from_text(self, transcript: str) -> List[str]:
        """テキストから患者の発言を推定抽出"""
        lines = transcript.split('\n')
        patient_statements = []
        
        for line in lines:
            line = line.strip()
            if any(symptom in line for symptom in self.dental_terms['symptoms']):
                patient_statements.append(line)
            elif any(pattern in line for pattern in ['痛くて', '気になって', 'お願いします']):
                patient_statements.append(line)
        
        return patient_statements
    
    def _extract_doctor_from_text(self, transcript: str) -> List[str]:
        """テキストから医師の発言を推定抽出"""
        lines = transcript.split('\n')
        doctor_statements = []
        
        for line in lines:
            line = line.strip()
            if any(term in line for term in self.dental_terms['conditions']):
                doctor_statements.append(line)
            elif any(pattern in line for pattern in ['診察', '治療', '確認', 'では']):
                doctor_statements.append(line)
        
        return doctor_statements
    
    def _generate_subjective(self, patient_statements: List[str]) -> str:
        """主観的情報（S）の生成"""
        if not patient_statements:
            return "患者の主訴：記録なし"
        
        # 主要な症状を抽出
        symptoms = []
        duration = []
        concerns = []
        
        for statement in patient_statements:
            # 症状の抽出
            for symptom in self.dental_terms['symptoms']:
                if symptom in statement:
                    symptoms.append(f"「{statement.strip()}」")
                    break
            
            # 期間の抽出
            duration_match = re.search(r'(\d+)(日|週間|ヶ月|年)', statement)
            if duration_match:
                duration.append(duration_match.group(0))
            
            # 不安や要望の抽出
            if any(word in statement for word in ['不安', '心配', '希望', '要望']):
                concerns.append(statement.strip())
        
        # S（主観的情報）の構成
        subjective_parts = []
        
        if symptoms:
            subjective_parts.append(f"主訴：{', '.join(symptoms[:2])}")  # 最大2つの症状
        
        if duration:
            subjective_parts.append(f"症状の期間：{duration[0]}前から")
        
        if concerns:
            subjective_parts.append(f"患者の懸念：{concerns[0]}")
        
        return '。'.join(subjective_parts) + '。' if subjective_parts else "患者の主訴：詳細な記録なし。"
    
    def _generate_objective(self, doctor_statements: List[str]) -> str:
        """客観的情報（O）の生成"""
        if not doctor_statements:
            return "診察所見：記録なし"
        
        # 診察所見を抽出
        findings = []
        examinations = []
        
        for statement in doctor_statements:
            # 所見の抽出
            if any(condition in statement for condition in self.dental_terms['conditions']):
                findings.append(statement.strip())
            
            # 検査結果の抽出
            if any(word in statement for word in ['確認', '診察', '検査', '状態']):
                examinations.append(statement.strip())
        
        # O（客観的情報）の構成
        objective_parts = []
        
        if examinations:
            objective_parts.append(f"診察：{examinations[0]}")
        
        if findings:
            objective_parts.append(f"所見：{findings[0]}")
        
        return '。'.join(objective_parts) + '。' if objective_parts else "診察所見：詳細な記録なし。"
    
    def _generate_assessment(self, doctor_statements: List[str]) -> str:
        """評価・診断（A）の生成"""
        if not doctor_statements:
            return "診断：記録なし"
        
        # 診断に関する発言を抽出
        diagnoses = []
        
        for statement in doctor_statements:
            # 診断名の抽出
            for condition in self.dental_terms['conditions']:
                if condition in statement:
                    diagnoses.append(condition)
            
            # 診断的な表現の抽出
            if any(word in statement for word in ['診断', '判断', '考えられる', '疑われる']):
                diagnoses.append(statement.strip())
        
        if diagnoses:
            # 重複を除去して最初の診断を使用
            unique_diagnoses = list(dict.fromkeys(diagnoses))
            return f"診断：{unique_diagnoses[0]}。"
        else:
            return "診断：要精査。"
    
    def _generate_plan(self, doctor_statements: List[str]) -> str:
        """計画（P）の生成"""
        if not doctor_statements:
            return "治療計画：記録なし"
        
        # 治療計画を抽出
        treatments = []
        next_appointments = []
        instructions = []
        
        for statement in doctor_statements:
            # 治療内容の抽出
            for treatment in self.dental_terms['treatments']:
                if treatment in statement:
                    treatments.append(statement.strip())
                    break
            
            # 次回予約の抽出
            if any(word in statement for word in ['次回', '来週', '予約']):
                next_appointments.append(statement.strip())
            
            # 指導内容の抽出
            if any(word in statement for word in ['指導', 'お願い', '注意']):
                instructions.append(statement.strip())
        
        # P（計画）の構成
        plan_parts = []
        
        if treatments:
            plan_parts.append(f"治療：{treatments[0]}")
        
        if next_appointments:
            plan_parts.append(f"次回：{next_appointments[0]}")
        
        if instructions:
            plan_parts.append(f"指導：{instructions[0]}")
        
        return '。'.join(plan_parts) + '。' if plan_parts else "治療計画：要検討。"
    
    def _calculate_confidence(self, soap_note: Dict) -> float:
        """SOAP生成の信頼度を計算"""
        confidence = 0.0
        
        # 各セクションの内容の充実度を評価
        for section, content in soap_note.items():
            if content and content != f"{section}：記録なし" and "記録なし" not in content:
                confidence += 0.25
        
        return min(confidence, 1.0)
    
    def _generate_default_soap(self) -> Dict:
        """デフォルトのSOAPテンプレート"""
        return {
            'S': '患者の主訴：記録の処理中にエラーが発生しました。',
            'O': '診察所見：記録の処理中にエラーが発生しました。',
            'A': '診断：要確認。',
            'P': '治療計画：要検討。'
        }


class SOAPFormatter:
    """SOAP形式の整形・出力クラス"""
    
    @staticmethod
    def format_for_rececon(soap_data: Dict) -> str:
        """レセコン投入用の形式に整形"""
        soap_note = soap_data.get('soap_note', {})
        
        formatted = f"""【カウンセリング記録】
日時：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}

S（主観的情報）：
{soap_note.get('S', '')}

O（客観的情報）：
{soap_note.get('O', '')}

A（評価・診断）：
{soap_note.get('A', '')}

P（計画）：
{soap_note.get('P', '')}

※AI生成による記録（要確認）
信頼度：{soap_data.get('confidence_score', 0):.1%}"""
        
        return formatted
    
    @staticmethod
    def format_as_json(soap_data: Dict) -> str:
        """JSON形式で出力"""
        return json.dumps(soap_data, ensure_ascii=False, indent=2)


def test_soap_generation():
    """SOAP生成機能のテスト"""
    
    # サンプル文字起こしデータ
    sample_transcript = {
        'recording_id': 'rec_20250126_1030',
        'transcript': '''患者: おはようございます。右上の奥歯が痛くて来ました。
医師: おはようございます。いつ頃からの痛みでしょうか？
患者: 2週間くらい前からです。冷たいものを飲むとしみるんです。
医師: そうですね。では診察させていただきます。右上の第一大臼歯ですね。深いう蝕が見られます。
患者: 虫歯ですか？
医師: はい、虫歯です。神経に近いところまで進んでいますが、まだ神経は生きているようです。
患者: 治療はどのようになりますか？
医師: 虫歯の部分を削って、白い詰め物をする治療になります。1回で終わる予定です。
患者: わかりました。お願いします。
医師: では次回、治療を行いましょう。来週の同じ時間はいかがですか？''',
        'speaker_segments': [
            {'speaker': 'patient', 'text': 'おはようございます。右上の奥歯が痛くて来ました。'},
            {'speaker': 'doctor', 'text': 'おはようございます。いつ頃からの痛みでしょうか？'},
            {'speaker': 'patient', 'text': '2週間くらい前からです。冷たいものを飲むとしみるんです。'},
            {'speaker': 'doctor', 'text': 'そうですね。では診察させていただきます。右上の第一大臼歯ですね。深いう蝕が見られます。'},
            {'speaker': 'patient', 'text': '虫歯ですか？'},
            {'speaker': 'doctor', 'text': 'はい、虫歯です。神経に近いところまで進んでいますが、まだ神経は生きているようです。'},
            {'speaker': 'patient', 'text': '治療はどのようになりますか？'},
            {'speaker': 'doctor', 'text': '虫歯の部分を削って、白い詰め物をする治療になります。1回で終わる予定です。'},
            {'speaker': 'patient', 'text': 'わかりました。お願いします。'},
            {'speaker': 'doctor', 'text': 'では次回、治療を行いましょう。来週の同じ時間はいかがですか？'}
        ]
    }
    
    # SOAP生成
    generator = SOAPGenerator()
    soap_result = generator.generate_soap(sample_transcript)
    
    print("SOAP生成結果:")
    print(json.dumps(soap_result, ensure_ascii=False, indent=2))
    
    # レセコン用フォーマット
    formatter = SOAPFormatter()
    rececon_format = formatter.format_for_rececon(soap_result)
    
    print("\nレセコン投入用フォーマット:")
    print(rececon_format)
    
    return soap_result


if __name__ == "__main__":
    test_soap_generation()
#!/usr/bin/env python3
"""
Gemini APIを使用した歯科カウンセリングデータ処理
患者・医師の自動特定とSOAP形式変換
"""

import google.generativeai as genai
import json
import re
from typing import Dict, List, Optional, Tuple

class GeminiProcessor:
    def __init__(self, api_key: str):
        """Gemini API初期化"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def identify_patient_doctor(self, conversation_text: str) -> Dict:
        """
        会話内容から患者・医師を自動特定
        """
        prompt = f"""
以下の歯科カウンセリングの会話から、患者名と医師名を特定してください。

会話内容:
{conversation_text}

以下のJSON形式で回答してください:
{{
    "patient_name": "患者の名前（例：田中太郎）",
    "doctor_name": "医師の名前（例：山田医師）",
    "confidence_patient": 0.95,
    "confidence_doctor": 0.90,
    "reasoning": "特定の根拠"
}}

注意事項:
- 「〜さん」「〜先生」などの敬語から推定
- 名前が明示されていない場合は「患者」「医師」として記録
- 信頼度は0.0-1.0で評価
- 推定根拠を簡潔に説明
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSONブロックを抽出
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '{' in response_text and '}' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                response_text = response_text[json_start:json_end]
            
            result = json.loads(response_text)
            return result
        except Exception as e:
            print(f"Debug - Response text: {response.text if 'response' in locals() else 'No response'}")
            return {
                "patient_name": "患者",
                "doctor_name": "医師", 
                "confidence_patient": 0.5,
                "confidence_doctor": 0.5,
                "reasoning": f"自動特定エラー: {str(e)}"
            }
    
    def convert_to_soap(self, conversation_text: str, patient_name: str = "患者", doctor_name: str = "医師") -> Dict:
        """
        会話内容をSOAP形式に変換
        """
        prompt = f"""
以下の歯科カウンセリングの会話をSOAP形式に変換してください。

患者名: {patient_name}
医師名: {doctor_name}

会話内容:
{conversation_text}

以下のJSON形式で回答してください:
{{
    "S": "主観的情報（患者の訴え、症状、感じていること）",
    "O": "客観的情報（医師の診察所見、検査結果、観察事実）", 
    "A": "評価・診断（医師の診断、病状評価、リスク評価）",
    "P": "計画（治療計画、次回予約、患者指導）",
    "confidence": 0.95,
    "key_points": ["重要なポイント1", "重要なポイント2"]
}}

SOAP分類の基準:
- S: 患者が「痛い」「しみる」「気になる」など主観的に述べた内容
- O: 医師が「認める」「確認」「検査結果」など客観的に観察した内容
- A: 医師の「診断」「評価」「〜と考えられる」などの判断
- P: 「治療します」「次回〜」「〜してください」などの今後の計画

歯科特有の用語を正確に分類してください。
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSONブロックを抽出
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '{' in response_text and '}' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                response_text = response_text[json_start:json_end]
            
            result = json.loads(response_text)
            return result
        except Exception as e:
            print(f"Debug - SOAP Response text: {response.text if 'response' in locals() else 'No response'}")
            return {
                "S": "自動変換エラーが発生しました",
                "O": "自動変換エラーが発生しました", 
                "A": "自動変換エラーが発生しました",
                "P": "自動変換エラーが発生しました",
                "confidence": 0.0,
                "key_points": [f"エラー: {str(e)}"]
            }
    
    def analyze_conversation_quality(self, conversation_text: str) -> Dict:
        """
        会話品質の分析（将来機能）
        """
        prompt = f"""
以下の歯科カウンセリング会話の品質を分析してください。

会話内容:
{conversation_text}

以下の観点で評価し、JSON形式で回答してください:
{{
    "communication_quality": 0.85,
    "patient_understanding": 0.90,
    "doctor_explanation": 0.80,
    "treatment_consent_likelihood": 0.75,
    "improvement_suggestions": [
        "より詳細な説明が必要",
        "患者の不安に対するフォローアップ"
    ],
    "positive_aspects": [
        "丁寧な説明",
        "患者の質問に適切に回答"
    ]
}}

評価基準:
- communication_quality: 全体的なコミュニケーションの質
- patient_understanding: 患者の理解度
- doctor_explanation: 医師の説明の分かりやすさ
- treatment_consent_likelihood: 治療同意の可能性
- 各スコアは0.0-1.0で評価
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSONブロックを抽出
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '{' in response_text and '}' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                response_text = response_text[json_start:json_end]
            
            result = json.loads(response_text)
            return result
        except Exception as e:
            print(f"Debug - Quality Response text: {response.text if 'response' in locals() else 'No response'}")
            return {
                "communication_quality": 0.5,
                "patient_understanding": 0.5,
                "doctor_explanation": 0.5,
                "treatment_consent_likelihood": 0.5,
                "improvement_suggestions": [f"分析エラー: {str(e)}"],
                "positive_aspects": []
            }

    def generate_custom_analysis(self, conversation_text: str) -> Dict:
        """
        AIによるカスタム分析データ生成
        元データにはない情報をAIが推定・生成
        """
        prompt = f"""
以下の歯科カウンセリング会話から、元データにはない追加情報をAIが分析・生成してください：

会話内容:
{conversation_text}

以下の項目を分析し、JSON形式で回答してください:
{{
    "emotion_analysis": {{
        "patient_anxiety_level": 0.7,
        "patient_trust_level": 0.6,
        "doctor_empathy_score": 0.8,
        "stress_indicators": ["痛み", "不安", "時間的プレッシャー"],
        "emotional_state": "心配だが協力的",
        "communication_comfort": 0.75
    }},
    "treatment_assessment": {{
        "urgency_level": 0.8,
        "pain_severity_estimated": 6,
        "treatment_complexity": "中程度",
        "patient_compliance_prediction": 0.9,
        "treatment_success_probability": 0.85
    }},
    "risk_factors": [
        "虫歯の進行リスク",
        "神経への影響可能性",
        "治療遅延による悪化"
    ],
    "satisfaction_prediction": 0.85,
    "follow_up_recommendations": [
        "1週間後の経過確認",
        "痛み止めの処方検討",
        "口腔ケア指導の実施"
    ],
    "clinical_insights": {{
        "patient_education_needs": ["虫歯予防", "口腔ケア方法"],
        "communication_style_preference": "詳細な説明を好む",
        "decision_making_pattern": "慎重だが協力的"
    }}
}}

分析基準:
- 会話の内容、トーン、質問パターンから患者の心理状態を推定
- 症状の記述から治療の緊急度や複雑さを評価
- 患者の反応から満足度や治療成功の可能性を予測
- 全て0.0-1.0のスケールで数値化（該当しない場合は配列で記述）
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSONブロックを抽出
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '{' in response_text and '}' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                response_text = response_text[json_start:json_end]
            
            # コメントを除去（// で始まる行を削除）
            lines = response_text.split('\n')
            clean_lines = []
            for line in lines:
                # // コメントを除去
                if '//' in line:
                    line = line[:line.find('//')]
                clean_lines.append(line)
            response_text = '\n'.join(clean_lines)
            
            result = json.loads(response_text)
            return result
            
        except Exception as e:
            print(f"Debug - Custom Analysis Response: {response.text if 'response' in locals() else 'No response'}")
            return {
                "emotion_analysis": {
                    "patient_anxiety_level": 0.5,
                    "patient_trust_level": 0.5,
                    "doctor_empathy_score": 0.5,
                    "stress_indicators": ["分析エラー"],
                    "emotional_state": "不明",
                    "communication_comfort": 0.5
                },
                "treatment_assessment": {
                    "urgency_level": 0.5,
                    "pain_severity_estimated": 5,
                    "treatment_complexity": "不明",
                    "patient_compliance_prediction": 0.5,
                    "treatment_success_probability": 0.5
                },
                "risk_factors": [f"分析エラー: {str(e)}"],
                "satisfaction_prediction": 0.5,
                "follow_up_recommendations": ["エラーにより生成できませんでした"],
                "clinical_insights": {
                    "patient_education_needs": ["エラー"],
                    "communication_style_preference": "不明",
                    "decision_making_pattern": "不明"
                }
            }

def demo_gemini_processing():
    """Gemini処理のデモンストレーション"""
    
    # APIキー設定
    API_KEY = "AIzaSyCeqgKbwdnORP-m4A-zUO6bbMHfwUviSts"
    
    # サンプル会話データ
    sample_conversation = """
    Speaker A: おはようございます。田中さん、今日はどのような症状でいらっしゃいましたか？
    
    Speaker B: 実は、右上の奥歯が2週間ほど前から冷たいものを飲むとしみるんです。特に朝起きた時がひどくて。
    
    Speaker A: なるほど。冷たいものでしみるということですね。痛みはどの程度でしょうか？
    
    Speaker B: ズキズキするような痛みではなくて、キーンとしみる感じです。でも最近は何もしなくても少し違和感があります。
    
    Speaker A: 分かりました。では診察させていただきますね。お口を大きく開けてください。
    
    Speaker A: 右上の第一大臼歯に深いう蝕を認めますね。歯髄に近い部分まで進行しているようです。打診痛はありませんが、冷水痛が陽性です。
    
    Speaker B: やっぱり虫歯でしたか。どのくらい悪いんでしょうか？
    
    Speaker A: かなり深い虫歯ですが、神経はまだ生きているようです。ただし、放置すると神経まで達してしまう可能性があります。
    
    Speaker B: 治療はどのようになりますか？
    
    Speaker A: 虫歯の部分を削って、コンポジットレジンという白い詰め物で修復します。1回の治療で完了予定です。
    
    Speaker B: 分かりました。いつ頃治療していただけますか？
    
    Speaker A: 来週の火曜日、2月2日の午前中はいかがでしょうか？
    
    Speaker B: はい、お願いします。
    """
    
    print("🤖 Gemini API処理デモ")
    print("=" * 50)
    
    try:
        processor = GeminiProcessor(API_KEY)
        
        # 1. 患者・医師特定
        print("\n👥 患者・医師自動特定:")
        identification = processor.identify_patient_doctor(sample_conversation)
        print(f"患者: {identification['patient_name']} (信頼度: {identification['confidence_patient']:.2f})")
        print(f"医師: {identification['doctor_name']} (信頼度: {identification['confidence_doctor']:.2f})")
        print(f"根拠: {identification['reasoning']}")
        
        # 2. SOAP変換
        print("\n📋 SOAP形式変換:")
        soap_result = processor.convert_to_soap(
            sample_conversation, 
            identification['patient_name'], 
            identification['doctor_name']
        )
        
        print(f"S (主観): {soap_result['S']}")
        print(f"O (客観): {soap_result['O']}")
        print(f"A (評価): {soap_result['A']}")
        print(f"P (計画): {soap_result['P']}")
        print(f"信頼度: {soap_result['confidence']:.2f}")
        
        # 3. 会話品質分析
        print("\n📊 会話品質分析:")
        quality = processor.analyze_conversation_quality(sample_conversation)
        print(f"コミュニケーション品質: {quality['communication_quality']:.2f}")
        print(f"患者理解度: {quality['patient_understanding']:.2f}")
        print(f"治療同意可能性: {quality['treatment_consent_likelihood']:.2f}")
        
        print("\n改善提案:")
        for suggestion in quality['improvement_suggestions']:
            print(f"  - {suggestion}")
        
        # 4. カスタム分析（AIが元データから新しい情報を生成）
        print("\n🎯 AIカスタム分析（元データにない情報を生成）:")
        custom_analysis = processor.generate_custom_analysis(sample_conversation)
        
        print(f"\n感情分析:")
        emotion = custom_analysis['emotion_analysis']
        print(f"  患者不安度: {emotion['patient_anxiety_level']:.2f}")
        print(f"  患者信頼度: {emotion['patient_trust_level']:.2f}")
        print(f"  医師共感度: {emotion['doctor_empathy_score']:.2f}")
        print(f"  感情状態: {emotion['emotional_state']}")
        
        print(f"\n治療評価:")
        treatment = custom_analysis['treatment_assessment']
        print(f"  緊急度: {treatment['urgency_level']:.2f}")
        print(f"  推定痛みレベル: {treatment['pain_severity_estimated']}/10")
        print(f"  治療成功確率: {treatment['treatment_success_probability']:.2f}")
        
        print(f"\nリスク要因:")
        for risk in custom_analysis['risk_factors']:
            print(f"  - {risk}")
        
        print(f"\n推奨フォローアップ:")
        for rec in custom_analysis['follow_up_recommendations']:
            print(f"  - {rec}")
        
        # 結果をJSONファイルに保存
        result = {
            'identification': identification,
            'soap': soap_result,
            'quality': quality,
            'custom_analysis': custom_analysis,  # 新しいカスタム分析データ
            'processed_at': '2025-01-26T10:30:00'
        }
        
        with open('output/gemini_processing_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 処理完了: output/gemini_processing_result.json")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    demo_gemini_processing()
from http.server import BaseHTTPRequestHandler
import json
import os
import re

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # CORS headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # Parse request
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            conversation_text = data.get('content', '')
            soap_data = data.get('soap', {})
            
            # Gemini API処理
            api_key = os.environ.get('GEMINI_API_KEY')
            if api_key and len(conversation_text) > 10:
                result = self._gemini_quality(conversation_text, soap_data, api_key)
            else:
                result = self._fallback_quality(conversation_text, soap_data)
            
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {"error": str(e), "fallback": True}
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _gemini_quality(self, conversation_text, soap_data, api_key):
        """Gemini AI による品質分析"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
以下の歯科医療会話を分析し、成約可能性（治療受諾の可能性）を評価してください。

会話内容:
{conversation_text}

以下の観点で0.0-1.0のスコアを算出してください:
1. success_possibility: 成約可能性（患者の治療受諾意欲）
2. patient_understanding: 患者理解度
3. treatment_consent: 治療同意の可能性

以下のJSON形式で回答してください:
{{
  "success_possibility": 0.0から1.0のスコア,
  "patient_understanding": 0.0から1.0のスコア,
  "treatment_consent": 0.0から1.0のスコア,
  "overall_quality": 0.0から1.0の総合品質,
  "improvements": ["改善提案1", "改善提案2"],
  "positives": ["良い点1", "良い点2"],
  "confidence": 0.0から1.0の信頼度
}}
"""
            
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            
            # Process log追加
            result["process_log"] = [
                "🤖 Gemini AI品質分析開始",
                f"📝 解析対象: {len(conversation_text)}文字の医療会話データ",
                "🧠 成約可能性・理解度・同意度の総合評価実行",
                f"📊 分析結果:",
                f"  - 成約可能性: {result.get('success_possibility', 0):.2f}",
                f"  - 患者理解度: {result.get('patient_understanding', 0):.2f}",
                f"  - 治療同意: {result.get('treatment_consent', 0):.2f}",
                f"✅ Gemini AI品質分析完了（信頼度: {result.get('confidence', 0):.2f}）"
            ]
            result["method"] = "gemini_ai_quality_analysis"
            
            return result
            
        except Exception as e:
            print(f"Gemini Quality API error: {e}")
            return self._fallback_quality(conversation_text, soap_data)
    
    def _fallback_quality(self, conversation_text, soap_data):
        """フォールバック品質分析"""
        lines = conversation_text.strip().split('\n')
        patient_lines = [line for line in lines if '患者' in line or 'Patient' in line]
        doctor_lines = [line for line in lines if '医師' in line or 'Doctor' in line or 'Dr.' in line]
        
        # 成約可能性計算（治療受諾重視）
        success_keywords = ['はい', 'お願いします', 'やります', '受けます', '同意', 'よろしく']
        hesitation_keywords = ['考えさせて', '迷って', '不安', '心配', '高い', '費用']
        
        patient_text = ' '.join(patient_lines)
        success_count = sum(1 for keyword in success_keywords if keyword in patient_text)
        hesitation_count = sum(1 for keyword in hesitation_keywords if keyword in patient_text)
        
        success_possibility = max(0.1, min(0.9, (success_count - hesitation_count * 0.5) / 3 + 0.3))
        
        # 患者理解度計算
        understanding_keywords = ['分かりました', 'なるほど', '理解', 'わかります']
        confusion_keywords = ['分からない', 'よくわからない', '難しい']
        
        understanding_count = sum(1 for keyword in understanding_keywords if keyword in patient_text)
        confusion_count = sum(1 for keyword in confusion_keywords if keyword in patient_text)
        
        patient_understanding = max(0.1, min(0.9, understanding_count / (understanding_count + confusion_count + 1) + 0.4))
        
        # 治療同意計算
        consent_keywords = ['治療', '処置', '次回', '予約']
        has_treatment_discussion = any(keyword in conversation_text for keyword in consent_keywords)
        treatment_consent = max(0.2, min(0.8, success_possibility * 0.7 + (0.2 if has_treatment_discussion else 0)))
        
        overall_quality = (success_possibility * 0.4 + patient_understanding * 0.3 + treatment_consent * 0.3)
        
        improvements = []
        positives = []
        
        if success_possibility < 0.5:
            improvements.append("患者の治療意欲を高める説明が必要")
        if patient_understanding < 0.6:
            improvements.append("より分かりやすい説明を心がける")
        if treatment_consent < 0.5:
            improvements.append("具体的な治療計画の提示が有効")
        
        if success_possibility > 0.7:
            positives.append("患者の治療への積極性が高い")
        if patient_understanding > 0.7:
            positives.append("患者の理解度が良好")
        if len(doctor_lines) > len(patient_lines):
            positives.append("医師からの丁寧な説明")
        
        return {
            "success_possibility": round(success_possibility, 2),
            "patient_understanding": round(patient_understanding, 2),
            "treatment_consent": round(treatment_consent, 2),
            "overall_quality": round(overall_quality, 2),
            "improvements": improvements or ["全体的に良好な会話"],
            "positives": positives or ["基本的なコミュニケーションは成立"],
            "confidence": 0.7,
            "process_log": [
                "📋 フォールバック品質分析実行",
                f"✅ 分析完了: 成約可能性={success_possibility:.2f}, 理解度={patient_understanding:.2f}"
            ],
            "method": "pattern_based_quality_analysis"
        }
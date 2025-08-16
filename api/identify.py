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
            
            # Gemini API処理（環境変数からAPIキー取得）
            api_key = os.environ.get('GEMINI_API_KEY')
            if api_key and len(conversation_text) > 10:
                result = self._gemini_identify(conversation_text, api_key)
            else:
                result = self._fallback_identify(conversation_text)
            
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
    
    def _gemini_identify(self, conversation_text, api_key):
        """Gemini AI による患者・医師識別"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
歯科医療の会話から患者名と医師名を正確に抽出してください。

会話内容:
{conversation_text}

以下のJSON形式で回答してください:
{{
  "patient_name": "患者の名前（見つからない場合は'患者'）",
  "doctor_name": "医師の名前（見つからない場合は'医師'）",
  "confidence_patient": 0.0から1.0の信頼度,
  "confidence_doctor": 0.0から1.0の信頼度,
  "reasoning": "判断根拠の説明"
}}
"""
            
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            
            # Process log追加
            result["process_log"] = [
                "🤖 Gemini AI患者・医師識別開始",
                f"📝 解析対象: {len(conversation_text)}文字の医療会話データ",
                "🧠 自然言語処理による名前抽出実行",
                f"✅ 識別完了: 患者「{result.get('patient_name', '不明')}」医師「{result.get('doctor_name', '不明')}」"
            ]
            result["method"] = "gemini_ai_identification"
            
            return result
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._fallback_identify(conversation_text)
    
    def _fallback_identify(self, conversation_text):
        """フォールバック識別"""
        patient_name = "患者"
        doctor_name = "医師"
        
        # 基本的なパターンマッチング
        patient_patterns = [
            r'([一-龯ぁ-んァ-ン]{2,6})[さ様]',
            r'患者[：:\s]*([一-龯ぁ-んァ-ン]{2,5})'
        ]
        
        for pattern in patient_patterns:
            matches = re.findall(pattern, conversation_text)
            if matches:
                patient_name = matches[0]
                break
        
        doctor_patterns = [
            r'([一-龯ぁ-んァ-ン]{2,6})\s*先生',
            r'Dr\.?\s*([一-龯A-Za-z]{2,6})'
        ]
        
        for pattern in doctor_patterns:
            matches = re.findall(pattern, conversation_text)
            if matches:
                doctor_name = matches[0]
                break
        
        return {
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "confidence_patient": 0.7 if patient_name != "患者" else 0.3,
            "confidence_doctor": 0.7 if doctor_name != "医師" else 0.3,
            "reasoning": "パターンマッチングによる識別",
            "process_log": [
                "📋 フォールバック識別実行",
                f"✅ 結果: 患者「{patient_name}」医師「{doctor_name}」"
            ],
            "method": "pattern_matching_fallback"
        }
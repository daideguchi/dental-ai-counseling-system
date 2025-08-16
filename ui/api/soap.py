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
            patient_name = data.get('patient_name', '患者')
            doctor_name = data.get('doctor_name', '医師')
            
            # Gemini API処理
            api_key = os.environ.get('GEMINI_API_KEY')
            if api_key and len(conversation_text) > 10:
                result = self._gemini_soap(conversation_text, patient_name, doctor_name, api_key)
            else:
                result = self._fallback_soap(conversation_text, patient_name, doctor_name)
            
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
    
    def _gemini_soap(self, conversation_text, patient_name, doctor_name, api_key):
        """Gemini AI による SOAP変換"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
以下の歯科医療会話をSOAP形式（主観的情報・客観的所見・評価・計画）に変換してください。

患者: {patient_name}
医師: {doctor_name}

会話内容:
{conversation_text}

以下のJSON形式で回答してください:
{{
  "subjective": "患者の主観的な症状・訴え",
  "objective": "医師の観察・検査所見",
  "assessment": "診断・評価",
  "plan": "治療計画・方針",
  "confidence": 0.0から1.0の信頼度
}}
"""
            
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            
            # Process log追加
            subjective_length = len(result.get('subjective', ''))
            objective_length = len(result.get('objective', ''))
            assessment_length = len(result.get('assessment', ''))
            plan_length = len(result.get('plan', ''))
            
            result["process_log"] = [
                "🤖 Gemini AI SOAP変換開始",
                f"📝 解析対象: {len(conversation_text.split())}行の歯科医療会話データ",
                "🧠 自然言語処理による医療記録構造化実行",
                f"📊 SOAP分類結果:",
                f"  - S (主観的情報): {subjective_length}文字",
                f"  - O (客観的所見): {objective_length}文字", 
                f"  - A (評価・診断): {assessment_length}文字",
                f"  - P (治療計画): {plan_length}文字",
                f"✅ Gemini AI SOAP変換完了（信頼度: {result.get('confidence', 0):.2f}）"
            ]
            result["method"] = "gemini_ai_medical_record_structuring"
            
            return result
            
        except Exception as e:
            print(f"Gemini SOAP API error: {e}")
            return self._fallback_soap(conversation_text, patient_name, doctor_name)
    
    def _fallback_soap(self, conversation_text, patient_name, doctor_name):
        """フォールバック SOAP変換"""
        lines = conversation_text.strip().split('\n')
        patient_lines = []
        doctor_lines = []
        
        for line in lines:
            if patient_name in line or '患者' in line:
                patient_lines.append(line.split(':', 1)[-1].strip())
            elif doctor_name in line or '医師' in line or 'Dr.' in line:
                doctor_lines.append(line.split(':', 1)[-1].strip())
        
        # 基本的なSOAP分類
        subjective = ' '.join(patient_lines[:2]) if patient_lines else "主観的症状の記録が不明"
        objective = ' '.join(doctor_lines[:2]) if doctor_lines else "客観的所見の記録が不明"
        assessment = "症状の評価・診断が必要"
        plan = "治療計画の策定が必要"
        
        return {
            "subjective": subjective,
            "objective": objective,
            "assessment": assessment,
            "plan": plan,
            "confidence": 0.6,
            "process_log": [
                "📋 フォールバックSOAP変換実行",
                f"✅ 変換完了: S={len(subjective)}文字, O={len(objective)}文字"
            ],
            "method": "pattern_based_soap_conversion"
        }
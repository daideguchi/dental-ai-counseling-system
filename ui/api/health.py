from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # 環境変数チェック
            gemini_key = os.environ.get('GEMINI_API_KEY')
            gemini_status = {
                "available": gemini_key is not None,
                "key_length": len(gemini_key) if gemini_key else 0,
                "key_prefix": gemini_key[:10] + "..." if gemini_key else None
            }
            
            # Gemini API接続テスト
            if gemini_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    # 簡単なテスト
                    test_response = model.generate_content("test")
                    gemini_status["connection_test"] = "success"
                    gemini_status["model"] = "gemini-1.5-flash"
                except Exception as e:
                    gemini_status["connection_test"] = f"failed: {str(e)}"
            else:
                gemini_status["connection_test"] = "no_api_key"
            
            response = {
                "status": "healthy",
                "service": "dental_ai_vercel",
                "version": "1.0.0", 
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "endpoints": [
                    "/api/health",
                    "/api/identify", 
                    "/api/soap",
                    "/api/quality"
                ],
                "platform": "vercel_serverless",
                "gemini_ai": gemini_status,
                "debug_info": {
                    "env_vars_count": len(os.environ),
                    "python_path": os.getcwd()
                }
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "status": "error",
                "service": "dental_ai_vercel",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
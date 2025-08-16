from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
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
            "platform": "vercel_serverless"
        }
        
        self.wfile.write(json.dumps(response).encode())
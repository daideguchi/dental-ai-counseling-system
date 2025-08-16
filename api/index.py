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
            "message": "Dental AI API is working",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        self.wfile.write(json.dumps(response).encode())
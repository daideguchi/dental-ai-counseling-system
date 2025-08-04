#!/usr/bin/env python3
"""
UIデモ用のシンプルなWebサーバー
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

def start_demo_server():
    """デモ用Webサーバーを起動"""
    
    # UIディレクトリに移動
    ui_dir = Path(__file__).parent
    os.chdir(ui_dir)
    
    PORT = 8001
    
    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # CORS対応
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
            print(f"🌐 UIデモサーバー起動中...")
            print(f"📱 ブラウザで以下のURLにアクセスしてください:")
            print(f"   http://localhost:{PORT}")
            print(f"🛑 停止するには Ctrl+C を押してください")
            
            # ブラウザを自動で開く
            webbrowser.open(f'http://localhost:{PORT}')
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n✅ サーバーを停止しました")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ ポート {PORT} は既に使用されています")
            print(f"💡 別のポートを試すか、既存のプロセスを終了してください")
        else:
            print(f"❌ サーバー起動エラー: {e}")

if __name__ == "__main__":
    start_demo_server()
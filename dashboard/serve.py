#!/usr/bin/env python3
"""
Serveur simple pour servir le dashboard WakeDock
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

class WakeDockHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent / '.svelte-kit' / 'output' / 'client'), **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
    
    def do_GET(self):
        # Pour les routes SPA, servir index.html
        if not self.path.startswith('/_app/') and not os.path.isfile(self.translate_path(self.path)):
            self.path = '/index.html'
        super().do_GET()

def main():
    port = int(os.environ.get('PORT', 3000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    with socketserver.TCPServer((host, port), WakeDockHandler) as httpd:
        print(f"🚀 Dashboard WakeDock disponible sur:")
        print(f"   - Local:   http://localhost:{port}")
        print(f"   - Network: http://{host}:{port}")
        print(f"\n🔗 API Backend sur http://localhost:8000")
        print(f"📚 Documentation API: http://localhost:8000/api/docs")
        print(f"\n👤 Compte de test: admin / admin123")
        print(f"\n⏹️  Arrêter avec Ctrl+C")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du serveur...")

if __name__ == "__main__":
    main()

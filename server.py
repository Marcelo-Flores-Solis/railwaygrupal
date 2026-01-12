import http.server
import socketserver
import os
import sys

# 1. Leemos el puerto que Railway nos asigne dinámicamente
# Si Railway no nos da nada, usamos 8080 como respaldo
PORT = int(os.environ.get("PORT", 8080))

print(f"--- CONFIGURANDO PUERTO: {PORT} ---")

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"<h1>HOLA MUNDO!</h1><p>Conexion exitosa con Railway.</p>")

# 2. Configuración para evitar errores de "Puerto ocupado"
class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    try:
        # 3. Usamos '0.0.0.0' explícitamente. Es OBLIGATORIO en la nube.
        server = ReusableTCPServer(('0.0.0.0', PORT), Handler)
        print(f"✅ SERVIDOR ESCUCHANDO EN 0.0.0.0:{PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ ERROR FATAL: {e}")
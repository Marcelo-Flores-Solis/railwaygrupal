import http.server
import socketserver
import os

PORT = int(os.environ.get("PORT", 8080))

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        # CORRECCIÓN: Quitamos la 'b' del principio y usamos .encode()
        mensaje = "<h1>¡FUNCIONA!</h1><p>El servidor arranco bien.</p>"
        self.wfile.write(mensaje.encode('utf-8'))

if __name__ == '__main__':
    print(f"🚀 Iniciando en puerto {PORT}...")
    # '0.0.0.0' es obligatorio para que Railway escuche
    server = socketserver.TCPServer(('0.0.0.0', PORT), Handler)
    server.serve_forever()
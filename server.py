import http.server
import socketserver
import os

PORT = int(os.environ.get("PORT", 8080))
ADDRESS = '0.0.0.0'

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>HOLA MUNDO</h1>")

if __name__ == '__main__':
    print(f"--- INICIANDO EN {PORT} ---")
    server = socketserver.TCPServer((ADDRESS, PORT), Handler)
    server.serve_forever()
import http.server
import socketserver
import os

PORT = int(os.environ.get("PORT", 8000))

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>Hola! El servidor funciona. El error era la base de datos.</h1>")

if __name__ == '__main__':
    print(f"Iniciando en puerto {PORT}")
    server = socketserver.TCPServer(('', PORT), SimpleHandler)
    server.serve_forever()
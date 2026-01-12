import http.server
import socketserver
import os
import sys

# Forzamos el puerto 8080 si no llega nada, pero intentamos leer la variable
RAW_PORT = os.environ.get("PORT")
PORT = int(RAW_PORT) if RAW_PORT else 8080

print(f"DEBUG: Variable PORT detectada = {RAW_PORT}")
print(f"DEBUG: Puerto final a usar = {PORT}")

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"¡CONEXIÓN RECIBIDA! Alguien entró a: {self.path}")
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"<h1>HOLA MUNDO</h1><p>Conexion exitosa.</p>")

if __name__ == '__main__':
    print(f"--- INICIANDO SERVIDOR EN 0.0.0.0:{PORT} ---")
    try:
        # Usamos string vacío '' que equivale a 0.0.0.0 (todas las interfaces)
        server = socketserver.TCPServer(('', PORT), Handler)
        print("--- SERVIDOR ESCUCHANDO. SI VES ESTO, PYTHON ESTA VIVO ---")
        server.serve_forever()
    except Exception as e:
        print(f"FATAL ERROR AL INICIAR: {e}")
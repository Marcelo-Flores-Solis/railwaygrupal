import http.server
import socketserver
import os
import mimetypes
import json
from urllib.parse import parse_qs, urlparse

# --- IMPORTACIÓN SEGURA DE DB ---
try:
    import db_manager
    print("✅ DB Manager cargado correctamente.")
except Exception as e:
    print(f"⚠️ ERROR: No se pudo cargar db_manager: {e}")
    db_manager = None

# --- CONFIGURACIÓN ---
PORT = int(os.environ.get("PORT", 8080))

# Rutas absolutas para evitar errores de carpeta
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(ROOT_DIR, 'templates')
ASSET_DIR = os.path.join(ROOT_DIR, 'assets')

class BibliotecaHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        if path == '': path = '/'

        rutas_html = {
            '/': 'index.html',
            '/catalogo': 'catalogo.html',
            '/login': 'login.html',
            '/registro': 'register.html',
            '/usuario': 'user.html',
            '/detalle': 'element.html'
        }

        try:
            # 1. API (Datos JSON)
            if path.startswith('/api/'):
                self.manejar_api_get(path, parsed.query)
                return

            # 2. ASSETS (CSS, JS, IMG)
            if path.startswith('/assets/'):
                self.servir_statico(path)
                return

            # 3. PÁGINAS HTML
            if path in rutas_html:
                archivo = os.path.join(TEMPLATE_DIR, rutas_html[path])
                # Verificamos si existe antes de intentar abrirlo
                if os.path.exists(archivo):
                    self.servir_archivo(archivo, 'text/html')
                else:
                    print(f"❌ Error 404: No encuentro el archivo {archivo}")
                    self.send_error(404, "Archivo HTML no encontrado")
            else:
                self.send_error(404, "Pagina no encontrada")

        except Exception as e:
            print(f"🔥 Error en do_GET: {e}")
            self.send_error(500)

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            datos = json.loads(post_data.decode('utf-8'))

            if not db_manager:
                self.responder_json({"error": "Sin conexión a BD"}, 500)
                return

            if self.path == '/api/registro':
                if db_manager.guardar_usuario(datos['nombre'], datos['email'], datos['password']):
                    self.responder_json({"mensaje": "OK"}, 201)
                else:
                    self.send_error(400, "Error: Email duplicado")

            elif self.path == '/api/login':
                user = db_manager.verificar_usuario(datos['email'], datos['password'])
                if user: self.responder_json(user)
                else: self.send_error(401, "Credenciales incorrectas")

            elif self.path == '/api/prestar':
                if db_manager.prestar_libro(datos.get('id_libro'), datos.get('id_usuario')):
                    self.responder_json({"mensaje": "Prestado"})
                else:
                    self.send_error(400, "No se pudo prestar")

            elif self.path == '/api/devolver':
                if db_manager.devolver_libro(datos.get('id_libro'), datos.get('id_usuario')):
                    self.responder_json({"mensaje": "Devuelto"})
                else:
                    self.send_error(400, "Error devolución")
            
            else:
                self.send_error(404, "Ruta POST desconocida")

        except Exception as e:
            print(f"🔥 Error POST: {e}")
            self.send_error(500, str(e))

    # --- AUXILIARES ---
    def manejar_api_get(self, path, query):
        if not db_manager:
            self.responder_json([])
            return

        if path == '/api/libros':
            self.responder_json(db_manager.obtener_todos_los_libros())
        elif path == '/api/buscar':
            q = parse_qs(query).get('q', [''])[0]
            self.responder_json(db_manager.buscar_libros(q))
        elif path == '/api/libro':
            id_libro = parse_qs(query).get('id', [None])[0]
            libro = db_manager.obtener_libro_por_id(id_libro)
            if libro: self.responder_json(libro)
            else: self.send_error(404)

    def servir_statico(self, path):
        # Limpieza de ruta para seguridad
        ruta_relativa = path.lstrip('/')
        ruta_absoluta = os.path.join(ROOT_DIR, ruta_relativa)
        if os.path.exists(ruta_absoluta):
             self.servir_archivo(ruta_absoluta)
        else:
             print(f"❌ Asset perdido: {ruta_absoluta}")
             self.send_error(404)

    def servir_archivo(self, ruta, mime_force=None):
        try:
            mime = mime_force or mimetypes.guess_type(ruta)[0] or 'application/octet-stream'
            with open(ruta, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', mime)
                self.end_headers()
                self.wfile.write(f.read())
        except Exception as e:
            print(f"Error sirviendo {ruta}: {e}")

    def responder_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        # Usamos encode('utf-8') correctamente
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

if __name__ == '__main__':
    print(f"🚀 Iniciando servidor en puerto {PORT}...")
    # Escuchamos en 0.0.0.0 para que Railway conecte
    server = ThreadedHTTPServer(('0.0.0.0', PORT), BibliotecaHandler)
    server.serve_forever()
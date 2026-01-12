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
PORT = int(os.environ.get("PORT", 8000))
TEMPLATE_DIR = 'templates'
ASSET_DIR = 'assets'

class BibliotecaHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        print(f"📥 Petición recibida: {self.path}") # LOG NUEVO
        
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
            # 1. API
            if path.startswith('/api/'):
                print("   👉 Redirigiendo a API") # LOG NUEVO
                self.manejar_api_get(path, parsed.query)
                return

            # 2. ASSETS
            if path.startswith('/assets/'):
                print("   👉 Sirviendo asset") # LOG NUEVO
                self.servir_statico(path)
                return

            # 3. HTML
            if path in rutas_html:
                archivo = os.path.join(TEMPLATE_DIR, rutas_html[path])
                print(f"   👉 Intentando servir HTML: {archivo}") # LOG NUEVO
                
                if os.path.exists(archivo):
                    self.servir_archivo(archivo, 'text/html')
                else:
                    print(f"   ❌ ERROR: No encuentro el archivo {archivo}") # LOG NUEVO
                    self.send_error(404, f"Falta el archivo {rutas_html[path]} en templates/")
            else:
                print("   ❌ Ruta desconocida")
                self.send_error(404, "Pagina no encontrada")

        except Exception as e:
            print(f"🔥 CRASH en do_GET: {e}") # LOG NUEVO
            self.send_error(500, f"Error interno: {e}")

        try:
            # 1. API (Datos JSON para Javascript)
            if path.startswith('/api/'):
                self.manejar_api_get(path, parsed.query)
                return

            # 2. ARCHIVOS ESTÁTICOS (CSS, JS, Imágenes)
            if path.startswith('/assets/'):
                self.servir_statico(path)
                return

            # 3. PÁGINAS HTML
            if path in rutas_html:
                archivo = os.path.join(TEMPLATE_DIR, rutas_html[path])
                self.servir_archivo(archivo, 'text/html')
            else:
                self.send_error(404, "Pagina no encontrada")

        except Exception as e:
            print(f"Error GET: {e}")
            self.send_error(500)

    def do_POST(self):
        try:
            # Leer datos enviados
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            datos = json.loads(post_data.decode('utf-8'))

            if not db_manager:
                self.send_error(500, "Base de datos no conectada")
                return

            # Rutas POST
            if self.path == '/api/registro':
                if db_manager.guardar_usuario(datos['nombre'], datos['email'], datos['password']):
                    self.responder_json({"mensaje": "OK"}, 201)
                else:
                    self.send_error(400, "Error: Email duplicado")

            elif self.path == '/api/login':
                user = db_manager.verificar_usuario(datos['email'], datos['password'])
                if user: self.responder_json(user)
                else: self.send_error(401, "Credenciales invalidas")

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
                self.send_error(404, "API POST desconocida")

        except Exception as e:
            print(f"Error POST: {e}")
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

    def serving_statico(self, path):
        # Limpieza de ruta para seguridad básica
        clean_path = path.lstrip('/')
        if not clean_path.startswith('assets'):
            self.send_error(403)
            return
        self.servir_archivo(clean_path)

    def servir_statico(self, path):
        # Eliminar la barra inicial
        ruta_relativa = path.lstrip('/')
        self.servir_archivo(ruta_relativa)

    def servir_archivo(self, ruta, mime_force=None):
        if os.path.exists(ruta):
            mime = mime_force or mimetypes.guess_type(ruta)[0] or 'application/octet-stream'
            with open(ruta, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', mime)
                self.end_headers()
                self.wfile.write(f.read())
        else:
            self.send_error(404, f"Archivo no encontrado: {ruta}")

    def responder_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

if __name__ == '__main__':
    print(f"🚀 Iniciando servidor en puerto {PORT}...")
    server = ThreadedHTTPServer(('', PORT), BibliotecaHandler)
    server.serve_forever()
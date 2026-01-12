import http.server
import socketserver
import os
import mimetypes
import json
from urllib.parse import parse_qs, urlparse

# --- IMPORTACIÓN DE TU DB MANAGER ---
try:
    import db_manager as db
    print("✅ Base de datos cargada correctamente.")
except ImportError as e:
    print(f"⚠️ ERROR CRÍTICO: No se encontró db_manager.py: {e}")
    db = None

# CONFIGURACIÓN DEL PUERTO (Railway usa la variable PORT)
PORT = int(os.environ.get("PORT", 8000))

# Directorios de archivos estáticos
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(ROOT_DIR, 'public_html')
TEMPLATES_DIR = os.path.join(PUBLIC_DIR, 'templates')

class BibliotecaHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        """Maneja las peticiones de lectura (Ver páginas, obtener datos)"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path.rstrip('/')
        if path == '': path = '/'

        # Mapa de rutas amigables a archivos reales
        rutas_templates = {
            '/catalogo': 'catalogo.html',
            '/login': 'login.html',
            '/registro': 'register.html',
            '/usuario': 'user.html',
            '/detalle': 'element.html'
        }

        try:
            # --- API ENDPOINTS (Datos JSON) ---

            # 1. Obtener todos los libros
            if path == '/api/libros':
                if db:
                    self.responder_json(db.obtener_todos_los_libros())
                else:
                    self.send_error(500, "Error de conexión a BD")
                return

            # 2. Buscar libros (?q=termino)
            if path == '/api/buscar':
                query_params = parse_qs(parsed_path.query)
                termino = query_params.get('q', [''])[0]
                if db:
                    self.responder_json(db.buscar_libros(termino))
                return

            # 3. Obtener un solo libro (?id=1)
            if path == '/api/libro':
                query_params = parse_qs(parsed_path.query)
                id_libro = query_params.get('id', [None])[0]
                if db and id_libro:
                    libro = db.obtener_libro_por_id(id_libro)
                    if libro: self.responder_json(libro)
                    else: self.send_error(404, "Libro no encontrado")
                return

            # --- SERVIR ARCHIVOS (HTML, CSS, IMÁGENES) ---
            if path == '/':
                self.servir_archivo(os.path.join(ROOT_DIR, 'index.html'))
            elif path.startswith('/assets/'):
                # Sirve CSS, JS e imágenes
                self.servir_archivo(os.path.join(PUBLIC_DIR, path.lstrip('/')))
            elif path in rutas_templates:
                self.servir_archivo(os.path.join(TEMPLATES_DIR, rutas_templates[path]))
            else:
                self.send_error(404, "Página no encontrada")

        except Exception as e:
            print(f"Error GET: {e}")
            self.send_error(500)

    def do_POST(self):
        """Maneja el envío de datos (Login, Registro, Préstamos)"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            datos = json.loads(post_data.decode('utf-8'))

            # 1. Registro de usuario
            if self.path == '/api/registro':
                exito = db.guardar_usuario(datos['nombre'], datos['email'], datos['password'])
                if exito: self.responder_json({"mensaje": "Usuario creado"}, 201)
                else: self.send_error(400, "Error: El email ya existe o datos inválidos")
            
            # 2. Login
            elif self.path == '/api/login':
                usuario = db.verificar_usuario(datos['email'], datos['password'])
                if usuario:
                    # Devolvemos ID y nombre para guardarlo en el navegador (localStorage)
                    self.responder_json({
                        "id": usuario['id'], 
                        "nombre": usuario['nombre'], 
                        "email": usuario['email']
                    })
                else:
                    self.send_error(401, "Credenciales incorrectas")

            # 3. Prestar Libro
            elif self.path == '/api/prestar':
                id_libro = datos.get('id_libro')
                id_usuario = datos.get('id_usuario') # ¡Importante! Necesitamos saber quién
                
                if db.prestar_libro(id_libro, id_usuario):
                    self.responder_json({"mensaje": "Libro prestado con éxito"})
                else:
                    self.send_error(400, "No se pudo prestar (No disponible o error)")

            # 4. Devolver Libro (Nueva función)
            elif self.path == '/api/devolver':
                id_libro = datos.get('id_libro')
                id_usuario = datos.get('id_usuario')

                if db.devolver_libro(id_libro, id_usuario):
                    self.responder_json({"mensaje": "Libro devuelto con éxito"})
                else:
                    self.send_error(400, "Error al devolver el libro")
            
            else:
                self.send_error(404, "Ruta POST desconocida")

        except Exception as e:
            print(f"Error POST: {e}")
            self.send_error(500, f"Error interno: {e}")

    # --- FUNCIONES AUXILIARES ---

    def responder_json(self, data, status=200):
        """Envía una respuesta en formato JSON al navegador"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        # CORS headers (Opcional, ayuda si tienes problemas con fetch local)
        self.send_header('Access-Control-Allow-Origin', '*') 
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))

    def servir_archivo(self, ruta_archivo):
        """Lee un archivo del disco y lo envía al navegador"""
        if not os.path.exists(ruta_archivo):
            self.send_error(404, "Archivo no encontrado")
            return

        # Adivina el tipo de archivo (text/html, image/png, etc.)
        mime_type, _ = mimetypes.guess_type(ruta_archivo)
        if mime_type is None:
            mime_type = 'application/octet-stream'

        try:
            with open(ruta_archivo, 'rb') as f:
                contenido = f.read()
                self.send_response(200)
                self.send_header('Content-type', mime_type)
                self.end_headers()
                self.wfile.write(contenido)
        except Exception as e:
            print(f"Error sirviendo archivo {ruta_archivo}: {e}")
            self.send_error(500)

# --- INICIO DEL SERVIDOR ---
# Usamos ThreadingTCPServer para que si entran 2 personas a la vez, no se bloquee
class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

if __name__ == '__main__':
    print(f"🚀 Iniciando servidor en el puerto {PORT}...")
    server = ThreadedHTTPServer(('', PORT), BibliotecaHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    print("Servidor detenido.")
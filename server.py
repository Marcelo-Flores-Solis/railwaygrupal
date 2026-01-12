import http.server
import socketserver
import os
import mimetypes
import json
from urllib.parse import parse_qs, urlparse

# --- IMPORTACIÓN DE LA BASE DE DATOS (MODO SEGURO) ---
try:
    import db_manager as db
    print("✅ Base de datos cargada correctamente.")
except Exception as e:
    # Usamos 'Exception' para capturar cualquier error (Sintaxis, Indentación, Librería faltante)
    print(f"⚠️ ERROR CRÍTICO: Falló la carga de db_manager.py. El servidor funcionará sin BD. Razón: {e}")
    db = None

# --- CONFIGURACIÓN ---
PORT = int(os.environ.get("PORT", 8000))

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(ROOT_DIR, 'public_html')
TEMPLATES_DIR = os.path.join(PUBLIC_DIR, 'templates')

class BibliotecaHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path.rstrip('/')
        if path == '': path = '/'

        rutas_templates = {
            '/catalogo': 'catalogo.html',
            '/login': 'login.html',
            '/registro': 'register.html',
            '/usuario': 'user.html',
            '/detalle': 'element.html'
        }

        try:
            # --- API: OBTENER TODOS LOS LIBROS ---
            if path == '/api/libros':
                if db:
                    self.responder_json(db.obtener_todos_los_libros())
                else:
                    self.responder_json([], 200) # Devuelve lista vacía si no hay BD
                return

            # --- API: BUSCAR LIBROS ---
            if path == '/api/buscar':
                query_params = parse_qs(parsed_path.query)
                termino = query_params.get('q', [''])[0]
                if db:
                    self.responder_json(db.buscar_libros(termino))
                else:
                    self.responder_json([])
                return

            # --- API: OBTENER UN SOLO LIBRO ---
            if path == '/api/libro':
                query_params = parse_qs(parsed_path.query)
                id_libro = query_params.get('id', [None])[0]
                if db and id_libro:
                    libro = db.obtener_libro_por_id(id_libro)
                    if libro: self.responder_json(libro)
                    else: self.send_error(404, "Libro no encontrado")
                else:
                    self.send_error(500, "Base de datos no disponible")
                return

            # --- SERVIR ARCHIVOS ESTÁTICOS ---
            if path == '/':
                self.servir_archivo(os.path.join(ROOT_DIR, 'index.html'))
            elif path.startswith('/assets/'):
                self.servir_archivo(os.path.join(PUBLIC_DIR, path.lstrip('/')))
            elif path in rutas_templates:
                self.servir_archivo(os.path.join(TEMPLATES_DIR, rutas_templates[path]))
            else:
                self.send_error(404, "Pagina no encontrada")

        except Exception as e:
            print(f"Error GET: {e}")
            self.send_error(500)

    def do_POST(self):
        try:
            # Si no hay DB conectada, rechazamos cualquier intento de guardar datos
            if not db:
                self.send_error(500, "La base de datos no está conectada. Revisa los logs.")
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            datos = json.loads(post_data.decode('utf-8'))

            # --- REGISTRO ---
            if self.path == '/api/registro':
                exito = db.guardar_usuario(datos['nombre'], datos['email'], datos['password'])
                if exito: self.responder_json({"mensaje": "Usuario creado"}, 201)
                else: self.send_error(400, "Error: Email ya existe o datos inválidos")
            
            # --- LOGIN ---
            elif self.path == '/api/login':
                usuario = db.verificar_usuario(datos['email'], datos['password'])
                if usuario:
                    self.responder_json({
                        "id": usuario['id'], 
                        "nombre": usuario['nombre'], 
                        "email": usuario['email']
                    })
                else:
                    self.send_error(401, "Credenciales incorrectas")

            # --- PRESTAR LIBRO ---
            elif self.path == '/api/prestar':
                id_libro = datos.get('id_libro')
                id_usuario = datos.get('id_usuario')
                if db.prestar_libro(id_libro, id_usuario):
                    self.responder_json({"mensaje": "Libro prestado con éxito"})
                else:
                    self.send_error(400, "No se pudo prestar")

            # --- DEVOLVER LIBRO ---
            elif self.path == '/api/devolver':
                id_libro = datos.get('id_libro')
                id_usuario = datos.get('id_usuario')
                if db.devolver_libro(id_libro, id_usuario):
                    self.responder_json({"mensaje": "Libro devuelto con éxito"})
                else:
                    self.send_error(400, "Error al devolver")
            
            else:
                self.send_error(404, "Ruta POST desconocida")

        except Exception as e:
            print(f"Error POST: {e}")
            self.send_error(500, f"Error interno: {e}")

    # --- FUNCIONES AUXILIARES ---

    def responder_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*') 
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))

    def servir_archivo(self, ruta_archivo):
        if not os.path.exists(ruta_archivo):
            self.send_error(404, "Archivo no encontrado")
            return

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

# --- SERVIDOR MULTIHILO ---
class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

if __name__ == '__main__':
    print(f"🚀 Iniciando servidor en el puerto {PORT}...")
    # Escuchamos en '' (todas las interfaces) para que Railway lo detecte
    server = ThreadedHTTPServer(('', PORT), BibliotecaHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    print("Servidor detenido.")
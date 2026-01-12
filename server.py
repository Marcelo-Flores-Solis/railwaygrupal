import http.server
import socketserver
import os
import mimetypes
import json
from urllib.parse import parse_qs, urlparse

# Importamos el manager. Si está en la raíz, es así:
try:
    import db_manager
    print("✅ DB Manager cargado.")
except Exception as e:
    print(f"⚠️ Error cargando db_manager: {e}")
    db_manager = None

PORT = int(os.environ.get("PORT", 8000))
TEMPLATE_DIR = 'templates'
ASSET_DIR = 'assets'

class BibliotecaHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        # Limpieza del path
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        if path == '': path = '/'

        # Mapa de rutas a archivos HTML
        rutas = {
            '/': 'index.html',
            '/catalogo': 'catalogo.html',
            '/login': 'login.html',
            '/registro': 'register.html',
            '/usuario': 'user.html',
            '/detalle': 'element.html'
        }

        try:
            # 1. ARCHIVOS ESTÁTICOS (CSS, JS, IMG)
            # Igual que en tu otro código: si empieza por /assets/
            if path.startswith('/assets/'):
                self.servir_statico(path)
                return

            # 2. API: DATOS JSON (Para que funcione el Javascript)
            if path.startswith('/api/'):
                self.manejar_api_get(path, parsed.query)
                return

            # 3. PÁGINAS HTML
            if path in rutas:
                # Busca el archivo dentro de la carpeta templates
                archivo_path = os.path.join(TEMPLATE_DIR, rutas[path])
                self.servir_html(archivo_path)
            else:
                self.send_error(404, "Pagina no encontrada")

        except Exception as e:
            print(f"Error GET: {e}")
            self.send_error(500, f"Error interno: {e}")

    def do_POST(self):
        try:
            # Leer el JSON que envía el navegador
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            datos = json.loads(post_data.decode('utf-8'))

            # Rutas de la API (Login, Registro, Prestar)
            if self.path == '/api/registro':
                exito = db_manager.guardar_usuario(datos['nombre'], datos['email'], datos['password'])
                if exito: self.responder_json({"mensaje": "Usuario creado"}, 201)
                else: self.send_error(400, "Error: Email duplicado")

            elif self.path == '/api/login':
                usuario = db_manager.verificar_usuario(datos['email'], datos['password'])
                if usuario:
                    self.responder_json(usuario) # Devuelve id, nombre, email
                else:
                    self.send_error(401, "Credenciales incorrectas")

            elif self.path == '/api/prestar':
                if db_manager.prestar_libro(datos.get('id_libro'), datos.get('id_usuario')):
                    self.responder_json({"mensaje": "Prestamo exitoso"})
                else:
                    self.send_error(400, "No se pudo prestar")
            
            elif self.path == '/api/devolver':
                if db_manager.devolver_libro(datos.get('id_libro'), datos.get('id_usuario')):
                    self.responder_json({"mensaje": "Devolución exitosa"})
                else:
                    self.send_error(400, "No se pudo devolver")

            else:
                self.send_error(404, "Ruta POST no valida")

        except Exception as e:
            print(f"Error POST: {e}")
            self.send_error(500, str(e))

    # --- FUNCIONES AUXILIARES (Iguales a tu estilo) ---

    def servir_html(self, ruta_archivo):
        if os.path.exists(ruta_archivo):
            # Adivina el tipo (aunque sabemos que es HTML)
            mime_type, _ = mimetypes.guess_type(ruta_archivo)
            with open(ruta_archivo, 'rb') as f:
                content = f.read()
                self.send_response(200)
                self.send_header('Content-type', mime_type or 'text/html')
                self.end_headers()
                self.wfile.write(content)
        else:
            self.send_error(404, "Archivo HTML no encontrado")

    def servir_statico(self, path):
        # Quitamos la barra inicial para que os.path.join funcione bien
        ruta_relativa = path.lstrip('/') 
        # Si la ruta ya incluye 'assets/', úsala directo, si no, ajústala
        if not ruta_relativa.startswith(ASSET_DIR):
             ruta_relativa = os.path.join(ASSET_DIR, ruta_relativa)
        
        if os.path.exists(ruta_relativa):
            mime_type, _ = mimetypes.guess_type(ruta_relativa)
            with open(ruta_relativa, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', mime_type or 'application/octet-stream')
                self.end_headers()
                self.wfile.write(f.read())
        else:
            self.send_error(404, "Asset no encontrado")

    def manejar_api_get(self, path, query):
        if not db_manager:
            self.responder_json([], 500)
            return

        if path == '/api/libros':
            libros = db_manager.obtener_todos_los_libros()
            self.responder_json(libros)
        
        elif path == '/api/buscar':
            params = parse_qs(query)
            termino = params.get('q', [''])[0]
            libros = db_manager.buscar_libros(termino)
            self.responder_json(libros)

        elif path == '/api/libro':
            params = parse_qs(query)
            id_libro = params.get('id', [None])[0]
            libro = db_manager.obtener_libro_por_id(id_libro)
            if libro: self.responder_json(libro)
            else: self.send_error(404, "Libro no encontrado")

    def responder_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

if __name__ == '__main__':
    print(f"🚀 Servidor corriendo en puerto {PORT}")
    server = ThreadedHTTPServer(('', PORT), BibliotecaHandler)
    server.serve_forever()
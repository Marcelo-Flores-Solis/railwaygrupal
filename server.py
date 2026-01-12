import socketserver

import os

import mimetypes

import json

from urllib.parse import parse_qs, urlparse



# --- IMPORTACIÓN DIRECTA ---

try:

    import db_manager as db

    print("✅ Base de datos cargada correctamente.")

except ImportError as e:

    print(f"⚠️ ERROR CRÍTICO: {e}")

    db = None



# CONFIGURACIÓN

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

            # API: LISTA LIBROS

            if path == '/api/libros':

                if db:

                    self.responder_json(db.obtener_todos_los_libros())

                else:

                    self.send_error(500, "Sin BD")

                return



            # API: UN LIBRO

            if path == '/api/libro':

                query_params = parse_qs(parsed_path.query)

                id_libro = query_params.get('id', [None])[0]

                if db and id_libro:

                    libro = db.obtener_libro_por_id(id_libro)

                    if libro: self.responder_json(libro)

                    else: self.send_error(404)

                return



            # ARCHIVOS ESTÁTICOS Y TEMPLATES

            if path == '/':

                self.servir_archivo(os.path.join(ROOT_DIR, 'index.html'))

            elif path.startswith('/assets/'):

                self.servir_archivo(os.path.join(PUBLIC_DIR, path.lstrip('/')))

            elif path in rutas_templates:

                self.servir_archivo(os.path.join(TEMPLATES_DIR, rutas_templates[path]))

            else:

                self.send_error(404, "No encontrado")



        except Exception as e:

            print(f"Error GET: {e}")

            self.send_error(500)



    def do_POST(self):

        try:

            # 1. Leer el tamaño de los datos enviados

            content_length = int(self.headers['Content-Length'])

            post_data = self.rfile.read(content_length)

            datos = json.loads(post_data.decode('utf-8'))



            # 2. Rutas POST

            if self.path == '/api/registro':

                exito = db.guardar_usuario(datos['nombre'], datos['email'], datos['password'])

                if exito: self.responder_json({"mensaje": "Usuario creado"}, 201)

                else: self.send_error(400, "Error al crear usuario (quizas el email ya existe)")

           

            elif self.path == '/api/login':

                usuario = db.verificar_usuario(datos['email'], datos['password'])

                if usuario:

                    # Devolvemos los datos del usuario (sin la contraseña)

                    self.responder_json({"id": usuario['id'], "nombre": usuario['nombre'], "email": usuario['email']})

                else:

                    self.send_error(401, "Credenciales incorrectas")



            elif self.path == '/api/prestar':

                id_libro = datos.get('id_libro')

                if db.prestar_libro(id_libro):

                    self.responder_json({"mensaje": "Libro prestado con exito"})

                else:

                    self.send_error(500, "Error al prestar libro")

           

            else:

                self.send_error(404, "Ruta POST desconocida")



        except Exception as e:

            print(f"Error POST: {e}")

            self.send_error(500, f"Error interno: {e}")



    def responder_json(self, data, status=200):

        self.send_response(status)

        self.send_header('Content-type', 'application/json; charset=utf-8')

        self.end_headers()

        self.w        # Quitamos la barra inicial para que os.path.join funcione bien
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
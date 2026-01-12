import mysql.connector
from mysql.connector import Error

def crear_conexion():
    """Conecta a la base de datos de Railway"""
    try:
        connection = mysql.connector.connect(
            host='crossover.proxy.rlwy.net',           # TU HOST
            user='root',                               # TU USUARIO
            password='aRDrOAsJWIFemryAXrZuMVpcfqlIbhzL', # TU CONTRASEÑA
            port=39993,                                # TU PUERTO
            database='railway'                         # Nombre BD
        )
        return connection
    except Error as e:
        print(f"❌ Error al conectar a MySQL: {e}")
        return None

# --- LIBROS ---

def obtener_todos_los_libros():
    conn = crear_conexion()
    lista = []
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM libros")
            lista = cursor.fetchall()
        except Error as e:
            print(f"Error leyendo libros: {e}")
        finally:
            cursor.close()
            conn.close()
    return lista

def buscar_libros(termino):
    conn = crear_conexion()
    lista = []
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor(dictionary=True)
            # Busca coincidencias en titulo O autor
            query = "SELECT * FROM libros WHERE titulo LIKE %s OR autor LIKE %s"
            param = f"%{termino}%"
            cursor.execute(query, (param, param))
            lista = cursor.fetchall()
        except Error as e:
            print(f"Error buscando: {e}")
        finally:
            cursor.close()
            conn.close()
    return lista

def obtener_libro_por_id(id_libro):
    conn = crear_conexion()
    libro = None
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM libros WHERE id = %s", (id_libro,))
            libro = cursor.fetchone()
        except Error as e:
            print(f"Error obteniendo libro: {e}")
        finally:
            cursor.close()
            conn.close()
    return libro

# --- TRANSACCIONES (Préstamos) ---

def prestar_libro(id_libro, id_usuario):
    conn = crear_conexion()
    exito = False
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor()
            # 1. Verificar disponibilidad
            cursor.execute("SELECT disponible FROM libros WHERE id = %s", (id_libro,))
            res = cursor.fetchone()
            
            if res and res[0] == 1: # Si es 1 (True)
                # 2. Marcar como NO disponible
                cursor.execute("UPDATE libros SET disponible = 0 WHERE id = %s", (id_libro,))
                # 3. Registrar quién se lo llevó
                cursor.execute("INSERT INTO prestamos (usuario_id, libro_id) VALUES (%s, %s)", (id_usuario, id_libro))
                conn.commit()
                exito = True
        except Error as e:
            conn.rollback() # Deshacer cambios si falla
            print(f"Error prestando: {e}")
        finally:
            cursor.close()
            conn.close()
    return exito

def devolver_libro(id_libro, id_usuario):
    conn = crear_conexion()
    exito = False
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor()
            # 1. Marcar como disponible
            cursor.execute("UPDATE libros SET disponible = 1 WHERE id = %s", (id_libro,))
            # 2. Cerrar el préstamo (poner fecha de devolución)
            cursor.execute("UPDATE prestamos SET fecha_devolucion = NOW() WHERE libro_id = %s AND usuario_id = %s AND fecha_devolucion IS NULL", (id_libro, id_usuario))
            conn.commit()
            exito = True
        except Error as e:
            conn.rollback()
            print(f"Error devolviendo: {e}")
        finally:
            cursor.close()
            conn.close()
    return exito

# --- USUARIOS ---

def guardar_usuario(nombre, email, password):
    conn = crear_conexion()
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor()
            query = "INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)"
            cursor.execute(query, (nombre, email, password))
            conn.commit()
            return True
        except Error:
            return False # Probablemente el email ya existe
        finally:
            cursor.close()
            conn.close()
    return False

def verificar_usuario(email, password):
    conn = crear_conexion()
    usuario = None
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT id, nombre, email FROM usuarios WHERE email = %s AND password = %s"
            cursor.execute(query, (email, password))
            usuario = cursor.fetchone()
        except Error as e:
            print(f"Error login: {e}")
        finally:
            cursor.close()
            conn.close()
    return usuario
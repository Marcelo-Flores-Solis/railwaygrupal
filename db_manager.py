import mysql.connector
from mysql.connector import Error

def crear_conexion():
    """Conecta a la base de datos usando tus credenciales DIRECTAS"""
    try:
        connection = mysql.connector.connect(
            host='crossover.proxy.rlwy.net',         
            user='root',                             
            password='aRDrOAsJWIFemryAXrZuMVpcfqlIbhzL', 
            port=39993,                               
            database='railway'                        
        )
        return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

# --- GESTIÓN DE LIBROS ---

def obtener_todos_los_libros():
    conn = crear_conexion()
    lista = []
    if conn and conn.is_connected():
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM libros")
        lista = cursor.fetchall()
        cursor.close()
        conn.close()
    return lista

def buscar_libros(termino):
    conn = crear_conexion()
    lista = []
    if conn and conn.is_connected():
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM libros WHERE titulo LIKE %s OR autor LIKE %s"
        param = f"%{termino}%"
        cursor.execute(query, (param, param))
        lista = cursor.fetchall()
        cursor.close()
        conn.close()
    return lista

def obtener_libro_por_id(id_libro):
    conn = crear_conexion()
    libro = None
    if conn and conn.is_connected():
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM libros WHERE id = %s", (id_libro,))
        libro = cursor.fetchone()
        cursor.close()
        conn.close()
    return libro

# --- PRÉSTAMOS Y DEVOLUCIONES ---

def prestar_libro(id_libro, id_usuario):
    conn = crear_conexion()
    exito = False
    if conn and conn.is_connected():
        try:
            cursor = conn.cursor()
            # 1. Verificar si está disponible
            query_check = "SELECT disponible FROM libros WHERE id = %s"
            cursor.execute(query_check, (id_libro,))
            res = cursor.fetchone()
            
            if res and res[0] == 1:
                # 2. Marcar como prestado
                cursor.execute("UPDATE libros SET disponible = 0 WHERE id = %s", (id_libro,))
                # 3. Registrar el préstamo
                cursor.execute("INSERT INTO prestamos (usuario_id, libro_id) VALUES (%s, %s)", (id_usuario, id_libro))
                conn.commit()
                exito = True
        except Error as e:
            conn.rollback()
            print(f"Error prestando libro: {e}")
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
            # 2. Cerrar préstamo (poner fecha devolución)
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
            cursor.execute("INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)", (nombre, email, password))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Error as e:
            return False
    return False

def verificar_usuario(email, password):
    conn = crear_conexion()
    usuario = None
    if conn and conn.is_connected():
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s AND password = %s", (email, password))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
    return usuario
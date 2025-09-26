import mysql.connector
from mysql.connector import Error
import bdd.config as config

def get_usuarios_temporales():
    """
    Obtiene usuarios temporales desde la base de datos.
    Retorna una lista de diccionarios con los datos de usuarios temporales.
    """
    connection = None
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            port=config.DB_PORT
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # Query para obtener usuarios temporales sin NFC asignado
            query = """
                SELECT 
                    ua.ID_useratributes,
                    ua.name,
                    ua.surname,
                    ua.dni,
                    u.user_status as estado,
                    u.creation_date
                FROM UserAtributes ua
                INNER JOIN User u ON ua.ID_user = u.ID_user
                WHERE (ua.nfc_code IS NULL OR ua.nfc_code = '')
                ORDER BY u.creation_date DESC
            """
            
            cursor.execute(query)
            usuarios = cursor.fetchall()
            
            # Convertir estado a texto
            for usuario in usuarios:
                usuario['estado_texto'] = 'Pendiente' if usuario['estado'] == 1 else 'Confirmado'
                usuario['estado_clase'] = 'guest' if usuario['estado'] == 1 else 'confirmed'
            
            return usuarios
            
    except Error as e:
        print(f"Error al obtener usuarios temporales: {e}")
        return []
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def confirmar_usuario_temporal(id_useratributes):
    """
    Confirma un usuario temporal cambiando su estado.
    """
    connection = None
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            port=config.DB_PORT
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Actualizar el estado del usuario a confirmado
            query = """
                UPDATE User 
                SET user_status = 2 
                WHERE ID_user = (
                    SELECT ID_user FROM UserAtributes WHERE ID_useratributes = %s
                )
            """
            
            cursor.execute(query, (id_useratributes,))
            connection.commit()
            
            return cursor.rowcount > 0
            
    except Error as e:
        print(f"Error al confirmar usuario temporal: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def eliminar_usuario_temporal(id_useratributes):
    """
    Elimina un usuario temporal de la base de datos.
    Realiza un hard delete eliminando completamente el registro de User y UserAtributes,
    y cualquier registro relacionado en la tabla tracking.
    """
    connection = None
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            port=config.DB_PORT
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Primero obtener el ID_user para eliminar de User
            cursor.execute("SELECT ID_user FROM UserAtributes WHERE ID_useratributes = %s", (id_useratributes,))
            result = cursor.fetchone()
            
            if result:
                id_user = result[0]
                
                try:
                    # Primero eliminar registros relacionados en la tabla tracking
                    cursor.execute("DELETE FROM tracking WHERE ID_useratributes = %s", (id_useratributes,))
                    
                    # Luego eliminar de UserAtributes
                    cursor.execute("DELETE FROM UserAtributes WHERE ID_useratributes = %s", (id_useratributes,))
                    
                    # Finalmente eliminar de User
                    cursor.execute("DELETE FROM User WHERE ID_user = %s", (id_user,))
                    
                    connection.commit()
                    return True
                except Error as e:
                    # Si hay algún error, hacer rollback
                    connection.rollback()
                    print(f"Error al eliminar usuario temporal: {e}")
                    return False
            
            return False
            
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def verificar_usuario_existe(id_useratributes):
    """
    Verifica si un usuario temporal existe en la base de datos.
    """
    connection = None
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            port=config.DB_PORT
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            query = """
                SELECT COUNT(*) as count 
                FROM UserAtributes 
                WHERE ID_useratributes = %s
            """
            
            cursor.execute(query, (id_useratributes,))
            result = cursor.fetchone()
            
            return result[0] > 0
            
    except Error as e:
        print(f"Error al verificar usuario: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def actualizar_nfc_code(id_useratributes, nfc_code):
    """
    Actualiza el campo nfc_code para un usuario específico.
    """
    connection = None
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            port=config.DB_PORT
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            query = """
                UPDATE UserAtributes 
                SET nfc_code = %s 
                WHERE ID_useratributes = %s
            """
            
            cursor.execute(query, (nfc_code, id_useratributes))
            connection.commit()
            
            return cursor.rowcount > 0
            
    except Error as e:
        print(f"Error al actualizar NFC code: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

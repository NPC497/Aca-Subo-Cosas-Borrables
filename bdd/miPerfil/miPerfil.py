"""
Módulo para manejar la lógica de la información personal del usuario
Desaharcodea los valores actuales y obtiene datos reales de la base de datos
"""

from bdd.conexionBDD import get_connection
import mysql.connector
from funciones.encryption import encriptar_password, desencriptar_password
from datetime import datetime


def obtener_informacion_usuario_actual(user_id):
    """
    Obtiene la información personal del usuario actual desde la base de datos
    
    Args:
        user_id (int): ID del usuario actual
        
    Returns:
        dict: Diccionario con nombre, apellido y email del usuario
    """
    connection = get_connection()
    if connection is None:
        return {
            'nombre': 'Usuario',
            'apellido': 'No encontrado',
            'email': 'sin@email.com'
        }
    
    cursor = connection.cursor()
    
    query = """
    SELECT 
        ua.name,
        ua.surname,
        u.mail,
        u.profile_photo
    FROM User u
    JOIN UserAtributes ua ON u.ID_user = ua.ID_user
    WHERE u.ID_user = %s
    """
    
    try:
        cursor.execute(query, (user_id,))
        resultado = cursor.fetchone()
        
        if resultado:
            return {
                'nombre': resultado[0] or 'Usuario',
                'apellido': resultado[1] or 'Sin apellido',
                'email': resultado[2] or 'sin@email.com',
                'foto': resultado[3] or None
            }
        else:
            return {
                'nombre': 'Usuario',
                'apellido': 'No encontrado',
                'email': 'sin@email.com',
                'foto': None
            }
            
    except mysql.connector.Error as e:
        print(f"Error al obtener información del usuario: {e}")
        return {
            'nombre': 'Error',
            'apellido': 'Al cargar',
            'email': 'error@email.com',
            'foto': None
        }
    finally:
        cursor.close()
        connection.close()

def dar_de_baja_usuario(user_id, reason=None):
    """
    Desactiva la cuenta del usuario estableciendo user_status = 0.

    Args:
        user_id (int): ID del usuario
        reason (str|None): Motivo opcional de la baja (no persistido)

    Returns:
        bool: True si la operación fue exitosa
    """
    connection = get_connection()
    if connection is None:
        return False
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE User SET user_status = 0 WHERE ID_user = %s", (user_id,))
        connection.commit()
        return True
    except mysql.connector.Error as e:
        print(f"Error al dar de baja usuario: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()

def obtener_informacion_cuenta(user_id):
    """
    Obtiene información de cuenta para el sidebar de Mi Perfil:
     - miembro_desde (fecha de creación)
     - ultimo_acceso (última actividad)
     - ingresos_realizados (cantidad de actividades)
     - estado (activo/inactivo)
    """
    connection = get_connection()
    if connection is None:
        return {
            'miembro_desde': 'N/D',
            'ultimo_acceso': 'N/D',
            'ingresos_realizados': 0,
            'estado': 'N/D'
        }
    cursor = connection.cursor()
    try:
        # 1) Datos de User
        cursor.execute("SELECT creation_date, user_status FROM User WHERE ID_user = %s", (user_id,))
        row = cursor.fetchone()
        creation_date = row[0] if row else None
        user_status = row[1] if row else None

        # 2) Último acceso y cantidad de ingresos desde Activity por el usuario
        #   Activity se liga por UserAtributes
        cursor.execute(
            """
            SELECT MAX(a.activity_datetime) AS ultimo, COUNT(*) AS total
            FROM Activity a
            INNER JOIN UserAtributes ua ON ua.ID_useratributes = a.ID_useratributes
            WHERE ua.ID_user = %s
              AND a.activity_details LIKE 'Acceso concedido%'
            """,
            (user_id,)
        )
        row2 = cursor.fetchone()
        ultimo = row2[0] if row2 else None
        total = int(row2[1]) if row2 and row2[1] is not None else 0

        # Formatear fechas a dd/mm/yyyy (sin hora)
        def fmt(dt):
            try:
                if isinstance(dt, datetime):
                    return dt.strftime('%d/%m/%Y')
                elif dt:
                    # MySQL devuelve datetime como datetime ya; fallback por si llega como str
                    return str(dt)
            except Exception:
                return str(dt) if dt else 'N/D'
            return 'N/D'

        miembro_desde = fmt(creation_date) if creation_date else 'N/D'
        ultimo_acceso = fmt(ultimo) if ultimo else 'Sin registros'
        estado = 'Activo' if user_status else 'Inactivo' if user_status is not None else 'N/D'

        return {
            'miembro_desde': miembro_desde,
            'ultimo_acceso': ultimo_acceso,
            'ingresos_realizados': total,
            'estado': estado,
        }
    except mysql.connector.Error as e:
        print(f"Error al obtener información de cuenta: {e}")
        return {
            'miembro_desde': 'N/D',
            'ultimo_acceso': 'N/D',
            'ingresos_realizados': 0,
            'estado': 'N/D'
        }
    finally:
        cursor.close()
        connection.close()

def actualizar_password_usuario(user_id, current_password, new_password):
    """
    Valida la contraseña actual y actualiza a una nueva contraseña
    
    Args:
        user_id (int): ID del usuario
        current_password (str): Contraseña actual provista por el usuario
        new_password (str): Nueva contraseña a establecer
    
    Returns:
        tuple[bool, str]: (exito, mensaje)
    """
    connection = get_connection()
    if connection is None:
        return False, "Error de conexión a la base de datos"
    cursor = connection.cursor()
    try:
        # Obtener password actual encriptada
        cursor.execute("SELECT password FROM User WHERE ID_user = %s", (user_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Usuario no encontrado"
        encrypted_pwd = row[0]
        stored_plain = desencriptar_password(encrypted_pwd) if encrypted_pwd else None
        if stored_plain != current_password:
            return False, "La contraseña actual no es correcta"
        # Encriptar nueva contraseña y actualizar
        new_encrypted = encriptar_password(new_password)
        cursor.execute("UPDATE User SET password = %s WHERE ID_user = %s", (new_encrypted, user_id))
        connection.commit()
        return True, "Contraseña actualizada correctamente"
    except mysql.connector.Error as e:
        print(f"Error al actualizar contraseña: {e}")
        connection.rollback()
        return False, "Error al actualizar la contraseña"
    finally:
        cursor.close()
        connection.close()

def actualizar_informacion_usuario(user_id, nombre, apellido, email):
    """
    Actualiza la información personal del usuario en la base de datos
    
    Args:
        user_id (int): ID del usuario
        nombre (str): Nuevo nombre
        apellido (str): Nuevo apellido
        email (str): Nuevo email
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    
    # Actualizar tanto UserAtributes como User
    try:
        # Actualizar UserAtributes
        query_atributes = """
        UPDATE UserAtributes 
        SET name = %s, surname = %s
        WHERE ID_user = %s
        """
        cursor.execute(query_atributes, (nombre, apellido, user_id))
        
        # Actualizar email en User
        query_user = """
        UPDATE User 
        SET mail = %s
        WHERE ID_user = %s
        """
        cursor.execute(query_user, (email, user_id))
        
        connection.commit()
        return True
        
    except mysql.connector.Error as e:
        print(f"Error al actualizar información del usuario: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def obtener_password_actual(user_id):
    """
    Obtiene la contraseña hasheada del usuario (solo para verificación)
    
    Args:
        user_id (int): ID del usuario
        
    Returns:
        str: Contraseña hasheada o None si no existe
    """
    connection = get_connection()
    if connection is None:
        return None
    
    cursor = connection.cursor()
    
    query = "SELECT password FROM User WHERE ID_user = %s"
    
    try:
        cursor.execute(query, (user_id,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None
        
    except mysql.connector.Error as e:
        print(f"Error al obtener contraseña: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def actualizar_foto_usuario(user_id, relative_path_or_null):
    """
    Actualiza la ruta de la foto de perfil del usuario.

    Args:
        user_id (int): ID del usuario
        relative_path_or_null (str|None): Ruta relativa bajo /static (por ej. 'img/users/123.jpg') o None para eliminar

    Returns:
        bool: True si la actualización fue exitosa
    """
    connection = get_connection()
    if connection is None:
        return False
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE User SET profile_photo = %s WHERE ID_user = %s",
            (relative_path_or_null, user_id)
        )
        connection.commit()
        return True
    except mysql.connector.Error as e:
        print(f"Error al actualizar foto de usuario: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()

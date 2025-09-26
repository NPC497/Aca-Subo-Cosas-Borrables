import mysql.connector
from mysql.connector import Error
from bdd.conexionBDD import get_connection
from datetime import datetime

def obtener_todos_los_permisos():
    """
    Obtiene todos los permisos de la base de datos con toda la información necesaria
    para mostrar en la tabla de permisos.
    
    Retorna:
        Lista de diccionarios con los permisos
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        if connection is None:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # Obtener el ID del administrador actual (quien está viendo la página)
        id_admin_actual = obtener_id_admin_actual()
        
        # Listar permisos efectivos combinando:
        # 1) Heredados por rol (roledoorpermit)
        # 2) Directos por usuario (userdoorpermit)
        query = """
        SELECT 
            CAST(rdp.ID_roledoorpermit AS CHAR) AS id_permiso,
            1 AS estado,
            NOW() AS fecha_permiso,
            'permanente' AS tiempo_permiso,
            d.door_name AS nombre_puerta,
            ua_admin.name AS nombre_admin,
            ua_admin.surname AS apellido_admin,
            ua_user.name AS nombre_usuario,
            ua_user.surname AS apellido_usuario,
            ua_user.dni AS dni_usuario
        FROM UserAtributes ua_user
        INNER JOIN roledoorpermit rdp ON ua_user.ID_role = rdp.ID_role
        INNER JOIN Door d ON d.ID_door = rdp.ID_door
        LEFT JOIN UserAtributes ua_admin ON ua_admin.ID_user = %s
        
        UNION ALL
        
        SELECT 
            CONCAT('U-', udp.ID_user, '-', udp.ID_door) AS id_permiso,
            1 AS estado,
            udp.created_at AS fecha_permiso,
            CASE 
                WHEN udp.expiration_time IS NULL THEN 'Permanente'
                ELSE CONCAT(TIMESTAMPDIFF(MINUTE, udp.created_at, udp.expiration_time), ' min')
            END AS tiempo_permiso,
            d2.door_name AS nombre_puerta,
            ua_admin2.name AS nombre_admin,
            ua_admin2.surname AS apellido_admin,
            ua_user2.name AS nombre_usuario,
            ua_user2.surname AS apellido_usuario,
            ua_user2.dni AS dni_usuario
        FROM userdoorpermit udp
        INNER JOIN UserAtributes ua_user2 ON ua_user2.ID_user = udp.ID_user
        INNER JOIN Door d2 ON d2.ID_door = udp.ID_door
        LEFT JOIN UserAtributes ua_admin2 ON ua_admin2.ID_user = %s
        
        ORDER BY nombre_usuario, nombre_puerta
        """
        
        cursor.execute(query, (id_admin_actual, id_admin_actual))
        permisos = cursor.fetchall()
        
        # Formatear los datos para la vista
        for permiso in permisos:
            permiso['estado_texto'] = 'Activa' if permiso['estado'] == 1 else 'Inactiva'
            permiso['administrador'] = f"{permiso['nombre_admin']} {permiso['apellido_admin']}"
            permiso['usuario'] = f"{permiso['nombre_usuario']} {permiso['apellido_usuario']}"
            permiso['fecha_formateada'] = permiso['fecha_permiso'].strftime('%Y-%m-%d') if hasattr(permiso['fecha_permiso'], 'strftime') else str(permiso['fecha_permiso'])[:10]
            permiso['tiempo_texto'] = permiso['tiempo_permiso']
        
        return permisos
        
    except Error as e:
        print(f"Error al obtener permisos: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def obtener_permisos_por_usuario(id_usuario):
    """
    Obtiene todos los permisos de un usuario específico
    
    Args:
        id_usuario: ID del usuario
        
    Retorna:
        Lista de diccionarios con los permisos del usuario
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        if connection is None:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # Obtener el ID del administrador actual (quien está viendo la página)
        id_admin_actual = obtener_id_admin_actual()
        
        # Permisos efectivos por usuario basados en su rol
        query = """
        SELECT 
            rdp.ID_roledoorpermit AS id_permiso,
            1 AS estado,
            NOW() AS fecha_permiso,
            'permanente' AS tiempo_permiso,
            d.door_name AS nombre_puerta,
            ua_admin.name AS nombre_admin,
            ua_admin.surname AS apellido_admin,
            ua_user.name AS nombre_usuario,
            ua_user.surname AS apellido_usuario
        FROM UserAtributes ua_user
        INNER JOIN roledoorpermit rdp ON ua_user.ID_role = rdp.ID_role
        INNER JOIN Door d ON d.ID_door = rdp.ID_door
        INNER JOIN UserAtributes ua_admin ON ua_admin.ID_user = %s
        WHERE ua_user.ID_user = %s
        ORDER BY d.door_name
        """
        
        cursor.execute(query, (id_admin_actual, id_usuario))
        permisos = cursor.fetchall()
        
        # Formatear los datos
        for permiso in permisos:
            permiso['estado_texto'] = 'Activa' if permiso['estado'] == 1 else 'Inactiva'
            permiso['administrador'] = f"{permiso['nombre_admin']} {permiso['apellido_admin']}"
            permiso['usuario'] = f"{permiso['nombre_usuario']} {permiso['apellido_usuario']}"
            permiso['fecha_formateada'] = permiso['fecha_permiso'].strftime('%Y-%m-%d')
            permiso['tiempo_texto'] = permiso['tiempo_permiso']
        
        return permisos
        
    except Error as e:
        print(f"Error al obtener permisos por usuario: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def crear_permiso(id_user, permit_status=1):
    """
    Obsoleto: antes creaba registros en Permit. Ahora no hace nada porque Permit está deprecada.
    Se mantiene por compatibilidad y retorna True.
    """
    return True

def actualizar_estado_permiso(id_permit, nuevo_estado):
    """
    Obsoleto: ya no hay estado en Permit. Se mantiene por compatibilidad.
    """
    return True

def eliminar_permiso(id_permit):
    """
    Obsoleto: ya no se eliminan permisos de la tabla Permit. Se mantiene por compatibilidad.
    """
    return True

def obtener_puertas_disponibles():
    """
    Obtiene todas las puertas disponibles para asignar permisos
    
    Retorna:
        Lista de diccionarios con las puertas
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        if connection is None:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT ID_door as id_puerta, door_name as nombre_puerta FROM Door WHERE door_isOpen = 1"
        cursor.execute(query)
        puertas = cursor.fetchall()
        
        return puertas
        
    except Error as e:
        print(f"Error al obtener puertas: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def obtener_usuarios_para_permisos():
    """
    Obtiene todos los usuarios que pueden recibir permisos
    
    Retorna:
        Lista de diccionarios con los usuarios
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        if connection is None:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT ua.ID_useratributes as id_useratributes, ua.ID_user as id_user, ua.name as nombre, ua.surname as apellido, ua.dni
        FROM UserAtributes ua
        INNER JOIN User u ON ua.ID_user = u.ID_user
        WHERE u.user_status = 1
        ORDER BY ua.name, ua.surname
        """
        
        cursor.execute(query)
        usuarios = cursor.fetchall()
        
        return usuarios
        
    except Error as e:
        print(f"Error al obtener usuarios: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def buscar_usuario_por_dni(dni):
    """
    Busca un usuario específico por su DNI
    
    Args:
        dni: DNI del usuario a buscar
        
    Retorna:
        Diccionario con los datos del usuario o None si no se encuentra
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        if connection is None:
            return None
        
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT ua.ID_useratributes as id_useratributes, ua.ID_user as id_user, ua.name as nombre, ua.surname as apellido, ua.dni
        FROM UserAtributes ua
        INNER JOIN User u ON ua.ID_user = u.ID_user
        WHERE ua.dni = %s AND u.user_status = 1
        """
        
        cursor.execute(query, (dni,))
        usuario = cursor.fetchone()
        
        return usuario
        
    except Error as e:
        print(f"Error al buscar usuario por DNI: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def obtener_todas_las_puertas():
    """
    Obtiene todas las puertas disponibles en el sistema
    
    Retorna:
        Lista de diccionarios con las puertas
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        if connection is None:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT ID_door as id_puerta, door_name as nombre_puerta FROM Door ORDER BY door_name"
        cursor.execute(query)
        puertas = cursor.fetchall()
        
        return puertas
        
    except Error as e:
        print(f"Error al obtener todas las puertas: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def crear_permiso_completo(id_user, id_puerta, tiempo_minutos, id_admin):
    """
    Crea un nuevo permiso completo en la base de datos con puerta y tiempo específicos
    
    Args:
        id_user: ID del usuario que recibe el permiso
        id_puerta: ID de la puerta para la cual se otorga el permiso
        tiempo_minutos: Tiempo en minutos del permiso (0 = permanente)
        id_admin: ID del administrador que otorga el permiso
        
    Retorna:
        True si se creó exitosamente, False en caso contrario
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        if connection is None:
            return False
        
        cursor = connection.cursor()

        # Validaciones previas para evitar errores de FK
        # Verificar existencia de la puerta
        cursor.execute("SELECT 1 FROM Door WHERE ID_door = %s", (id_puerta,))
        door_exists = cursor.fetchone()
        if not door_exists:
            raise ValueError(f"La puerta con ID {id_puerta} no existe")

        # Verificar existencia del usuario
        cursor.execute("SELECT 1 FROM User WHERE ID_user = %s", (id_user,))
        user_exists = cursor.fetchone()
        if not user_exists:
            raise ValueError(f"El usuario con ID {id_user} no existe")
        
        # Calculate expiration time based on tiempo_minutos
        if tiempo_minutos > 0:
            # Time-limited permission
            expiration_time = "DATE_ADD(DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i'), INTERVAL %s MINUTE)"
            expiration_value = tiempo_minutos
        else:
            # Permanent permission
            expiration_time = "NULL"
            expiration_value = None
        
        # Updated query to include expiration fields
        if expiration_value is not None:
            query_door_permit = f"""
            INSERT INTO userdoorpermit (ID_user, ID_door, created_at, expiration_time, granted_by)
            VALUES (%s, %s, DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i'), {expiration_time}, %s)
            ON DUPLICATE KEY UPDATE 
                expiration_time = VALUES(expiration_time),
                granted_by = VALUES(granted_by),
                created_at = DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i')
            """
            cursor.execute(query_door_permit, (id_user, id_puerta, expiration_value, id_admin))
        else:
            query_door_permit = f"""
            INSERT INTO userdoorpermit (ID_user, ID_door, created_at, expiration_time, granted_by)
            VALUES (%s, %s, DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i'), {expiration_time}, %s)
            ON DUPLICATE KEY UPDATE 
                expiration_time = VALUES(expiration_time),
                granted_by = VALUES(granted_by),
                created_at = DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i')
            """
            cursor.execute(query_door_permit, (id_user, id_puerta, id_admin))
        
        # Updated activity logging to include expiration info
        if tiempo_minutos > 0:
            activity_detail = f"Permiso temporal otorgado por admin - Duración: {tiempo_minutos} minutos"
        else:
            activity_detail = "Permiso permanente otorgado por admin"
            
        query_activity = """
        INSERT INTO Activity (ID_useratributes, ID_door, activity_details)
        SELECT ua.ID_useratributes, %s, CONCAT(%s, ' (', admin_ua.name, ' ', admin_ua.surname, ')')
        FROM UserAtributes ua
        CROSS JOIN UserAtributes admin_ua
        WHERE ua.ID_user = %s AND admin_ua.ID_user = %s
        """
        
        cursor.execute(query_activity, (id_puerta, activity_detail, id_user, id_admin))
        
        connection.commit()
        return True
        
    except Error as e:
        print(f"Error al crear permiso completo: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def buscar_usuarios_por_dni_like(dni_parcial):
    """
    Busca usuarios cuyo DNI contenga los dígitos especificados (autocompletado)
    
    Args:
        dni_parcial: Parte del DNI a buscar
        
    Retorna:
        Lista de diccionarios con los usuarios que coinciden
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        if connection is None:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT ua.ID_useratributes as id_useratributes, ua.ID_user as id_user, 
               ua.name as nombre, ua.surname as apellido, ua.dni
        FROM UserAtributes ua
        INNER JOIN User u ON ua.ID_user = u.ID_user
        WHERE ua.dni LIKE %s AND u.user_status = 1
        ORDER BY ua.dni, ua.name, ua.surname
        LIMIT 10
        """
        
        # Usar LIKE con wildcards para buscar DNIs que contengan la cadena
        search_pattern = f"%{dni_parcial}%"
        cursor.execute(query, (search_pattern,))
        usuarios = cursor.fetchall()
        
        return usuarios
        
    except Error as e:
        print(f"Error al buscar usuarios por DNI (LIKE): {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def buscar_usuarios_por_campo(termino_busqueda):
    """
    Busca usuarios que coincidan con el término de búsqueda en DNI, nombre, apellido o email
    
    Args:
        termino_busqueda: Término de búsqueda a buscar en los campos del usuario
        
    Retorna:
        Lista de diccionarios con los usuarios que coinciden
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        if connection is None:
            return []
            
        cursor = connection.cursor(dictionary=True)
        
        # Preparamos el término de búsqueda para LIKE
        busqueda = f"%{termino_busqueda}%"
        
        query = """
            SELECT 
                u.ID_user as id_user,
                ua.name as nombre,
                ua.surname as apellido,
                ua.dni as dni,
                u.mail as email
            FROM User u
            INNER JOIN UserAtributes ua ON u.ID_user = ua.ID_user
            WHERE ua.dni LIKE %s
               OR ua.name LIKE %s
               OR ua.surname LIKE %s
               OR u.mail LIKE %s
            LIMIT 50
        """
        
        cursor.execute(query, (busqueda, busqueda, busqueda, busqueda))
        return cursor.fetchall()
        
    except Exception as e:
        print(f"Error al buscar usuarios por campo: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def obtener_id_admin_actual():
    """
    Obtiene el ID del administrador actual desde la sesión
    
    Retorna:
        ID del administrador o 1 por defecto
    """
    try:
        from flask import session
        user_id = session.get('user_id')
        if user_id:
            return user_id
        else:
            # Valor por defecto si no hay sesión
            return 1
    except:
        # Valor por defecto si hay error
        return 1

def eliminar_permiso_usuario(id_permiso):
    """
    Elimina un permiso de usuario de la base de datos.
    
    Args:
        id_permiso: Identificador del permiso en formato 'U-{user_id}-{door_id}'
        
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    connection = None
    cursor = None
    try:
        # Verificar si el ID de permiso tiene el formato esperado
        if not id_permiso.startswith('U-'):
            print(f"Formato de ID de permiso no válido: {id_permiso}")
            return False
            
        # Extraer user_id y door_id del ID de permiso
        parts = id_permiso.split('-')
        if len(parts) != 3:
            print(f"Formato de ID de permiso no válido: {id_permiso}")
            return False
            
        user_id = parts[1]
        door_id = parts[2]
        
        connection = get_connection()
        if connection is None:
            return False
            
        cursor = connection.cursor()
        
        # Eliminar el permiso de la tabla userdoorpermit
        query = """
        DELETE FROM userdoorpermit 
        WHERE ID_user = %s AND ID_door = %s
        """
        
        cursor.execute(query, (user_id, door_id))
        connection.commit()
        
        if cursor.rowcount > 0:
            print(f"Permiso eliminado correctamente: Usuario {user_id}, Puerta {door_id}")
            return True
        else:
            print(f"No se encontró el permiso para eliminar: Usuario {user_id}, Puerta {door_id}")
            return False
            
    except Error as e:
        print(f"Error al eliminar permiso: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

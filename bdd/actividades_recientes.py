import mysql.connector
from datetime import datetime

def obtener_conexion():
    """Obtiene una conexión a la base de datos usando la configuración existente"""
    try:
        import bdd.config as config
        conexion = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        return conexion
    except mysql.connector.Error as err:
        print(f"[ERROR] Error al conectar a la base de datos: {err}")
        return None

def obtener_actividades_recientes(limite=50, user_id=None, tipo=None):
    """Obtiene las actividades recientes de los usuarios, incluyendo tanto Activity como tracking
    
    Args:
        limite (int): Número máximo de actividades a devolver
        user_id (int): ID del usuario que realiza la consulta
        tipo (str, optional): Tipo de actividad a filtrar ('login', 'door', 'profile', etc.)
    """
    conexion = obtener_conexion()
    if not conexion:
        print("[ERROR] No se pudo conectar a la base de datos")
        return []
    
    try:
        cursor = conexion.cursor(dictionary=True)
        
        # Consulta para actividades de puertas (Activity)
        query_activity = """
        SELECT 
            ua.ID_user as user_id,
            ua.name as nombre,
            ua.surname as apellido,
            CONCAT(ua.name, ' ', ua.surname) as nombre_completo,
            d.door_name as puerta,
            a.activity_datetime as fecha_hora,
            a.activity_details as detalles,
            CASE 
                WHEN a.activity_details LIKE '%Acceso exitoso%' THEN 'door'
                WHEN a.activity_details LIKE '%inició sesión%' THEN 'login'
                WHEN a.activity_details LIKE '%actualizó%' THEN 'profile'
                ELSE 'system'
            END as tipo_actividad,
            'success' as status,
            'activity' as fuente
        FROM Activity a
        JOIN UserAtributes ua ON a.ID_useratributes = ua.ID_useratributes
        LEFT JOIN Door d ON a.ID_door = d.ID_door
        WHERE 1=1
        """
        
        # Consulta para actividades de seguimiento (tracking)
        query_tracking = """
        SELECT 
            ua.ID_user as user_id,
            ua.name as nombre,
            ua.surname as apellido,
            CONCAT(ua.name, ' ', ua.surname) as nombre_completo,
            NULL as puerta,
            t.track_date as fecha_hora,
            t.track_details as detalles,
            t.type as tipo_actividad,
            'success' as status,
            'tracking' as fuente
        FROM tracking t
        JOIN UserAtributes ua ON t.ID_useratributes = ua.ID_useratributes
        WHERE 1=1
        """
        
        params = []
        params_tracking = []
        
        # Aplicar filtro de usuario si no es admin
        if user_id and user_id != 1:
            query_activity += " AND ua.ID_user = %s"
            query_tracking += " AND ua.ID_user = %s"
            params.append(user_id)
            params_tracking.append(user_id)
        
        # Aplicar filtro de tipo de actividad
        if tipo:
            if tipo == 'door':
                query_activity += " AND a.activity_details LIKE %s"
                params.append('%Acceso exitoso%')
                # No incluir tracking para este tipo
                query_tracking += " AND 1=0"
            elif tipo == 'login':
                query_activity += " AND a.activity_details LIKE %s"
                params.append('%inició sesión%')
                query_tracking += " AND t.type = 'login'"
            elif tipo == 'profile':
                query_activity += " AND a.activity_details LIKE %s"
                params.append('%actualizó%')
                query_tracking += " AND t.type IN ('actualizacion_perfil', 'cambio_foto_perfil', 'cambio_password')"
            elif tipo == 'system':
                query_activity += " AND a.activity_details NOT LIKE %s AND a.activity_details NOT LIKE %s"
                params.extend(['%Acceso exitoso%', '%inició sesión%'])
                # No incluir tracking para este tipo
                query_tracking += " AND 1=0"
        
        # Ordenar y limitar
        query_activity += " ORDER BY a.activity_datetime DESC LIMIT %s"
        query_tracking += " ORDER BY t.track_date DESC LIMIT %s"
        
        # Ejecutar ambas consultas
        print(f"[DEBUG] Ejecutando consulta de actividades: {query_activity}")
        print(f"[DEBUG] Parámetros: {params + [limite]}")
        
        cursor.execute(query_activity, params + [limite])
        actividades = cursor.fetchall()
        
        print(f"[DEBUG] Actividades de Activity: {actividades}")
        
        cursor.execute(query_tracking, params_tracking + [limite])
        actividades_tracking = cursor.fetchall()
        
        print(f"[DEBUG] Actividades de Tracking: {actividades_tracking}")
        
        # Combinar y ordenar resultados
        todas_actividades = actividades + actividades_tracking
        
        # Ordenar por fecha descendente
        todas_actividades.sort(key=lambda x: x['fecha_hora'] if x['fecha_hora'] else '', reverse=True)
        
        # Aplicar límite después de combinar
        if limite:
            todas_actividades = todas_actividades[:limite]
        
        # Formatear fechas
        for actividad in todas_actividades:
            if actividad['fecha_hora']:
                fecha = actividad['fecha_hora']
                if isinstance(fecha, str):
                    try:
                        fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S.%f')
                        except ValueError:
                            # Si no se puede parsear, usar la fecha actual
                            fecha = datetime.now()
                
                actividad['fecha_hora'] = fecha.strftime('%Y-%m-%d %H:%M:%S')
                actividad['fecha_formateada'] = fecha.strftime('%d/%m/%Y %H:%M')
        
        print(f"[DEBUG] Total de actividades combinadas: {len(todas_actividades)}")
        
        return todas_actividades
        
    except Exception as e:
        print(f"[ERROR] Error al obtener actividades recientes: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()

def obtener_estadisticas_actividades(user_id=None):
    """Obtiene estadísticas de actividades para el dashboard"""
    conexion = obtener_conexion()
    if not conexion:
        return {}
    
    try:
        cursor = conexion.cursor(dictionary=True)
        
        # Consultas para inicios de sesión (Activity + Tracking)
        query_login_activity = """
        SELECT COUNT(*) as total
        FROM Activity a
        JOIN UserAtributes ua ON a.ID_useratributes = ua.ID_useratributes
        WHERE a.activity_details LIKE '%inició sesión%'
          AND a.activity_datetime >= DATE_FORMAT(NOW(), '%Y-%m-01')
        """
        query_login_tracking = """
        SELECT COUNT(*) as total
        FROM tracking t
        JOIN UserAtributes ua ON t.ID_useratributes = ua.ID_useratributes
        WHERE t.type = 'login'
          AND t.track_date >= DATE_FORMAT(NOW(), '%Y-%m-01')
        """
        
        # Consulta para accesos a puertas
        query_door = """
        SELECT COUNT(*) as total
        FROM Activity a
        JOIN UserAtributes ua ON a.ID_useratributes = ua.ID_useratributes
        WHERE a.activity_details LIKE '%Acceso exitoso%'
          AND a.activity_datetime >= DATE_FORMAT(NOW(), '%Y-%m-01')
        """
        
        # Consulta para último acceso
        query_last_access = """
        SELECT d.door_name as puerta, a.activity_datetime as fecha_hora
        FROM Activity a
        JOIN UserAtributes ua ON a.ID_useratributes = ua.ID_useratributes
        LEFT JOIN Door d ON a.ID_door = d.ID_door
        WHERE a.activity_details LIKE '%Acceso exitoso%'
        """
        
        params_activity = []
        params_tracking = []
        params_common = []
        
        # Si el usuario no es admin, filtrar por su ID
        if user_id and user_id != 1:
            query_login_activity += " AND ua.ID_user = %s"
            query_login_tracking += " AND ua.ID_user = %s"
            query_door += " AND ua.ID_user = %s"
            query_last_access += " AND ua.ID_user = %s"
            params_activity = [user_id]
            params_tracking = [user_id]
            params_common = [user_id]
        
        query_last_access += " ORDER BY a.activity_datetime DESC LIMIT 1"
        
        # Ejecutar consultas
        cursor.execute(query_login_activity, tuple(params_activity))
        login_activity_count = cursor.fetchone()['total']
        cursor.execute(query_login_tracking, tuple(params_tracking))
        login_tracking_count = cursor.fetchone()['total']
        logins = (login_activity_count or 0) + (login_tracking_count or 0)
        
        cursor.execute(query_door, tuple(params_common))
        door_accesses = cursor.fetchone()['total']
        
        cursor.execute(query_last_access, tuple(params_common))
        last_access = cursor.fetchone()
        
        return {
            'logins_este_mes': logins or 0,
            'accesos_puertas_este_mes': door_accesses or 0,
            'ultimo_acceso': last_access or None
        }
        
    except mysql.connector.Error as err:
        print(f"[ERROR] Error al obtener estadísticas: {err}")
        return {}
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

def filtrar_actividades(usuario_id=None, puerta_id=None, tipo_actividad=None, fecha_inicio=None, fecha_fin=None):
    """Filtra actividades según criterios específicos"""
    conexion = obtener_conexion()
    if not conexion:
        return []
    
    try:
        cursor = conexion.cursor(dictionary=True)
        
        query = """
        SELECT 
            ua.name as nombre,
            ua.surname as apellido,
            CONCAT(ua.name, ' ', ua.surname) as nombre_completo,
            d.door_name as puerta,
            a.activity_datetime as fecha_hora,
            a.activity_details as detalles
        FROM Activity a
        JOIN UserAtributes ua ON a.ID_useratributes = ua.ID_useratributes
        JOIN Door d ON a.ID_door = d.ID_door
        WHERE 1=1
        """
        
        params = []
        
        if usuario_id:
            query += " AND ua.ID_user = %s"
            params.append(usuario_id)
            
        if puerta_id:
            query += " AND a.ID_door = %s"
            params.append(puerta_id)
            
        if fecha_inicio:
            query += " AND DATE(a.activity_datetime) >= %s"
            params.append(fecha_inicio)
            
        if fecha_fin:
            query += " AND DATE(a.activity_datetime) <= %s"
            params.append(fecha_fin)
            
        query += " ORDER BY a.activity_datetime DESC"
        
        cursor.execute(query, params)
        actividades = cursor.fetchall()
        
        # Formatear las fechas
        for actividad in actividades:
            actividad['fecha_hora'] = actividad['fecha_hora'].strftime('%Y-%m-%d %H:%M:%S')
            
        return actividades
        
    except mysql.connector.Error as err:
        print(f"[ERROR] Error al filtrar actividades: {err}")
        return []
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

def obtener_usuarios_para_filtros():
    """Obtiene lista de usuarios para filtros"""
    conexion = obtener_conexion()
    if not conexion:
        return []
    
    try:
        cursor = conexion.cursor(dictionary=True)
        query = """
        SELECT 
            u.ID_user as id, 
            ua.name as nombre, 
            ua.surname as apellido 
        FROM User u
        JOIN UserAtributes ua ON u.ID_user = ua.ID_user
        ORDER BY ua.name, ua.surname
        """
        cursor.execute(query)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"[ERROR] Error al obtener usuarios: {err}")
        return []
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

def obtener_puertas_para_filtros():
    """Obtiene lista de puertas para filtros"""
    conexion = obtener_conexion()
    if not conexion:
        return []
    
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT ID_door as id, door_name as nombre FROM Door ORDER BY door_name")
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"[ERROR] Error al obtener puertas: {err}")
        return []
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

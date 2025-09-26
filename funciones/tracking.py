"""
Módulo para el registro de eventos de seguimiento de usuarios
"""

def registrar_evento_tracking(user_id, tipo_evento, detalles=None):
    """
    Registra un evento en la tabla de tracking
    
    Args:
        user_id (int): ID del usuario que realiza la acción
        tipo_evento (str): Tipo de evento (ej: 'login', 'registro', 'actualizacion_perfil', 'cambio_password', 'cambio_foto')
        detalles (str, optional): Detalles adicionales sobre el evento
    
    Returns:
        bool: True si el registro fue exitoso, False en caso contrario
    """
    from bdd.conexionBDD import get_connection
    import logging
    import sys
    
    # Configurar logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    if not user_id:
        logger.error("No se proporcionó user_id para registrar el evento de tracking")
        return False
    
    conn = None
    try:
        # Obtener conexión a la base de datos
        conn = get_connection()
        if not conn:
            logger.error("No se pudo conectar a la base de datos para registrar evento de tracking")
            return False
        
        cursor = conn.cursor()
        
        # Obtener el ID de UserAtributes para el usuario
        query = """
            SELECT ID_useratributes 
            FROM UserAtributes 
            WHERE ID_user = %s
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        
        if not result:
            logger.error(f"No se encontró UserAtributes para el usuario ID: {user_id}")
            return False
            
        id_useratributes = result[0]
        
        # Insertar el registro de tracking
        insert_query = """
            INSERT INTO tracking 
            (ID_useratributes, type, track_details) 
            VALUES (%s, %s, %s)
        """
        cursor.execute(insert_query, (id_useratributes, tipo_evento, str(detalles) if detalles else None))
        
        # Confirmar la transacción
        conn.commit()
        logger.info(f"Evento de tracking registrado: usuario_id={user_id}, tipo={tipo_evento}")
        return True
        
    except Exception as e:
        # Hacer rollback en caso de error
        if conn:
            conn.rollback()
        logger.error(f"Error al registrar evento de tracking: {str(e)}", exc_info=True)
        return False
        
    finally:
        # Cerrar la conexión
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error al cerrar la conexión: {str(e)}")
                pass

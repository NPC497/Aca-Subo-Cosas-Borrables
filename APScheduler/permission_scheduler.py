# MSN: APScheduler module for automatic permission cleanup
import mysql.connector
from mysql.connector import Error
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, timezone
import logging
import atexit
from bdd.conexionBDD import get_connection
import threading

# MSN: Configure logging for scheduler
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MSN: Global scheduler instance with thread lock
scheduler = None
scheduler_lock = threading.Lock()
jobstore = 'default'
executors = {
    'default': {'type': 'threadpool', 'max_workers': 1}
}
job_defaults = {
    'misfire_grace_time': 30,
    'coalesce': True,
    'max_instances': 1
}

# Make scheduler available for import
scheduler_instance = BackgroundScheduler(
    executors=executors,
    job_defaults=job_defaults,
    timezone='UTC'  # Usar UTC como timezone base
)

def get_scheduler():
    """
    MSN: Get or create a singleton instance of the scheduler
    """
    global scheduler
    
    if scheduler is None:
        with scheduler_lock:
            if scheduler is None:  # Double-checked locking pattern
                try:
                    # Configurar el scheduler con timezone explícito
                    scheduler = scheduler_instance
                    logger.info("MSN: Nueva instancia de scheduler creada")
                except Exception as e:
                    logger.error(f"MSN: Error al crear el scheduler: {e}")
                    raise
    
    return scheduler

def cleanup_expired_permissions():
    """
    MSN: Function to check and remove expired time-limited permissions
    Only affects permissions that have expiration times set (not permanent ones)
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        if connection is None:
            logger.error("MSN: No se pudo conectar a la base de datos")
            return
        
        cursor = connection.cursor(dictionary=True)
        
        # MSN: Find expired permissions (only those with expiration_time set)
        query_expired = """
        SELECT ID_userdoorpermit, ID_user, ID_door, created_at, expiration_time
        FROM userdoorpermit 
        WHERE expiration_time IS NOT NULL 
        AND expiration_time <= NOW()
        """
        
        logger.info(f"MSN: Ejecutando consulta: {query_expired}")
        cursor.execute(query_expired)
        expired_permissions = cursor.fetchall()
        
        if expired_permissions:
            logger.info(f"MSN: Encontrados {len(expired_permissions)} permisos expirados")
            logger.info(f"MSN: Detalles de permisos: {expired_permissions}")
            
            # MSN: Delete expired permissions
            for permission in expired_permissions:
                delete_query = """
                DELETE udp FROM userdoorpermit udp
                WHERE ID_userdoorpermit = %s
                """
                logger.info(f"MSN: Intentando eliminar permiso ID: {permission['ID_userdoorpermit']}")
                
                try:
                    cursor.execute(delete_query, (permission['ID_userdoorpermit'],))
                    logger.info(f"MSN: Filas afectadas: {cursor.rowcount}")
                    
                    # MSN: Log the activity for audit purposes
                    activity_query = """
                    INSERT INTO Activity (ID_useratributes, ID_door, activity_details)
                    SELECT ua.ID_useratributes, %s, CONCAT('Permiso temporal expirado automáticamente - Duración: ', 
                        TIMESTAMPDIFF(MINUTE, %s, %s), ' minutos')
                    FROM UserAtributes ua
                    WHERE ua.ID_user = %s
                    """
                    
                    cursor.execute(activity_query, (
                        permission['ID_door'],
                        permission['created_at'],
                        permission['expiration_time'],
                        permission['ID_user']
                    ))
                    
                    logger.info(f"MSN: Actividad registrada para permiso eliminado - Usuario ID: {permission['ID_user']}, Puerta ID: {permission['ID_door']}")
                    
                except Error as e:
                    logger.error(f"MSN: Error al eliminar permiso {permission['ID_userdoorpermit']}: {e}")
                    connection.rollback()
                    continue
            
            try:
                connection.commit()
                logger.info(f"MSN: Commit exitoso - {len(expired_permissions)} permisos expirados eliminados")
            except Error as e:
                logger.error(f"MSN: Error al hacer commit: {e}")
                connection.rollback()
                
        else:
            logger.info("MSN: No se encontraron permisos expirados")
            
    except Error as e:
        logger.error(f"MSN: Error en la conexión o consulta: {e}")
        if connection:
            connection.rollback()
    except Exception as e:
        logger.error(f"MSN: Error inesperado: {type(e).__name__}: {e}", exc_info=True)
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def get_permissions_status():
    """
    MSN: Get current status of permissions for monitoring
    Returns dict with counts of total, permanent, and temporary permissions
    """
    connection = None
    cursor = None
    try:
        connection = get_connection()
        if connection is None:
            return {"error": "No database connection"}
        
        cursor = connection.cursor(dictionary=True)
        
        # MSN: Count total permissions
        cursor.execute("SELECT COUNT(*) as total FROM userdoorpermit")
        total = cursor.fetchone()['total']
        
        # MSN: Count permanent permissions (no expiration)
        cursor.execute("SELECT COUNT(*) as permanent FROM userdoorpermit WHERE expiration_time IS NULL")
        permanent = cursor.fetchone()['permanent']
        
        # MSN: Count temporary permissions (with expiration)
        cursor.execute("SELECT COUNT(*) as temporary FROM userdoorpermit WHERE expiration_time IS NOT NULL")
        temporary = cursor.fetchone()['temporary']
        
        # MSN: Count active temporary permissions (not yet expired)
        cursor.execute("SELECT COUNT(*) as active_temporary FROM userdoorpermit WHERE expiration_time IS NOT NULL AND expiration_time > NOW()")
        active_temporary = cursor.fetchone()['active_temporary']
        
        return {
            "total_permissions": total,
            "permanent_permissions": permanent,
            "temporary_permissions": temporary,
            "active_temporary_permissions": active_temporary,
            "expired_permissions": temporary - active_temporary
        }
        
    except Error as e:
        logger.error(f"MSN: Error al obtener estado de permisos: {e}")
        return {"error": str(e)}
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def init_scheduler():
    """
    MSN: Initialize the scheduler with the cleanup job
    Returns the scheduler instance if successful, None otherwise
    """
    global scheduler
    
    try:
        scheduler = get_scheduler()
        if scheduler is None:
            return None
            
        with scheduler_lock:
            # Remove any existing job to prevent duplicates
            if scheduler.get_job('cleanup_expired_permissions'):
                scheduler.remove_job('cleanup_expired_permissions')
                logger.info("MSN: Job de limpieza existente eliminado")
            
            # Add the job only if it doesn't exist
            if not scheduler.get_job('cleanup_expired_permissions'):
                scheduler.add_job(
                    func=cleanup_expired_permissions,
                    trigger=CronTrigger(second='0'),  # Run at second 0 of every minute
                    id='cleanup_expired_permissions',
                    name='Limpiar permisos expirados',
                    replace_existing=True,
                    max_instances=1
                )
                logger.info("MSN: Job de limpieza programado correctamente")
                
                # Obtener la próxima ejecución usando el método get_next_run_time
                next_run = scheduler.get_job('cleanup_expired_permissions')
                if next_run and hasattr(next_run, 'next_run_time') and next_run.next_run_time:
                    logger.info(f"MSN: Próxima ejecución programada: {next_run.next_run_time}")
                else:
                    logger.info("MSN: No se pudo determinar la próxima ejecución")
            
            return scheduler
            
    except Exception as e:
        logger.error(f"MSN: Error al inicializar el job de limpieza: {str(e)}", exc_info=True)
        if scheduler is not None:
            try:
                scheduler.shutdown()
            except:
                pass
            scheduler = None
        return None

def start_scheduler():
    """
    MSN: Start the scheduler if not already running
    Returns True if started successfully, False otherwise
    """
    global scheduler
    
    try:
        if scheduler is None:
            scheduler = init_scheduler()
            
        if scheduler is None:
            logger.error("MSN: No se pudo inicializar el scheduler")
            return False
            
        with scheduler_lock:
            if scheduler.running:
                logger.warning("MSN: El scheduler ya está en ejecución")
                return True
                
            scheduler.start()
            
            # Calculate next run time
            job = scheduler.get_job('cleanup_expired_permissions')
            if job and job.next_run_time:
                next_run = job.next_run_time
                now = datetime.now(timezone.utc).astimezone()  # Make timezone-aware
                next_run = next_run.astimezone(now.tzinfo)  # Convert to local timezone
                sec_until = (next_run - now).total_seconds()
                logger.info(f"MSN: Scheduler iniciado. Próxima ejecución en {int(sec_until)} segundos")
            else:
                logger.warning("MSN: Scheduler iniciado pero no se pudo determinar la próxima ejecución")
                
            return True
            
    except Exception as e:
        logger.error(f"MSN: Error al iniciar el scheduler: {str(e)}", exc_info=True)
        return False

def stop_scheduler():
    """
    MSN: Stop the scheduler if it's running
    Returns True if stopped successfully, False otherwise
    """
    global scheduler
    
    with scheduler_lock:
        if scheduler is None:
            logger.warning("MSN: No se puede detener el scheduler, no está inicializado")
            return False
            
        if not scheduler.running:
            logger.warning("MSN: El scheduler no está en ejecución")
            return True
            
        try:
            scheduler.shutdown()
            logger.info("MSN: Scheduler detenido correctamente")
            return True
            
        except Exception as e:
            logger.error(f"MSN: Error al detener scheduler: {e}")
            return False

def get_scheduler_status():
    """
    MSN: Get current scheduler status
    Returns dict with status information
    """
    global scheduler
    
    if scheduler is None:
        return {"status": "not_initialized", "running": False}
        
    return {
        "status": "initialized",
        "running": scheduler.running,
        "next_run_time": str(scheduler.get_job('cleanup_expired_permissions').next_run_time) if scheduler.running else None
    }

# MSN: Ensure we only have one instance of the scheduler
scheduler = get_scheduler()

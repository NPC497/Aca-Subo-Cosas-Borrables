"""
Decoradores de autenticación para proteger rutas
"""
from functools import wraps
from flask import session, redirect, url_for, flash, render_template, jsonify, request
from bdd.conexionBDD import get_connection
from config import CONFIG

# MSN: API key configuration (should match the one in app.py)
API_KEYS = {
    'default': 'MBordon'  # CAMBIAR EN PRODUCCIÓN
}

def require_api_key(f):
    """Decorator para validar API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != CONFIG['API_KEY']:
            return jsonify({'status': False, 'message': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    """Decorador que requiere que el usuario esté logueado"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, inicia sesión para acceder a esta página')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorador que requiere que el usuario sea administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, inicia sesión para acceder a esta página')
            return redirect(url_for('auth.login'))
        
        # Verificar si el usuario es administrador
        # Aquí deberías verificar el rol del usuario
        # Por ahora, asumimos que el rol 1 es administrador
        if session.get('role') != 1:
            flash('No tienes permisos para acceder a esta página')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def nfc_required(f):
    """Decorador que verifica si el usuario tiene nfc_code asignado"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # No need to check session here since @login_required already does it
        
        # Verificar si el usuario es el ID 1 (superusuario que no requiere NFC)
        user_id = session.get('user_id')
        if user_id == 1:
            return f(*args, **kwargs)
            
        # Verificar si el usuario tiene nfc_code asignado
        conn = get_connection()
        
        if not conn:
            flash('Error de conexión a la base de datos. Por favor, intente nuevamente.')
            return render_template('shared/errores.html', 
                                 error_message='Error de conexión a la base de datos')
        
        try:
            cursor = conn.cursor()
            query = """
                SELECT nfc_code 
                FROM UserAtributes 
                WHERE ID_user = %s
            """
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            # Si no hay resultado o nfc_code está vacío, redirigir a pantalla de revisión
            if not result or not result[0] or result[0].strip() == '':
                return render_template('shared/cuenta-en-revision.html')
            
            return f(*args, **kwargs)
            
        except Exception as e:
            print(f"Error verificando nfc_code: {e}")
            flash('Error al verificar el estado de la cuenta. Por favor, contacte al administrador.')
            return render_template('shared/errores.html', 
                                 error_message=f'Error al verificar el estado de la cuenta: {str(e)}')
        finally:
            if conn:
                conn.close()
                
    return decorated_function

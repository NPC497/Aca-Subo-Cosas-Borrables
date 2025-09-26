from flask import Flask, render_template, request

app = Flask(__name__)

# Diccionario de errores y sus descripciones
errores = {
    'error_404': {
        'titulo': 'Error 404',
        'descripcion': 'Página no encontrada. El recurso solicitado no existe en el servidor.'
    },
    'error_500': {
        'titulo': 'Error 500',
        'descripcion': 'Error interno del servidor. Algo salió mal en el servidor.'
    },
    'error_403': {
        'titulo': 'Error 403',
        'descripcion': 'Acceso prohibido. No tienes permisos para acceder a este recurso.'
    },
    'error_401': {
        'titulo': 'Error 401',
        'descripcion': 'No autorizado. Se requiere autenticación para acceder a este recurso.'
    },
    'file_not_found': {
        'titulo': 'Archivo no encontrado',
        'descripcion': 'El archivo solicitado no pudo ser encontrado en el servidor.'
    },
    'permission_denied': {
        'titulo': 'Permiso denegado',
        'descripcion': 'No tienes permiso para acceder a este recurso.'
    },
    'default': {
        'titulo': 'Error inesperado',
        'descripcion': 'Ha ocurrido un error inesperado. Por favor, contacte al administrador.'
    }
}

@app.route('/')
def index():
    # Redirigir a la página de errores con un error genérico
    return render_template('shared/errores.html', 
                          titulo="Error", 
                          descripcion="Descripcion del error dado.")

@app.route('/error/<codigo_error>')
def mostrar_error(codigo_error):
    # Obtener información del error del diccionario
    error_info = errores.get(codigo_error, errores['default'])
    
    return render_template('shared/errores.html', 
                          titulo=error_info['titulo'], 
                          descripcion=error_info['descripcion'])

@app.route('/error')
def error_por_parametro():
    # Obtener el código de error desde los parámetros de la URL
    codigo_error = request.args.get('codigo', 'default')
    error_info = errores.get(codigo_error, errores['default'])
    
    return render_template('shared/errores.html', 
                          titulo=error_info['titulo'], 
                          descripcion=error_info['descripcion'])

if __name__ == '__main__':
    # Puerto 8000 como se especificó anteriormente
    app.run(debug=True, port=8000)

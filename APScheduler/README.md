# MSN: APScheduler Module - Automatic Permission Cleanup

Este módulo implementa un sistema automático de limpieza de permisos temporales usando APScheduler.

## Funcionalidad

- **Limpieza automática**: Ejecuta cada 5 minutos para eliminar permisos expirados
- **Solo permisos temporales**: Únicamente afecta permisos con `expiration_time` definido
- **Permisos permanentes**: Los permisos con `expiration_time = NULL` no son afectados
- **Registro de actividad**: Cada eliminación se registra en la tabla `Activity`

## Instalación

1. **Ejecutar migración de base de datos**:
   ```sql
   -- Ejecutar el archivo database_migration.sql
   source APScheduler/database_migration.sql;
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

### Inicialización Automática
El scheduler se inicializa automáticamente al arrancar la aplicación Flask.

### API Endpoints

- **GET `/api/scheduler/status`**: Obtiene el estado del scheduler y estadísticas de permisos
- **GET `/api/scheduler/cleanup`**: Ejecuta limpieza manual de permisos expirados

### Funciones Principales

```python
from APScheduler import init_scheduler, start_scheduler

# Inicializar scheduler
init_scheduler()

# Iniciar scheduler
start_scheduler()
```

## Estructura de Base de Datos

### Campos Agregados a `userdoorpermit`:

- `created_at`: Timestamp de creación del permiso
- `expiration_time`: Timestamp de expiración (NULL = permanente)
- `granted_by`: ID del administrador que otorgó el permiso

## Tipos de Permisos

### Permanentes
- `tiempo_minutos = 0` o `tiempo_minutos < 0`
- `expiration_time = NULL`
- **No son eliminados** por el scheduler

### Temporales
- `tiempo_minutos > 0`
- `expiration_time = created_at + INTERVAL tiempo_minutos MINUTE`
- **Son eliminados** automáticamente al expirar

## Monitoreo

### Estado del Scheduler
```json
{
  "scheduler": {
    "status": "initialized",
    "running": true,
    "jobs": 1
  },
  "permissions": {
    "total_permissions": 15,
    "permanent_permissions": 10,
    "temporary_permissions": 5,
    "active_temporary_permissions": 3,
    "expired_permissions": 2
  }
}
```

## Logs

El módulo registra todas las actividades importantes:
- Inicialización del scheduler
- Permisos expirados encontrados y eliminados
- Errores de conexión a base de datos
- Estado de ejecución

## Configuración

- **Intervalo de limpieza**: 5 minutos (configurable en `permission_scheduler.py`)
- **Logging**: Nivel INFO por defecto
- **Manejo de errores**: Rollback automático en caso de error

## Seguridad

- Requiere autenticación (`@login_required`)
- Requiere NFC válido (`@nfc_required`)
- Solo administradores pueden acceder a endpoints de monitoreo
- Transacciones con rollback automático

-- Script de corrección de base de datos
-- Arregla problemas de foreign keys y permite valores NULL donde es necesario

USE NotFC;

-- ============================================
-- CORRECCIÓN 1: Permitir NULL en Activity.ID_useratributes
-- para registrar intentos con NFC desconocidos
-- ============================================

ALTER TABLE Activity 
MODIFY COLUMN ID_useratributes INT DEFAULT NULL;

-- ============================================
-- CORRECCIÓN 2: Permitir NULL en Tracking.ID_useratributes
-- para eventos del sistema sin usuario específico
-- ============================================

ALTER TABLE tracking 
MODIFY COLUMN ID_useratributes INT(11) DEFAULT NULL;

-- ============================================
-- CORRECCIÓN 3: Asegurar que existe al menos la puerta 1
-- que es la que usa el ESP32 por defecto
-- ============================================

INSERT INTO Door (ID_door, door_name, door_isOpen) 
VALUES (1, 'Puerta Principal', FALSE)
ON DUPLICATE KEY UPDATE 
    door_name = COALESCE(door_name, 'Puerta Principal');

-- ============================================
-- CORRECCIÓN 4: Agregar índices para mejorar performance
-- ============================================

-- Índice para búsquedas rápidas por NFC
ALTER TABLE UserAtributes 
ADD INDEX idx_nfc_code (nfc_code);

-- Índice para historial de puertas
ALTER TABLE DoorStateHistory 
ADD INDEX idx_door_time (ID_door, changed_at);

-- Índice para actividad
ALTER TABLE Activity 
ADD INDEX idx_door_datetime (ID_door, activity_datetime);

-- ============================================
-- VERIFICACIÓN: Mostrar estructura actualizada
-- ============================================

SELECT 'Estructura de tabla Activity:' as '';
DESCRIBE Activity;

SELECT 'Estructura de tabla Tracking:' as '';
DESCRIBE tracking;

SELECT 'Puertas existentes:' as '';
SELECT * FROM Door;

COMMIT;
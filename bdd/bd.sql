CREATE DATABASE IF NOT EXISTS NotFC;
USE NotFC;

-- Tabla de usuarios (autenticación)
CREATE TABLE User (
    ID_user INT AUTO_INCREMENT PRIMARY KEY,
    mail VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    user_status BOOLEAN DEFAULT TRUE,
    profile_photo VARCHAR(255) DEFAULT NULL,
    creation_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de puertas
CREATE TABLE Door (
    ID_door INT PRIMARY KEY AUTO_INCREMENT,
    door_img TEXT,
    door_name VARCHAR(100),
    door_isOpen BOOLEAN DEFAULT FALSE,
    creation_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de roles
CREATE TABLE Role (
    ID_role INT PRIMARY KEY AUTO_INCREMENT,
    role VARCHAR(50) UNIQUE NOT NULL,
    asignar_permisos_usuarios BOOLEAN DEFAULT FALSE
);

-- Relación muchos a muchos entre roles y puertas
CREATE TABLE RoleDoorPermit (
    ID_roledoorpermit INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ID_role INT,
    ID_door INT,
    FOREIGN KEY (ID_role) REFERENCES Role(ID_role),
    FOREIGN KEY (ID_door) REFERENCES Door(ID_door)
);

-- Tabla de atributos del usuario (vinculación con NFC y datos personales)
CREATE TABLE UserAtributes (
    ID_useratributes INT PRIMARY KEY AUTO_INCREMENT,
    ID_user INT NOT NULL,
    ID_role INT NOT NULL,
    name VARCHAR(100),
    surname VARCHAR(100),
    dni VARCHAR(20) UNIQUE,
    nfc_code VARCHAR(100) NOT NULL,
    user_inside BOOLEAN DEFAULT FALSE,
    exit_permit BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (ID_user) REFERENCES User(ID_user),
    FOREIGN KEY (ID_role) REFERENCES Role(ID_role)
);



-- Historial de estado de puertas
CREATE TABLE DoorStateHistory (
    ID_state INT PRIMARY KEY AUTO_INCREMENT,
    ID_door INT NOT NULL,
    state BOOLEAN NOT NULL,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ID_door) REFERENCES Door(ID_door)
);

-- Tabla de permisos individuales (historial)
CREATE TABLE Permit (
    ID_permit INT PRIMARY KEY AUTO_INCREMENT,
    ID_user INT NOT NULL,
    permit_status BOOLEAN NOT NULL,
    creation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ID_user) REFERENCES User(ID_user)
);

-- Tabla de actividad de acceso a puertas
CREATE TABLE Activity (
    ID_activity INT PRIMARY KEY AUTO_INCREMENT,
    ID_useratributes INT DEFAULT NULL,
    ID_door INT NOT NULL,
    activity_datetime DATETIME DEFAULT CURRENT_TIMESTAMP,
    activity_details TEXT,
    FOREIGN KEY (ID_useratributes) REFERENCES UserAtributes(ID_useratributes),
    FOREIGN KEY (ID_door) REFERENCES Door(ID_door)
);


CREATE TABLE userdoorpermit (
    ID_userdoorpermit INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ID_user INT NOT NULL,
    ID_door INT NOT NULL,
    CONSTRAINT fk_userdoorpermit_user FOREIGN KEY (ID_user) REFERENCES user (ID_user),
    CONSTRAINT fk_userdoorpermit_door FOREIGN KEY (ID_door) REFERENCES door (ID_door)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;


CREATE TABLE tracking (
    ID_tracking INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ID_useratributes INT(11) DEFAULT NULL,
    track_date DATETIME DEFAULT current_timestamp(),
    track_details TEXT DEFAULT NULL,
    type VARCHAR(50),
    CONSTRAINT tracking_ibfk_1 FOREIGN KEY (ID_useratributes) REFERENCES useratributes (ID_useratributes)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;


INSERT INTO Door (ID_door, door_name, door_isOpen) 
VALUES (1, 'Puerta Principal', FALSE)
ON DUPLICATE KEY UPDATE 
    door_name = COALESCE(door_name, 'Puerta Principal');

-- Índice para búsquedas rápidas por NFC
ALTER TABLE UserAtributes 
ADD INDEX idx_nfc_code (nfc_code);

-- Índice para historial de puertas
ALTER TABLE DoorStateHistory 
ADD INDEX idx_door_time (ID_door, changed_at);

-- Índice para actividad
ALTER TABLE Activity 
ADD INDEX idx_door_datetime (ID_door, activity_datetime);


-- Insertar roles básicos si no existen
INSERT IGNORE INTO Role (role, asignar_permisos_usuarios) VALUES 
('Admin', 1),
('Usuario', 0),
('Master', 1);

-- MSN: Database migration to add time-based expiration to permissions
-- This script adds the necessary fields to support time-limited permissions

-- MSN: Add expiration fields to userdoorpermit table
ALTER TABLE userdoorpermit 
ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'MSN: Timestamp when permission was granted',
ADD COLUMN expiration_time DATETIME NULL COMMENT 'MSN: When permission expires (NULL = permanent)',
ADD COLUMN granted_by INT NULL COMMENT 'MSN: ID of admin who granted the permission',
ADD CONSTRAINT fk_userdoorpermit_admin FOREIGN KEY (granted_by) REFERENCES user (ID_user);

-- MSN: Add index for efficient cleanup queries
ALTER TABLE userdoorpermit 
ADD INDEX idx_expiration_cleanup (expiration_time);

-- MSN: Add index for permission queries by user and door
ALTER TABLE userdoorpermit 
ADD INDEX idx_user_door_permission (ID_user, ID_door);

-- MSN: Update existing records to have created_at timestamp (set to current time)
UPDATE userdoorpermit 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

-- MSN: Note: Existing permissions will be treated as permanent (expiration_time = NULL)
-- This preserves current functionality while enabling new time-limited permissions

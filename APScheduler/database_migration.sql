-- MSN: Database migration to add time-based expiration to permissions
-- This script adds the necessary fields to support time-limited permissions

USE NotFC;

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

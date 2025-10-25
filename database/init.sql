-- Create database with proper character set and collation
CREATE DATABASE IF NOT EXISTS employee_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE employee_db;

-- Admin table for secure login
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- store hashed passwords for security
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username)  -- Add index for faster lookups
);

-- Employee productivity table with new fields
CREATE TABLE IF NOT EXISTS productivity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(100) NOT NULL,
    productivity INT DEFAULT 0 CHECK (productivity >= 0 AND productivity <= 100),
    feedback TEXT,
    rating DECIMAL(3,1) DEFAULT 0.0 CHECK (rating >= 0 AND rating <= 5.0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_role (role)
);

-- Clear existing data to avoid duplicates
DELETE FROM productivity;
DELETE FROM admins WHERE username = 'admin';

-- Insert sample employees
INSERT INTO productivity (name, role, productivity, feedback, rating) VALUES
('Kishore', 'Azure Cloud Developer', 90, 'Excellent Azure automation and DevOps contribution.', 4.7),
('Ravi', 'GCP Architect', 85, 'Strong architectural understanding; needs better documentation.', 4.4),
('Sanjay', 'AWS Associate', 80, 'Good performance; needs to engage in reviews.', 4.1);

-- Insert admin user with secure password hash
-- Password is 'admin123'
INSERT INTO admins (username, password_hash) VALUES (
    'admin',
    'scrypt:32768:8:1$0oWbNA1zxdGf9Dbw$35f0262c06031346ed85eb30d5a40d3c7402be2452f400888d9d6f3952e0cd6e9dd592fb37f350027bfa9ae625a3e10f217329429fc67e573f49804207da374e'
);

-- Verify admin user was created
SELECT COUNT(*) as admin_count FROM admins WHERE username='admin';

-- Grant minimum required permissions
GRANT SELECT, INSERT, UPDATE ON employee_db.* TO 'root'@'%';
FLUSH PRIVILEGES;
CREATE DATABASE IF NOT EXISTS employee_db;
USE employee_db;

-- Admin table for secure login
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL  -- store hashed passwords for security
);

-- Employee productivity table with new fields
CREATE TABLE IF NOT EXISTS productivity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(100) NOT NULL,
    productivity INT DEFAULT 0,
    feedback TEXT,
    rating DECIMAL(3,1) DEFAULT 0.0
);

-- Insert sample employees
INSERT INTO productivity (name, role, productivity, feedback, rating) VALUES
('Kishore', 'Azure Cloud Developer', 90, 'Excellent Azure automation and DevOps contribution.', 4.7),
('Ravi', 'GCP Architect', 85, 'Strong architectural understanding; needs better documentation.', 4.4),
('Sanjay', 'AWS Associate', 80, 'Good performance; needs to engage in reviews.', 4.1);

-- Insert default admin
INSERT INTO admins (username, password_hash)
VALUES ('admin', '$pbkdf2-sha256$29000$abcxyz$hashedpasswordexample');

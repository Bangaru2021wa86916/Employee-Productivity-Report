CREATE DATABASE IF NOT EXISTS employee_db;
USE employee_db;

CREATE TABLE IF NOT EXISTS productivity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    role VARCHAR(100),
    productivity INT,
    feedback TEXT,
    rating FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO productivity (name, role, productivity) VALUES
('Alice', 'Azure Cloud Developer', 85),
('Bob', 'GCP Architect', 90),
('Charlie', 'AWS Associate', 80);

CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255)
);

-- password = admin123 (pbkdf2_sha256)
INSERT INTO admins (username, password_hash)
VALUES ('admin', '$pbkdf2-sha256$29000$o3RujTFmrFUKAaCUkvKeEw$xn0DI55/qRI44qV/79Zd0MDuhjW/Cp0nUumdmvsQ7LY');
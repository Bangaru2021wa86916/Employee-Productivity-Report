CREATE DATABASE IF NOT EXISTS employee_db;
USE employee_db;

CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    role VARCHAR(100),
    productivity_score INT
);

INSERT INTO productivity (name, role, productivity_score) VALUES
('Alice', 'Azure Cloud Developer', 85),
('Bob', 'GCP Architect', 90),
('Charlie', 'AWS Associate', 80);

CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255)
);

INSERT INTO admins (username, password_hash)
VALUES ('admin', '$pbkdf2:sha256:260000$BEnm0e7aW9dx4UuG$7b7813a539c0da4b2324dbdbd3e3eb16e32cdd1b5c02a3b14c2e58b07848b7a9');
GRANT ALL PRIVILEGES ON employee_db.* TO 'root'@'%';
FLUSH PRIVILEGES;   
-- End of file
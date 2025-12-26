CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Insertar varios usuarios de ejemplo
INSERT INTO users (username, password_hash) VALUES
('alice', 'hashed_password_1'),
('bob', 'hashed_password_2'),
('charlie', 'hashed_password_3');
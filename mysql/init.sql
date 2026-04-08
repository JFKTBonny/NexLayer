-- mysql/init.sql
CREATE DATABASE IF NOT EXISTS appdb;
USE appdb;

-- Users table (owned by user-service)
CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(100) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table (owned by order-service)
CREATE TABLE IF NOT EXISTS orders (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    product    VARCHAR(100) NOT NULL,
    quantity   INT NOT NULL DEFAULT 1,
    price      DECIMAL(10,2) NOT NULL,
    status     ENUM('pending','confirmed','shipped','delivered') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Notifications table (owned by notification-service)
CREATE TABLE IF NOT EXISTS notifications (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    type       ENUM('email','sms') NOT NULL,
    message    TEXT NOT NULL,
    sent       BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed data
INSERT INTO users (name, email, password) VALUES
    ('Alice Smith',  'alice@example.com', 'hashed_password_1'),
    ('Bob Johnson',  'bob@example.com',   'hashed_password_2'),
    ('Carol White',  'carol@example.com', 'hashed_password_3');

INSERT INTO orders (user_id, product, quantity, price, status) VALUES
    (1, 'Laptop',     1, 999.99,  'confirmed'),
    (1, 'Mouse',      2, 29.99,   'shipped'),
    (2, 'Keyboard',   1, 79.99,   'pending'),
    (3, 'Monitor',    1, 399.99,  'delivered');

INSERT INTO notifications (user_id, type, message, sent) VALUES
    (1, 'email', 'Your order has been confirmed', TRUE),
    (2, 'sms',   'Your order is pending payment', FALSE),
    (3, 'email', 'Your order has been delivered', TRUE);
// notification-service/app.js
const express = require('express');
const mysql   = require('mysql2/promise');

const app = express();
app.use(express.json());

// DB connection pool
const pool = mysql.createPool({
    host:     process.env.DB_HOST     || 'mysql',
    user:     process.env.DB_USER     || 'root',
    password: process.env.DB_PASSWORD || 'rootpass',
    database: process.env.DB_NAME     || 'appdb',
    waitForConnections: true,
    connectionLimit:    10
});

// Health check
app.get('/health', async (req, res) => {
    try {
        await pool.query('SELECT 1');
        res.json({ service: 'notification-service', status: 'up' });
    } catch (err) {
        res.status(500).json({ service: 'notification-service', status: 'down', error: err.message });
    }
});

// Get all notifications
app.get('/api/notifications', async (req, res) => {
    try {
        const [rows] = await pool.query(
            'SELECT * FROM notifications ORDER BY created_at DESC'
        );
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Get notifications for a user
app.get('/api/notifications/user/:userId', async (req, res) => {
    try {
        const [rows] = await pool.query(
            'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC',
            [req.params.userId]
        );
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Create notification
app.post('/api/notifications', async (req, res) => {
    const { user_id, type, message } = req.body;

    if (!user_id || !type || !message) {
        return res.status(400).json({ error: 'user_id, type, message required' });
    }

    try {
        const [result] = await pool.query(
            'INSERT INTO notifications (user_id, type, message) VALUES (?, ?, ?)',
            [user_id, type, message]
        );

        // Simulate sending notification
        console.log(`[${type.toUpperCase()}] To user ${user_id}: ${message}`);

        res.status(201).json({
            id:      result.insertId,
            message: 'Notification created and queued'
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Mark notification as sent
app.put('/api/notifications/:id/send', async (req, res) => {
    try {
        const [result] = await pool.query(
            'UPDATE notifications SET sent = TRUE WHERE id = ?',
            [req.params.id]
        );
        if (result.affectedRows === 0) {
            return res.status(404).json({ error: 'Notification not found' });
        }
        res.json({ message: 'Notification marked as sent' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// Get unsent notifications
app.get('/api/notifications/pending', async (req, res) => {
    try {
        const [rows] = await pool.query(
            'SELECT * FROM notifications WHERE sent = FALSE'
        );
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Notification service running on port ${PORT}`));

module.exports = app;
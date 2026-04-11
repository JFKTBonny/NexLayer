// notification-service/tests/app.test.js
const request = require('supertest');

// app.js now exports without calling listen()
// No port binding conflict in tests
const app = require('../app');

// Mock mysql2 so tests run without a real database
jest.mock('mysql2/promise', () => {
    const mockPool = {
        query: jest.fn()
    };
    return {
        createPool: jest.fn(() => mockPool)
    };
});

// Get reference to mock pool for controlling responses
const mysql   = require('mysql2/promise');
const mockPool = mysql.createPool();

// Reset mocks before each test
beforeEach(() => {
    jest.clearAllMocks();
});

// ── Health Check ──────────────────────────────────────────
describe('GET /health', () => {

    test('returns up when DB is reachable', async () => {
        mockPool.query.mockResolvedValueOnce([[{ 1: 1 }]]);

        const res = await request(app).get('/health');

        expect(res.statusCode).toBe(200);
        expect(res.body.service).toBe('notification-service');
        expect(res.body.status).toBe('up');
    });

    test('returns down when DB is unreachable', async () => {
        mockPool.query.mockRejectedValueOnce(
            new Error('Connection refused')
        );

        const res = await request(app).get('/health');

        expect(res.statusCode).toBe(500);
        expect(res.body.status).toBe('down');
    });
});

// ── GET /api/notifications ────────────────────────────────
describe('GET /api/notifications', () => {

    test('returns list of notifications', async () => {
        mockPool.query.mockResolvedValueOnce([[
            { id: 1, user_id: 1, type: 'email',
              message: 'Test', sent: false }
        ]]);

        const res = await request(app).get('/api/notifications');

        expect(res.statusCode).toBe(200);
        expect(Array.isArray(res.body)).toBe(true);
        expect(res.body[0].id).toBe(1);
    });

    test('returns 500 on DB error', async () => {
        mockPool.query.mockRejectedValueOnce(
            new Error('DB error')
        );

        const res = await request(app).get('/api/notifications');

        expect(res.statusCode).toBe(500);
        expect(res.body.error).toBeDefined();
    });
});

// ── POST /api/notifications ───────────────────────────────
describe('POST /api/notifications', () => {

    test('creates notification with valid body', async () => {
        mockPool.query.mockResolvedValueOnce([{ insertId: 5 }]);

        const res = await request(app)
            .post('/api/notifications')
            .send({
                user_id: 1,
                type:    'email',
                message: 'Your order shipped'
            })
            .set('Content-Type', 'application/json');

        expect(res.statusCode).toBe(201);
        expect(res.body.id).toBe(5);
    });

    test('returns 400 when user_id missing', async () => {
        const res = await request(app)
            .post('/api/notifications')
            .send({ type: 'email', message: 'Test' })
            .set('Content-Type', 'application/json');

        expect(res.statusCode).toBe(400);
        expect(res.body.error).toBeDefined();
    });

    test('returns 400 when type missing', async () => {
        const res = await request(app)
            .post('/api/notifications')
            .send({ user_id: 1, message: 'Test' })
            .set('Content-Type', 'application/json');

        expect(res.statusCode).toBe(400);
    });

    test('returns 400 when message missing', async () => {
        const res = await request(app)
            .post('/api/notifications')
            .send({ user_id: 1, type: 'email' })
            .set('Content-Type', 'application/json');

        expect(res.statusCode).toBe(400);
    });

    test('returns 400 when body is empty', async () => {
        const res = await request(app)
            .post('/api/notifications')
            .send({})
            .set('Content-Type', 'application/json');

        expect(res.statusCode).toBe(400);
    });
});

// ── GET /api/notifications/pending ───────────────────────
describe('GET /api/notifications/pending', () => {

    test('returns only unsent notifications', async () => {
        mockPool.query.mockResolvedValueOnce([[
            { id: 2, user_id: 1, type: 'sms',
              message: 'Pending', sent: false }
        ]]);

        const res = await request(app)
            .get('/api/notifications/pending');

        expect(res.statusCode).toBe(200);
        expect(Array.isArray(res.body)).toBe(true);
    });
});

// ── PUT /api/notifications/:id/send ──────────────────────
describe('PUT /api/notifications/:id/send', () => {

    test('marks notification as sent', async () => {
        mockPool.query.mockResolvedValueOnce([{ affectedRows: 1 }]);

        const res = await request(app)
            .put('/api/notifications/1/send');

        expect(res.statusCode).toBe(200);
        expect(res.body.message).toBeDefined();
    });

    test('returns 404 when notification not found', async () => {
        mockPool.query.mockResolvedValueOnce([{ affectedRows: 0 }]);

        const res = await request(app)
            .put('/api/notifications/9999/send');

        expect(res.statusCode).toBe(404);
    });
});
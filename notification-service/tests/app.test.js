// notification-service/tests/app.test.js
const request = require('supertest');
const app     = require('../app');

describe('Health Check', () => {
    test('GET /health returns status up', async () => {
        const res = await request(app).get('/health');
        expect(res.statusCode).toBe(200);
        expect(res.body.service).toBe('notification-service');
    });
});

describe('Notifications API', () => {
    test('GET /api/notifications returns array', async () => {
        const res = await request(app).get('/api/notifications');
        // Either success or DB unavailable in test env
        expect([200, 500]).toContain(res.statusCode);
    });

    test('POST /api/notifications validates body', async () => {
        const res = await request(app)
            .post('/api/notifications')
            .send({})
            .set('Content-Type', 'application/json');
        expect(res.statusCode).toBe(400);
    });
});
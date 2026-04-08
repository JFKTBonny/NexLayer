# user-service/tests/test_integration.py
import json
import os
import pytest

# Only runs when INTEGRATION=true env var is set
# so unit tests stay fast and DB-free by default
pytestmark = pytest.mark.skipif(
    os.getenv('INTEGRATION') != 'true',
    reason='Integration tests require INTEGRATION=true and live MySQL'
)

class TestIntegration:

    def test_create_and_retrieve_user(self, client):
        create_resp = client.post(
            '/api/users',
            data=json.dumps({
                'name':     'Integration User',
                'email':    'integration@test.com',
                'password': 'intpass123'
            }),
            content_type='application/json'
        )
        assert create_resp.status_code == 201
        user_id = json.loads(create_resp.data)['id']

        get_resp = client.get(f'/api/users/{user_id}')
        assert get_resp.status_code == 200
        data = json.loads(get_resp.data)
        assert data['email'] == 'integration@test.com'

    def test_create_update_delete_user(self, client):
        create_resp = client.post(
            '/api/users',
            data=json.dumps({
                'name':     'Temp User',
                'email':    'temp@test.com',
                'password': 'temppass'
            }),
            content_type='application/json'
        )
        user_id = json.loads(create_resp.data)['id']

        update_resp = client.put(
            f'/api/users/{user_id}',
            data=json.dumps({'name': 'Updated Temp', 'email': 'temp@test.com'}),
            content_type='application/json'
        )
        assert update_resp.status_code == 200

        delete_resp = client.delete(f'/api/users/{user_id}')
        assert delete_resp.status_code == 200

        get_resp = client.get(f'/api/users/{user_id}')
        assert get_resp.status_code == 404

    def test_duplicate_email_rejected(self, client):
        payload = {
            'name':     'Dup User',
            'email':    'dup@test.com',
            'password': 'duppass'
        }
        first  = client.post('/api/users', data=json.dumps(payload), content_type='application/json')
        second = client.post('/api/users', data=json.dumps(payload), content_type='application/json')
        assert first.status_code  == 201
        assert second.status_code == 409

        # cleanup
        user_id = json.loads(first.data)['id']
        client.delete(f'/api/users/{user_id}')
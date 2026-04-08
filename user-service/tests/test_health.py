# user-service/tests/test_health.py
import json

class TestHealth:

    def test_health_endpoint_exists(self, client):
        response = client.get('/health')
        assert response.status_code in [200, 500]

    def test_health_returns_json(self, client):
        response = client.get('/health')
        data = json.loads(response.data)
        assert 'service' in data
        assert 'status' in data

    def test_health_service_name(self, client):
        response = client.get('/health')
        data = json.loads(response.data)
        assert data['service'] == 'user-service'

    def test_health_unknown_route(self, client):
        response = client.get('/unknown-route')
        assert response.status_code == 404
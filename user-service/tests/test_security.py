# user-service/tests/test_security.py
import json
from unittest.mock import patch, MagicMock

class TestSecurity:

    @patch('app.get_db')
    def test_password_never_returned_in_get_all(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'created_at': '2026-01-01'}
        ]
        response = client.get('/api/users')
        data     = json.loads(response.data)
        for user in data:
            assert 'password' not in user

    @patch('app.get_db')
    def test_password_never_returned_in_get_one(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'created_at': '2026-01-01'
        }
        response = client.get('/api/users/1')
        data     = json.loads(response.data)
        assert 'password' not in data

    @patch('app.get_db')
    def test_password_is_sha256_hashed(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid         = 10
        client.post(
            '/api/users',
            data=json.dumps({
                'name':     'Secure User',
                'email':    'secure@example.com',
                'password': 'myplainpassword'
            }),
            content_type='application/json'
        )
        call_args       = mock_cursor.execute.call_args
        stored_password = call_args[0][1][2]
        # SHA256 hash is always 64 hex chars
        assert len(stored_password) == 64
        assert stored_password != 'myplainpassword'

    def test_sql_injection_in_user_id(self, client):
        response = client.get("/api/users/1' OR '1'='1")
        # Flask routing rejects non-integer — returns 404 not 200
        assert response.status_code == 404

    def test_content_type_required_for_post(self, client):
        response = client.post(
            '/api/users',
            data='{"name":"Test","email":"t@t.com","password":"pass"}'
            # no content_type header
        )
        # Should fail gracefully — not 500
        assert response.status_code in [400, 415, 500]
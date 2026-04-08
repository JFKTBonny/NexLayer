# user-service/tests/test_users.py
import json
import pytest
from unittest.mock import patch, MagicMock

class TestGetUsers:

    @patch('app.get_db')
    def test_get_all_users_returns_200(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value    = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'created_at': '2026-01-01'},
            {'id': 2, 'name': 'Bob',   'email': 'bob@example.com',   'created_at': '2026-01-02'},
        ]
        response = client.get('/api/users')
        assert response.status_code == 200

    @patch('app.get_db')
    def test_get_all_users_returns_list(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'created_at': '2026-01-01'},
        ]
        response = client.get('/api/users')
        data     = json.loads(response.data)
        assert isinstance(data, list)

    @patch('app.get_db')
    def test_get_all_users_returns_correct_fields(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'created_at': '2026-01-01'},
        ]
        response = client.get('/api/users')
        data     = json.loads(response.data)
        user     = data[0]
        assert 'id'         in user
        assert 'name'       in user
        assert 'email'      in user
        assert 'created_at' in user
        assert 'password' not in user    # password must never be exposed

    @patch('app.get_db')
    def test_get_all_users_empty_list(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        response = client.get('/api/users')
        data     = json.loads(response.data)
        assert response.status_code == 200
        assert data == []


class TestGetUser:

    @patch('app.get_db')
    def test_get_existing_user_returns_200(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'created_at': '2026-01-01'
        }
        response = client.get('/api/users/1')
        assert response.status_code == 200

    @patch('app.get_db')
    def test_get_existing_user_returns_correct_data(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'id': 1, 'name': 'Alice Smith', 'email': 'alice@example.com', 'created_at': '2026-01-01'
        }
        response = client.get('/api/users/1')
        data     = json.loads(response.data)
        assert data['id']    == 1
        assert data['name']  == 'Alice Smith'
        assert data['email'] == 'alice@example.com'

    @patch('app.get_db')
    def test_get_nonexistent_user_returns_404(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        response = client.get('/api/users/9999')
        assert response.status_code == 404

    @patch('app.get_db')
    def test_get_nonexistent_user_returns_error_message(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        response = client.get('/api/users/9999')
        data     = json.loads(response.data)
        assert 'error' in data


class TestCreateUser:

    @patch('app.get_db')
    def test_create_user_returns_201(self, mock_db, client, sample_user):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid         = 5
        response = client.post(
            '/api/users',
            data=json.dumps(sample_user),
            content_type='application/json'
        )
        assert response.status_code == 201

    @patch('app.get_db')
    def test_create_user_returns_id(self, mock_db, client, sample_user):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid         = 5
        response = client.post(
            '/api/users',
            data=json.dumps(sample_user),
            content_type='application/json'
        )
        data = json.loads(response.data)
        assert 'id' in data

    def test_create_user_missing_name_returns_400(self, client):
        response = client.post(
            '/api/users',
            data=json.dumps({'email': 'test@test.com', 'password': 'pass'}),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_create_user_missing_email_returns_400(self, client):
        response = client.post(
            '/api/users',
            data=json.dumps({'name': 'Test', 'password': 'pass'}),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_create_user_missing_password_returns_400(self, client):
        response = client.post(
            '/api/users',
            data=json.dumps({'name': 'Test', 'email': 'test@test.com'}),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_create_user_empty_body_returns_400(self, client):
        response = client.post(
            '/api/users',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400

    @patch('app.get_db')
    def test_create_duplicate_email_returns_409(self, mock_db, client, sample_user):
        import mysql.connector
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = mysql.connector.IntegrityError("Duplicate entry")
        response = client.post(
            '/api/users',
            data=json.dumps(sample_user),
            content_type='application/json'
        )
        assert response.status_code == 409

    @patch('app.get_db')
    def test_create_user_password_is_hashed(self, mock_db, client, sample_user):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid         = 5
        client.post(
            '/api/users',
            data=json.dumps(sample_user),
            content_type='application/json'
        )
        call_args = mock_cursor.execute.call_args
        # password stored must not equal plain text
        stored_password = call_args[0][1][2]
        assert stored_password != sample_user['password']


class TestUpdateUser:

    @patch('app.get_db')
    def test_update_user_returns_200(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        response = client.put(
            '/api/users/1',
            data=json.dumps({'name': 'Alice Updated', 'email': 'alice_new@example.com'}),
            content_type='application/json'
        )
        assert response.status_code == 200

    @patch('app.get_db')
    def test_update_user_returns_message(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        response = client.put(
            '/api/users/1',
            data=json.dumps({'name': 'Alice Updated', 'email': 'alice_new@example.com'}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        assert 'message' in data


class TestDeleteUser:

    @patch('app.get_db')
    def test_delete_user_returns_200(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        response = client.delete('/api/users/1')
        assert response.status_code == 200

    @patch('app.get_db')
    def test_delete_user_returns_message(self, mock_db, client):
        mock_conn   = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value          = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        response = client.delete('/api/users/1')
        data     = json.loads(response.data)
        assert 'message' in data
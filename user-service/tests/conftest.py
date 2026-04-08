# user-service/tests/conftest.py
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app

@pytest.fixture
def app():
    flask_app.config.update({
        'TESTING':   True,
        'DEBUG':     False,
    })
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def sample_user():
    return {
        'name':     'Test User',
        'email':    'testuser@example.com',
        'password': 'testpass123'
    }

@pytest.fixture
def sample_user_alt():
    return {
        'name':     'Another User',
        'email':    'another@example.com',
        'password': 'anotherpass456'
    }
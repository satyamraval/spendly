import pytest
from werkzeug.security import check_password_hash

import app as app_module
from database import db


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def _users():
    conn = db.get_db()
    try:
        return conn.execute("SELECT * FROM users").fetchall()
    finally:
        conn.close()


def _post(client, name="Jane Doe", email="jane@example.com", password="password123"):
    return client.post("/register", data={"name": name, "email": email, "password": password})


def test_get_register(client):
    assert client.get("/register").status_code == 200


def test_valid_registration(client):
    resp = _post(client)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login")
    users = _users()
    assert len(users) == 1
    assert users[0]["password_hash"] != "password123"
    assert check_password_hash(users[0]["password_hash"], "password123")


def test_duplicate_email_case_insensitive(client):
    _post(client)
    resp = _post(client, email="JANE@Example.com")
    assert resp.status_code == 200
    assert b"An account with this email already exists." in resp.data
    assert len(_users()) == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"name": "   "},
        {"email": "not-an-email"},
        {"email": "a@b"},
        {"password": "short"},
    ],
)
def test_invalid_input(client, kwargs):
    resp = _post(client, **kwargs)
    assert resp.status_code == 200
    assert b"auth-error" in resp.data
    assert _users() == []


def test_repopulates_fields_not_password(client):
    resp = _post(client, name="Jane", email="jane@example.com", password="short")
    assert b'value="Jane"' in resp.data
    assert b'value="jane@example.com"' in resp.data
    assert b"short" not in resp.data.replace(b"Password must be", b"")

import pytest

import app as app_module
from database import db


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    db.seed_db()
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def _login(client, email="demo@spendly.com", password="demo123"):
    return client.post("/login", data={"email": email, "password": password})


def _user_id(client):
    with client.session_transaction() as sess:
        return sess.get("user_id")


def test_get_login(client):
    assert client.get("/login").status_code == 200


def test_valid_login(client):
    resp = _login(client)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")
    assert _user_id(client) is not None


def test_email_case_insensitive(client):
    assert _login(client, email="  DEMO@Spendly.com ").status_code == 302
    assert _user_id(client) is not None


@pytest.mark.parametrize(
    "kwargs",
    [{"password": "wrongpass"}, {"email": "nobody@example.com"}],
)
def test_invalid_credentials(client, kwargs):
    resp = _login(client, **kwargs)
    assert resp.status_code == 200
    assert b"Invalid email or password." in resp.data
    assert _user_id(client) is None


def test_error_repopulates_email_not_password(client):
    resp = _login(client, password="wrongpass")
    assert b'value="demo@spendly.com"' in resp.data
    assert b"wrongpass" not in resp.data


def test_login_redirects_when_logged_in(client):
    _login(client)
    resp = client.get("/login")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")


def test_navbar_reflects_login_state(client):
    assert b"Sign out" not in client.get("/").data
    assert b"Sign in" in client.get("/").data
    _login(client)
    page = client.get("/profile")
    assert page.status_code == 200
    home = client.get("/")
    assert b"Sign out" in home.data
    assert b"Get started" not in home.data


def test_logout_clears_session(client):
    _login(client)
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")
    assert _user_id(client) is None
    assert b"Sign in" in client.get("/").data


def test_logout_when_logged_out(client):
    assert client.get("/logout").status_code == 302


def test_register_then_login(client):
    client.post(
        "/register",
        data={"name": "New User", "email": "new@example.com", "password": "password123"},
    )
    resp = _login(client, email="new@example.com", password="password123")
    assert resp.status_code == 302
    assert _user_id(client) is not None

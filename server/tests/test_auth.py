def test_register_returns_token_and_user(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Ada Lovelace", "email": "ada@example.com", "username": "ada", "password": "Password123!"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["token"]
    assert body["email"] == "ada@example.com"
    assert body["username"] == "ada"


def test_register_rejects_duplicate_email(client, register_user):
    register_user(email="duplicate@example.com", username="first")

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Someone Else",
            "email": "duplicate@example.com",
            "username": "second",
            "password": "Password123!",
        },
    )

    assert response.status_code == 409


def test_register_rejects_duplicate_username(client, register_user):
    register_user(email="first@example.com", username="taken")

    response = client.post(
        "/api/auth/register",
        json={"name": "Someone Else", "email": "second@example.com", "username": "taken", "password": "Password123!"},
    )

    assert response.status_code == 409


def test_register_rejects_short_password(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Short Pw", "email": "shortpw@example.com", "username": "shortpw", "password": "1234"},
    )

    assert response.status_code == 422


def test_register_rejects_invalid_username(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Bad Username",
            "email": "badusername@example.com",
            "username": "Not Valid!",
            "password": "Password123!",
        },
    )

    assert response.status_code == 422


def test_login_with_correct_password_returns_token(client, register_user):
    register_user(email="grace@example.com", username="grace", password="Password123!")

    response = client.post("/api/auth/login", json={"email": "grace@example.com", "password": "Password123!"})

    assert response.status_code == 200
    assert response.json()["token"]


def test_login_with_wrong_password_is_unauthorized(client, register_user):
    register_user(email="grace2@example.com", username="grace2", password="Password123!")

    response = client.post("/api/auth/login", json={"email": "grace2@example.com", "password": "WrongPassword!"})

    assert response.status_code == 401


def test_login_with_unknown_email_is_unauthorized(client):
    response = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "Password123!"})

    assert response.status_code == 401


def test_protected_endpoint_without_token_is_unauthorized(client):
    response = client.get("/api/me")

    assert response.status_code == 401


def test_protected_endpoint_with_garbage_token_is_unauthorized(client):
    response = client.get("/api/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_register_rejects_reserved_username(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "A", "email": "a@example.com", "username": "Admin", "password": "Password123!"},
    )

    assert response.status_code == 422


def test_register_rejects_overlong_fields(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "n" * 121, "email": "a@example.com", "username": "a" * 51, "password": "Password123!"},
    )

    assert response.status_code == 422


def test_update_me_rejects_overlong_bio(client, register_user, auth_header):
    headers = auth_header(register_user()["token"])

    response = client.patch("/api/me", json={"bio": "b" * 281}, headers=headers)

    assert response.status_code == 422


def test_login_is_rate_limited(client, register_user):
    from app.ratelimit import limiter

    register_user()
    limiter.enabled = True
    statuses = [
        client.post("/api/auth/login", json={"email": "test@example.com", "password": "wrong-password"}).status_code
        for _ in range(11)
    ]

    assert statuses[:10] == [401] * 10
    assert statuses[10] == 429


def test_secret_key_required_outside_dev():
    import pytest
    from pydantic import ValidationError

    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(env="production")
    assert Settings(env="production", secret_key="x" * 40).env == "production"
    assert Settings(env="test").env == "test"

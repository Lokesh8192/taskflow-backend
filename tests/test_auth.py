def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test@1234",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["status"] == "success"
    assert body["message"] == "User registered successfully"
    assert body["data"]["username"] == "testuser"
    assert body["data"]["email"] == "test@example.com"


def test_duplicate_registration(client):
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test@1234",
    }

    first_response = client.post(
        "/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/auth/register",
        json=payload,
    )

    assert second_response.status_code == 409

    body = second_response.json()

    assert body["status"] == "error"


def test_login_user(client, registered_user):
    response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert body["message"] == "User logged in successfully"

    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]


def test_invalid_login(client, registered_user):
    response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": "Wrong@1234",
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["status"] == "error"
    assert body["message"] == "Invalid email or password"


def test_login_twice_generates_distinct_refresh_tokens(client, registered_user, monkeypatch):
    fixed_now = __import__("datetime").datetime(2026, 9, 18, 12, 0, 0, tzinfo=__import__("datetime").timezone.utc)

    class FixedDateTime(__import__("datetime").datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is not None:
                return fixed_now.astimezone(tz)
            return fixed_now

    monkeypatch.setattr("app.core.security.datetime", FixedDateTime)

    first_response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    assert second_response.status_code == 200
    assert first_response.json()["data"]["refresh_token"] != second_response.json()["data"]["refresh_token"]


def test_get_current_user(client, registered_user, auth_headers):
    response = client.get(
        "/users/me",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert body["data"]["email"] == registered_user["email"]


def test_protected_endpoint_without_token(client):
    response = client.get("/users/me")

    assert response.status_code in (401, 403)

    body = response.json()

    assert body["status"] == "error"


def test_refresh_token(client, registered_user):
    login_response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["data"]["refresh_token"]

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert "access_token" in body["data"]


def test_logout_revokes_refresh_token(
    client,
    registered_user,
    auth_headers,
):
    login_response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["data"]["refresh_token"]

    logout_response = client.post(
        "/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
        headers=auth_headers,
    )

    assert logout_response.status_code == 200

    body = logout_response.json()

    assert body["status"] == "success"

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert refresh_response.status_code == 401

    body = refresh_response.json()

    assert body["status"] == "error"
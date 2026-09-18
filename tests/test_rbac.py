def test_regular_user_cannot_access_admin_dashboard(
    client,
    auth_headers,
):
    response = client.get(
        "/admin/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["status"] == "error"


def test_admin_can_access_admin_dashboard(
    client,
    admin_auth_headers,
):
    response = client.get(
        "/admin/dashboard",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
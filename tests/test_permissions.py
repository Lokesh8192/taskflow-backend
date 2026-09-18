from app.models.project_member import ProjectMember
from app.models.user import User


def create_project(client, auth_headers):
    response = client.post(
        "/projects",
        json={
            "name": "Permission Test Project",
            "description": "Testing project permissions",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    return response.json()["data"]


def create_task(client, auth_headers, project_id):
    response = client.post(
        "/tasks",
        json={
            "project_id": project_id,
            "title": "Permission Test Task",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    return response.json()["data"]


def create_second_user(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "seconduser",
            "email": "second@example.com",
            "password": "Test@1234",
        },
    )

    assert response.status_code == 201

    return response.json()["data"]


def login_user(client, email):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "Test@1234",
        },
    )

    assert response.status_code == 200

    token = response.json()["data"]["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def add_project_member(
    db_session,
    project_id,
    user_id,
    role,
):
    member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        role=role,
    )

    db_session.add(member)
    db_session.commit()

    return member


def test_non_member_cannot_view_project_tasks(
    client,
    auth_headers,
    db_session,
):
    project = create_project(
        client,
        auth_headers,
    )

    second_user = create_second_user(client)

    second_headers = login_user(
        client,
        second_user["email"],
    )

    response = client.get(
        f"/tasks?project_id={project['id']}",
        headers=second_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["status"] == "error"


def test_project_member_can_view_project_tasks(
    client,
    auth_headers,
    db_session,
):
    project = create_project(
        client,
        auth_headers,
    )

    second_user = create_second_user(client)

    add_project_member(
        db_session,
        project_id=project["project_id"],
        user_id=second_user["id"],
        role="member",
    )

    create_task(
        client,
        auth_headers,
        project["project_id"],
    )

    second_headers = login_user(
        client,
        second_user["email"],
    )

    response = client.get(
        f"/tasks?project_id={project['project_id']}",
        headers=second_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert len(body["data"]) == 1


def test_viewer_cannot_create_task(
    client,
    auth_headers,
    db_session,
):
    project = create_project(
        client,
        auth_headers,
    )

    second_user = create_second_user(client)

    add_project_member(
        db_session,
        project_id=project["project_id"],
        user_id=second_user["id"],
        role="viewer",
    )

    second_headers = login_user(
        client,
        second_user["email"],
    )

    response = client.post(
        "/tasks",
        json={
            "project_id": project["project_id"],
            "title": "Viewer Task",
        },
        headers=second_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["status"] == "error"


def test_member_cannot_update_another_users_task(
    client,
    auth_headers,
    db_session,
):
    project = create_project(
        client,
        auth_headers,
    )

    task = create_task(
        client,
        auth_headers,
        project["project_id"],
    )

    second_user = create_second_user(client)

    add_project_member(
        db_session,
        project_id=project["project_id"],
        user_id=second_user["id"],
        role="member",
    )

    second_headers = login_user(
        client,
        second_user["email"],
    )

    response = client.put(
        f"/tasks/{task['id']}",
        json={
            "title": "Unauthorized Update",
        },
        headers=second_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["status"] == "error"


def test_manager_can_update_task(
    client,
    auth_headers,
    db_session,
):
    project = create_project(
        client,
        auth_headers,
    )

    task = create_task(
        client,
        auth_headers,
        project["project_id"],
    )

    second_user = create_second_user(client)

    add_project_member(
        db_session,
        project_id=project["project_id"],
        user_id=second_user["id"],
        role="manager",
    )

    second_headers = login_user(
        client,
        second_user["email"],
    )

    response = client.put(
        f"/tasks/{task['id']}",
        json={
            "status": "in_progress",
        },
        headers=second_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert body["data"]["status"] == "in_progress"


def test_assignee_must_be_project_member(
    client,
    auth_headers,
):
    project = create_project(
        client,
        auth_headers,
    )

    second_user = create_second_user(client)

    response = client.post(
        "/tasks",
        json={
            "project_id": project["project_id"],
            "title": "Invalid Assignment",
            "assigned_to": second_user["id"],
        },
        headers=auth_headers,
    )

    assert response.status_code in (400, 403)

    body = response.json()

    assert body["status"] == "error"


def test_filter_tasks_by_status(
    client,
    auth_headers,
):
    project = create_project(
        client,
        auth_headers,
    )

    first_task = create_task(
        client,
        auth_headers,
        project["project_id"],
    )

    second_task = create_task(
        client,
        auth_headers,
        project["project_id"],
    )

    client.put(
        f"/tasks/{second_task['id']}",
        json={
            "status": "done",
        },
        headers=auth_headers,
    )

    response = client.get(
        f"/tasks?project_id={project['project_id']}&status=done",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert len(body["data"]) == 1
    assert body["data"][0]["id"] == second_task["id"]
    assert body["data"][0]["id"] != first_task["id"]


def test_filter_tasks_by_priority(
    client,
    auth_headers,
):
    project = create_project(
        client,
        auth_headers,
    )

    first_task = create_task(
        client,
        auth_headers,
        project["project_id"],
    )

    second_task = create_task(
        client,
        auth_headers,
        project["project_id"],
    )

    client.put(
        f"/tasks/{second_task['id']}",
        json={
            "priority": "high",
        },
        headers=auth_headers,
    )

    response = client.get(
        f"/tasks?project_id={project['project_id']}&priority=high",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert len(body["data"]) == 1
    assert body["data"][0]["id"] == second_task["id"]
    assert body["data"][0]["id"] != first_task["id"]


def test_project_member_can_view_task_history(
    client,
    auth_headers,
    db_session,
):
    project = create_project(
        client,
        auth_headers,
    )

    task = create_task(
        client,
        auth_headers,
        project["id"],
    )

    second_user = create_second_user(client)

    add_project_member(
        db_session,
        project_id=project["id"],
        user_id=second_user["id"],
        role="member",
    )

    second_headers = login_user(
        client,
        second_user["email"],
    )

    response = client.get(
        f"/tasks/{task['id']}/history",
        headers=second_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert len(body["data"]) >= 1


def test_non_member_cannot_view_task_history(
    client,
    auth_headers,
):
    project = create_project(
        client,
        auth_headers,
    )

    task = create_task(
        client,
        auth_headers,
        project["id"],
    )

    second_user = create_second_user(client)

    second_headers = login_user(
        client,
        second_user["email"],
    )

    response = client.get(
        f"/tasks/{task['id']}/history",
        headers=second_headers,
    )

    assert response.status_code == 403

    body = response.json()

    assert body["status"] == "error"
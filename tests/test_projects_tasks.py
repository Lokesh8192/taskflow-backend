def create_project(client, auth_headers):
    response = client.post(
        "/projects",
        json={
            "name": "TaskFlow Project",
            "description": "Project for automated tests",
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
            "title": "Implement authentication",
            "description": "Build JWT authentication",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    return response.json()["data"]


def test_create_project(client, auth_headers):
    project = create_project(
        client,
        auth_headers,
    )

    assert project["name"] == "TaskFlow Project"


def test_get_user_projects(client, auth_headers):
    project = create_project(
        client,
        auth_headers,
    )

    response = client.get(
        "/projects",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert len(body["data"]) == 1
    assert body["data"][0]["id"] == project["id"]


def test_create_task(client, auth_headers):
    project = create_project(
        client,
        auth_headers,
    )

    task = create_task(
        client,
        auth_headers,
        project["id"],
    )

    assert task["title"] == "Implement authentication"
    assert task["project_id"] == project["id"]


def test_get_project_tasks(client, auth_headers):
    project = create_project(
        client,
        auth_headers,
    )

    create_task(
        client,
        auth_headers,
        project["id"],
    )

    create_task(
        client,
        auth_headers,
        project["id"],
    )

    response = client.get(
        f"/tasks?project_id={project['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert len(body["data"]) == 2


def test_update_task_creates_history(
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

    task_id = task["id"]

    update_response = client.put(
        f"/tasks/{task_id}",
        json={
            "status": "in_progress",
            "priority": "high",
        },
        headers=auth_headers,
    )

    assert update_response.status_code == 200

    body = update_response.json()

    assert body["status"] == "success"
    assert body["data"]["status"] == "in_progress"
    assert body["data"]["priority"] == "high"

    history_response = client.get(
        f"/tasks/{task_id}/history",
        headers=auth_headers,
    )

    assert history_response.status_code == 200

    history_body = history_response.json()

    assert history_body["status"] == "success"
    assert len(history_body["data"]) >= 2

    actions = [
        item["action"]
        for item in history_body["data"]
    ]

    assert "CREATED" in actions
    assert "UPDATED" in actions


def test_delete_task(client, auth_headers):
    project = create_project(
        client,
        auth_headers,
    )

    task = create_task(
        client,
        auth_headers,
        project["id"],
    )

    task_id = task["id"]

    delete_response = client.delete(
        f"/tasks/{task_id}",
        headers=auth_headers,
    )

    assert delete_response.status_code == 200

    body = delete_response.json()

    assert body["status"] == "success"

    get_response = client.get(
        f"/tasks/{task_id}",
        headers=auth_headers,
    )

    assert get_response.status_code == 404
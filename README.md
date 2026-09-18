# TaskFlow Backend

TaskFlow is a REST API for collaborative project and task management. It is built with FastAPI, SQLAlchemy, PostgreSQL, Alembic, and JWT authentication.

The API lets users register and sign in, create projects, manage project members, create and track tasks, and review task status changes.


## Features

- JWT access and refresh tokens
- Secure password hashing with bcrypt
- User profile and administrator-only endpoint
- Projects with owner, manager, member, and viewer roles
- Task creation, assignment, filtering, updates, deletion, and audit history
- PostgreSQL migrations through Alembic
- Automated test suite with a separate test database

## Requirements

- Python 3.10 or later
- PostgreSQL

## Setup

1. Create two PostgreSQL databases: one for the application and one for tests.

   ```sql
   CREATE DATABASE taskflow_db;
   CREATE DATABASE taskflow_test;
   ```

2. Create and activate a virtual environment.

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies.

   ```powershell
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env`, then provide your database credentials and a strong secret key.

   ```powershell
   Copy-Item .env.example .env
   ```

   Example configuration:

   ```env
   DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/taskflow_db
   TEST_DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/taskflow_test
   SECRET_KEY=replace-with-a-long-random-secret
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   ```

5. Apply the database migrations.

   ```powershell
   alembic upgrade head
   ```

6. Start the API.

   ```powershell
   uvicorn app.main:app --reload
   ```

The server starts at `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Application Flow

```text
Register -> Login -> Receive access + refresh tokens
                     |
                     v
              Authorization: Bearer <access token>
                     |
                     v
Create project -> Owner is added automatically -> Add project members
                     |
                     v
         Create, assign, filter, and update tasks
                     |
                     v
             Review task history and log out
```

### Typical workflow

1. Register a user with `POST /auth/register`.
2. Log in with `POST /auth/login`. Save the returned access and refresh tokens.
3. Send the access token with every protected request:

   ```http
   Authorization: Bearer <access_token>
   ```

4. Create a project using `POST /projects`. The creator becomes its `owner` automatically.
5. As the owner, add other registered users at `POST /projects/{project_id}/members`.
6. Create project tasks with `POST /tasks`; an assignee must be an active member of that project.
7. List project tasks using `GET /tasks?project_id=1`, optionally filtering by `status`, `priority`, or `assigned_to`.
8. Update a task with `PUT /tasks/{task_id}`. Status, priority, and assignee changes are recorded in task history.
9. Read the history at `GET /tasks/{task_id}/history`.
10. When the access token expires, call `POST /auth/refresh`; call `POST /auth/logout` to revoke the refresh token.

## Permissions

| Role | Project access | Task access |
| --- | --- | --- |
| Owner | Can update/delete the project and add, change, or remove members | Can create, update, and delete any project task |
| Manager | Can view the project and members | Can create, update, and delete any project task |
| Member | Can view the project and members | Can create tasks; can update or delete tasks they created |
| Viewer | Can view the project, members, tasks, and task history | Cannot create, update, or delete tasks |
| System admin | Can access `/admin/dashboard` | Does not bypass project membership rules |

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | API status |
| GET | `/health` | Health check |
| POST | `/auth/register` | Register a user |
| POST | `/auth/login` | Sign in and receive tokens |
| POST | `/auth/refresh` | Create a new access token |
| POST | `/auth/logout` | Revoke a refresh token |
| GET | `/users/me` | Get the authenticated user's profile |
| GET | `/admin/dashboard` | Administrator-only endpoint |
| POST / GET | `/projects` | Create or list accessible projects |
| GET / PUT / DELETE | `/projects/{project_id}` | Read, update, or delete a project |
| POST / GET | `/projects/{project_id}/members` | Add or list project members |
| PATCH / DELETE | `/projects/{project_id}/members/{user_id}` | Change a member's role or remove them |
| POST | `/tasks` | Create a task |
| GET | `/tasks?project_id={id}` | List project tasks |
| GET / PUT / DELETE | `/tasks/{task_id}` | Read, update, or delete a task |
| GET | `/tasks/{task_id}/history` | View task audit history |

## Request Examples

Register:

```json
{
  "username": "alex",
  "email": "alex@example.com",
  "password": "StrongPass@123"
}
```

Create a project:

```json
{
  "name": "Website Launch",
  "description": "Tasks for the public launch"
}
```

Add a member:

```json
{
  "user_id": 2,
  "role": "member"
}
```

Create a task:

```json
{
  "project_id": 1,
  "title": "Prepare launch checklist",
  "description": "Confirm content, infrastructure, and QA",
  "status": "todo",
  "priority": "high",
  "due_date": "2026-10-01",
  "assigned_to": 2
}
```

## Response Format

Successful API responses have a consistent envelope:

```json
{
  "status": "success",
  "message": "Task created successfully",
  "data": {}
}
```

Validation, authentication, authorization, and not-found errors return the appropriate HTTP status code with an error detail.

## Database Migrations

Create a migration after changing SQLAlchemy models:

```powershell
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

## Tests

Ensure `TEST_DATABASE_URL` points to a dedicated database; the test fixture creates tables before the suite, cleans data between tests, and removes the tables afterwards.

```powershell
pytest
```

## Author

**M. Lokeswara Reddy**  
Python Software Developer
# Smart Team Task Manager

> **Course:** Special Topics in Programming (مباحث ویژه در برنامه‌نویسی)  
> **Assignments:** Chapter 3 (Architecture & API) & Chapter 4 (Docker Containerization & CI)  
> **Architecture Pattern:** Modular Monolith  
> **Lead Architect & DevOps:** Habib Eghdami  

---

## 📌 Executive Summary

**Smart Team Task Manager** is a collaborative productivity platform designed for engineering and cross-functional teams. This repository documents the initial baseline architecture and strict RESTful API contracts established during the system design phase.

The architecture adopts the **Modular Monolith** pattern: it combines the simplicity of single-unit deployment and local developer velocity with high domain cohesion, isolated module boundaries, and zero cross-module database coupling.

---

## 🏛️ High-Level System Architecture

### Modular Monolith Architecture Diagram

The system comprises four principal layers:
1. **Front-End Layer:** Single Page Application (SPA) / Mobile Client.
2. **API Gateway & Routing Layer:** Cross-cutting concerns (CORS, Rate Limiting, JWT Authentication).
3. **Modular Monolith Backend Application:**
   - **Auth Module:** Credential authentication, password hashing, JWT generation & verification.
   - **Users Module:** User registration, profile management, and role-based access.
   - **Tasks Module:** Task lifecycle management, status workflows, priorities, and filtering.
   - **Shared Kernel & Infrastructure:** Database abstraction, connection pool, and in-memory event bus.
4. **Database Layer:** Relational persistence (PostgreSQL) ensuring ACID transactional guarantees.

```mermaid
flowchart TD
    subgraph ClientLayer ["Client / Presentation Layer"]
        UI["Web SPA / Frontend Client<br/>(React / Vue / Mobile)"]
        HTTPClient["HTTP Client Service<br/>(Axios / Fetch with JWT Interceptors)"]
        UI --> HTTPClient
    end

    subgraph GatewayLayer ["API Gateway & Middleware Layer"]
        CORS["CORS & Security Headers Middleware"]
        RateLimiter["Rate Limiter & Request Sanitizer"]
        AuthMiddleware["JWT Authentication Guard"]
        
        CORS --> RateLimiter --> AuthMiddleware
    end

    subgraph BackendCore ["Modular Monolith Backend Core"]
        subgraph AuthModule ["Auth Module"]
            AuthController["AuthController<br/>• POST /api/users/login"]
            AuthService["AuthService<br/>(JWT Token Engine & Bcrypt / Argon2)"]
            AuthController --> AuthService
        end

        subgraph UsersModule ["Users Module"]
            UsersController["UsersController<br/>• POST /api/users/register<br/>• GET /api/users/me"]
            UsersService["UsersService<br/>(User Entity Management & Profile)"]
            UsersRepo["UsersRepository"]
            
            UsersController --> UsersService --> UsersRepo
        end

        subgraph TasksModule ["Tasks Module"]
            TasksController["TasksController<br/>• /api/tasks CRUD"]
            TasksService["TasksService<br/>(Task Domain Rules & State Engine)"]
            TasksRepo["TasksRepository"]
            
            TasksController --> TasksService --> TasksRepo
        end

        subgraph SharedKernel ["Shared Kernel & Common Infrastructure"]
            EventBus["In-Memory Domain Event Bus"]
            DBContext["Database Pool & Unit of Work"]
        end
    end

    subgraph PersistenceLayer ["Persistence Layer (PostgreSQL)"]
        DB[("Relational Database")]
        UsersTable[("users table")]
        TasksTable[("tasks table")]
        DB --- UsersTable
        DB --- TasksTable
    end

    %% Network & Request Routing
    HTTPClient -->|"HTTPS / REST (JSON)"| CORS
    AuthMiddleware -->|"Route /api/users/login"| AuthController
    AuthMiddleware -->|"Route /api/users/register, /me"| UsersController
    AuthMiddleware -->|"Route /api/tasks/*"| TasksController

    %% Inter-Module In-Memory Calls
    AuthService -.->|"Query User by Email"| UsersService
    TasksService -.->|"Verify Assignee Validity"| UsersService
    TasksService -.->|"Publish Domain Events"| EventBus

    %% Persistence Access
    UsersRepo --> DBContext
    TasksRepo --> DBContext
    DBContext -->|"SQL Connection Pool & Transactions"| DB
```

---

## 📡 RESTful API Contract Specification

All endpoints adhere to strict REST conventions: resource-oriented paths, plural nouns, standard HTTP verbs (`GET`, `POST`, `PUT`, `DELETE`), and canonical status codes.

*Full specification with complete schemas is also available at [`docs/api-contract.md`](docs/api-contract.md).*

### Summary Table

| Resource | Method | Path | Description | HTTP Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| **Users** | `POST` | `/api/users/register` | Register new user | `201 Created`, `400 Bad Request`, `409 Conflict` |
| **Users** | `POST` | `/api/users/login` | Authenticate & generate JWT | `200 OK`, `400 Bad Request`, `401 Unauthorized` |
| **Users** | `GET` | `/api/users/me` | Get authenticated user profile | `200 OK`, `401 Unauthorized` |
| **Tasks** | `GET` | `/api/tasks` | List tasks with query params | `200 OK`, `401 Unauthorized` |
| **Tasks** | `POST` | `/api/tasks` | Create task | `201 Created`, `400 Bad Request`, `401 Unauthorized` |
| **Tasks** | `GET` | `/api/tasks/:id` | Get task details by ID | `200 OK`, `401 Unauthorized`, `404 Not Found` |
| **Tasks** | `PUT` | `/api/tasks/:id` | Full update of task by ID | `200 OK`, `400 Bad Request`, `401 Unauthorized`, `404 Not Found` |
| **Tasks** | `DELETE` | `/api/tasks/:id` | Remove task by ID | `204 No Content`, `401 Unauthorized`, `404 Not Found` |

---

### 1. Users Resource Endpoints

#### 1.1 `POST /api/users/register`
Creates a new user profile with securely hashed credentials.

- **Status Codes:**
  - `201 Created`: Registration successful.
  - `400 Bad Request`: Validation failure (e.g. malformed email or weak password).
  - `409 Conflict`: An account with this email address already exists.

##### Sample Request Payload:
```json
{
  "name": "Habib Eghdami",
  "email": "habib@example.com",
  "password": "SecurePassword#2026"
}
```

##### Sample Response Payload (`201 Created`):
```json
{
  "success": true,
  "data": {
    "id": "u-45120",
    "name": "Habib Eghdami",
    "email": "habib@example.com",
    "role": "MEMBER",
    "createdAt": "2026-11-12T19:05:00.000Z"
  }
}
```

---

#### 1.2 `POST /api/users/login`
Authenticates user credentials and issues a signed JWT access token.

- **Status Codes:**
  - `200 OK`: Authentication succeeded; JWT returned.
  - `400 Bad Request`: Missing email or password in request body.
  - `401 Unauthorized`: Invalid credentials provided.

##### Sample Request Payload:
```json
{
  "email": "habib@example.com",
  "password": "SecurePassword#2026"
}
```

##### Sample Response Payload (`200 OK`):
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1LTQ1MTIwIiwiZW1haWwiOiJoYWJpYkBleGFtcGxlLmNvbSIsInJvbGUiOiJNRU1CRVIiLCJpYXQiOjE3OTQ1MTM5MDAsImV4cCI6MTc5NDUxNzUwMH0.signatureSampleKey",
    "tokenType": "Bearer",
    "expiresIn": 3600,
    "user": {
      "id": "u-45120",
      "name": "Habib Eghdami",
      "email": "habib@example.com",
      "role": "MEMBER"
    }
  }
}
```

---

#### 1.3 `GET /api/users/me`
Retrieves identity and permissions for the currently authenticated user.

- **Header:** `Authorization: Bearer <accessToken>`
- **Status Codes:**
  - `200 OK`: Profile details returned.
  - `401 Unauthorized`: Token is missing, invalid, or expired.

##### Sample Response Payload (`200 OK`):
```json
{
  "success": true,
  "data": {
    "id": "u-45120",
    "name": "Habib Eghdami",
    "email": "habib@example.com",
    "role": "MEMBER",
    "teams": [
      {
        "id": "team-01",
        "name": "Core Engineering",
        "role": "TEAM_LEAD"
      }
    ],
    "createdAt": "2026-11-12T19:05:00.000Z",
    "updatedAt": "2026-11-12T19:15:00.000Z"
  }
}
```

---

### 2. Tasks Resource Endpoints

#### 2.1 `GET /api/tasks`
Lists tasks with filtering and pagination.

- **Header:** `Authorization: Bearer <accessToken>`
- **Query Parameters:** `page`, `limit`, `status`, `priority`, `assignedTo`, `search`
- **Status Codes:**
  - `200 OK`: Task list successfully returned.
  - `401 Unauthorized`: Unauthenticated request.

##### Sample Response Payload (`200 OK`):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "t-1001",
        "title": "Design Initial API Contract and Architecture",
        "description": "Formulate OpenAPI specification and Modular Monolith diagram for Chapter 3 assignment.",
        "status": "IN_PROGRESS",
        "priority": "HIGH",
        "assignedTo": {
          "id": "u-45120",
          "name": "Habib Eghdami",
          "email": "habib@example.com"
        },
        "dueDate": "2026-11-15T23:59:59.000Z",
        "createdAt": "2026-11-12T19:10:00.000Z",
        "updatedAt": "2026-11-12T19:20:00.000Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "pageSize": 20,
      "totalItems": 1,
      "totalPages": 1,
      "hasNextPage": false,
      "hasPreviousPage": false
    }
  }
}
```

---

#### 2.2 `POST /api/tasks`
Creates a new task in the workspace.

- **Header:** `Authorization: Bearer <accessToken>`
- **Status Codes:**
  - `201 Created`: Task created.
  - `400 Bad Request`: Missing title or invalid parameters.
  - `401 Unauthorized`: Authentication missing or failed.

##### Sample Request Payload:
```json
{
  "title": "Setup Continuous Integration Pipeline",
  "description": "Configure GitHub Actions workflow for linting, unit tests, and automatic deployment.",
  "priority": "HIGH",
  "status": "TODO",
  "assignedToId": "u-45120",
  "dueDate": "2026-11-20T18:00:00.000Z"
}
```

##### Sample Response Payload (`201 Created`):
```json
{
  "success": true,
  "data": {
    "id": "t-1002",
    "title": "Setup Continuous Integration Pipeline",
    "description": "Configure GitHub Actions workflow for linting, unit tests, and automatic deployment.",
    "status": "TODO",
    "priority": "HIGH",
    "createdBy": "u-45120",
    "assignedTo": {
      "id": "u-45120",
      "name": "Habib Eghdami"
    },
    "dueDate": "2026-11-20T18:00:00.000Z",
    "createdAt": "2026-11-12T19:22:00.000Z",
    "updatedAt": "2026-11-12T19:22:00.000Z"
  }
}
```

---

#### 2.3 `GET /api/tasks/:id`
Retrieves detailed information of an individual task.

- **Header:** `Authorization: Bearer <accessToken>`
- **Status Codes:**
  - `200 OK`: Task found and returned.
  - `401 Unauthorized`: Unauthenticated request.
  - `404 Not Found`: Task does not exist.

##### Sample Response Payload (`200 OK`):
```json
{
  "success": true,
  "data": {
    "id": "t-1001",
    "title": "Design Initial API Contract and Architecture",
    "description": "Formulate OpenAPI specification and Modular Monolith diagram for Chapter 3 assignment.",
    "status": "IN_PROGRESS",
    "priority": "HIGH",
    "assignedTo": {
      "id": "u-45120",
      "name": "Habib Eghdami",
      "email": "habib@example.com"
    },
    "createdBy": {
      "id": "u-45120",
      "name": "Habib Eghdami"
    },
    "dueDate": "2026-11-15T23:59:59.000Z",
    "createdAt": "2026-11-12T19:10:00.000Z",
    "updatedAt": "2026-11-12T19:20:00.000Z"
  }
}
```

---

#### 2.4 `PUT /api/tasks/:id`
Replaces or fully updates an existing task.

- **Header:** `Authorization: Bearer <accessToken>`
- **Status Codes:**
  - `200 OK`: Task updated.
  - `400 Bad Request`: Validation failure.
  - `401 Unauthorized`: Authentication missing or failed.
  - `404 Not Found`: Task does not exist.

##### Sample Request Payload:
```json
{
  "title": "Design Initial API Contract and Architecture (Completed)",
  "description": "Formulate OpenAPI specification and Modular Monolith diagram for Chapter 3 assignment with review.",
  "status": "DONE",
  "priority": "URGENT",
  "assignedToId": "u-45120",
  "dueDate": "2026-11-13T12:00:00.000Z"
}
```

##### Sample Response Payload (`200 OK`):
```json
{
  "success": true,
  "data": {
    "id": "t-1001",
    "title": "Design Initial API Contract and Architecture (Completed)",
    "description": "Formulate OpenAPI specification and Modular Monolith diagram for Chapter 3 assignment with review.",
    "status": "DONE",
    "priority": "URGENT",
    "assignedTo": {
      "id": "u-45120",
      "name": "Habib Eghdami"
    },
    "dueDate": "2026-11-13T12:00:00.000Z",
    "createdAt": "2026-11-12T19:10:00.000Z",
    "updatedAt": "2026-11-12T19:30:00.000Z"
  }
}
```

---

#### 2.5 `DELETE /api/tasks/:id`
Deletes a task from the system.

- **Header:** `Authorization: Bearer <accessToken>`
- **Status Codes:**
  - `204 No Content`: Task successfully deleted; empty body returned.
  - `401 Unauthorized`: Unauthenticated request.
  - `404 Not Found`: Task does not exist.

##### Sample Response (`204 No Content`):
*(Empty response body)*

---

## 🔒 Security & Data Integrity

- **Password Storage:** Salted and hashed using Argon2id or Bcrypt (`work factor = 12`).
- **Token Security:** Short-lived JWT Access Tokens (1 hour) signed using `RS256` or `HS256` with strong secret rotation.
- **Input Validation:** Strict DTO schema validation on all inputs before reaching domain service layers.
- **Data Protection:** All endpoints enforce TLS 1.3 in transit and column-level encryption for sensitive tokens.

---

## 🐳 Docker Containerization (Chapter 4)

The backend service is fully containerized using a hardened, non-root `python:3.11-slim` container image adhering to production Docker best practices.

### 1. Build the Docker Image
To package and build the container image locally:

```bash
docker build -t smart-task-api .
```

### 2. Run Container with Port Mapping
Run the container in detached mode with host port `8000` mapped to container port `8000`:

```bash
docker run -d -p 8000:8000 --name smart-task-app smart-task-api
```

- `-d`: Run container in background (detached mode).
- `-p 8000:8000`: Maps port `8000` on the host to port `8000` inside the container.
- `--name smart-task-app`: Assigns a memorable container identifier.
- `smart-task-api`: The target image name tagged during the build stage.

### 3. Verify Container Status & Logs

Check that the container is up and running healthy:
```bash
docker ps
```

Stream and verify runtime application logs:
```bash
docker logs smart-task-app
```

Follow logs in real-time:
```bash
docker logs -f smart-task-app
```

Verify the API health check endpoint:
```bash
curl http://localhost:8000/api/health
```

### 4. Stop and Remove Container
When stopping and cleaning up the running container instance:
```bash
docker stop smart-task-app
docker rm smart-task-app
```

---

## 🚀 Continuous Integration (GitHub Actions)

A GitHub Actions workflow is established in [`.github/workflows/docker-check.yml`](.github/workflows/docker-check.yml) to automatically verify the Docker build process on every push and pull request targeting the `main` branch.

- **Trigger:** Push / Pull Request to `main`
- **Runner:** `ubuntu-latest`
- **Pipeline Stages:**
  1. Repository Checkout (`actions/checkout@v4`)
  2. Docker Buildx Setup (`docker/setup-buildx-action@v3`)
  3. Container Build Verification (`docker build -t smart-task-api .`)


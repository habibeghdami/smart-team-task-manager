# Smart Team Task Manager — API Contract & Architecture Specification

> **Course:** Special Topics in Programming (مباحث ویژه) — Chapter 3 Assignment  
> **Project:** Smart Team Task Manager  
> **Architecture Style:** Modular Monolith  
> **Document Version:** `1.0.0`  
> **Status:** Approved / Initial Baseline  

---

## 1. System Architecture Overview

The **Smart Team Task Manager** is designed following a **Modular Monolith** architectural pattern. This pattern combines the operational simplicity and single-deployment velocity of a monolith with the strict domain boundaries and encapsulation of microservices.

### 1.1 Architectural Pillars

1. **Presentation / Client Layer:**  
   Single Page Application (SPA) / Mobile Client communicating with the backend exclusively over standard HTTPS using RESTful JSON APIs.
2. **API Gateway & Routing Layer:**  
   Handles cross-cutting concerns before requests hit domain modules: CORS negotiation, rate limiting, request validation, and stateless JWT authentication extraction.
3. **Modular Monolith Core Application:**  
   Organized into discrete, highly cohesive modules with explicit boundaries:
   - **Auth Module:** Handles credential verification, cryptographic password hashing (Argon2id/Bcrypt), and JWT issuance/revocation checks.
   - **Users Module:** Manages user identity, account lifecycle, user profile retrieval, and organizational role assignments.
   - **Tasks Module:** Core business domain managing task states (`TODO`, `IN_PROGRESS`, `IN_REVIEW`, `DONE`), priorities (`LOW`, `MEDIUM`, `HIGH`, `URGENT`), assignment, due dates, and filtering.
   - **Shared Kernel / Common Infrastructure:** Shared cross-domain utilities, error formatting, database connection pooling, transactions, and an in-process asynchronous domain event bus.
4. **Persistence Layer:**  
   Relational database management system (PostgreSQL) guaranteeing ACID compliance for task state transitions and user credentials, with modular schema separation.

---

### 1.2 System Architecture Diagram (GitHub-Compatible Mermaid)

```mermaid
flowchart TD
    subgraph ClientLayer ["Client / Presentation Layer"]
        UI["Web SPA / Frontend Client<br/>(React / Vue / Mobile)"]
        HTTPClient["HTTP Service / API Client<br/>(Axios / Fetch with JWT Interceptor)"]
        UI --> HTTPClient
    end

    subgraph GatewayLayer ["API Gateway & Middleware Layer"]
        CORS["CORS & Security Headers Middleware"]
        RateLimiter["Rate Limiting & Request Sanitizer"]
        AuthMiddleware["JWT Authentication & Context Guard"]
        
        CORS --> RateLimiter --> AuthMiddleware
    end

    subgraph BackendCore ["Modular Monolith Backend Application"]
        subgraph AuthModule ["Auth Module"]
            AuthController["AuthController<br/>• POST /api/users/login"]
            AuthService["AuthService<br/>(Token Issuance & Password Verification)"]
            AuthController --> AuthService
        end

        subgraph UsersModule ["Users Module"]
            UsersController["UsersController<br/>• POST /api/users/register<br/>• GET /api/users/me"]
            UsersService["UsersService<br/>(User Lifecycle & Profile Management)"]
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
            DBContext["Database Pool & Unit of Work / ORM"]
        end
    end

    subgraph PersistenceLayer ["Persistence Layer (PostgreSQL)"]
        DB[("Relational Database")]
        UsersTable[("users table")]
        TasksTable[("tasks table")]
        DB --- UsersTable
        DB --- TasksTable
    end

    %% Network & Request Flow
    HTTPClient -->|"HTTPS / REST (JSON)"| CORS
    AuthMiddleware -->|"Route /api/users/login"| AuthController
    AuthMiddleware -->|"Route /api/users/register, /me"| UsersController
    AuthMiddleware -->|"Route /api/tasks/*"| TasksController

    %% Inter-Module Communication (In-Process)
    AuthService -.->|"In-Memory Query (Find by Email)"| UsersService
    TasksService -.->|"Verify Assignee / Permissions"| UsersService
    TasksService -.->|"Publish TaskCreated / StatusChanged"| EventBus

    %% Data Access
    UsersRepo --> DBContext
    TasksRepo --> DBContext
    DBContext -->|"SQL Connection Pool & Transactions"| DB
```

---

## 2. API Contract Specification

### 2.1 General Conventions

- **Base URL:** `https://api.smart-taskmanager.local/api` (or `/api` in relative routing)
- **Data Exchange Format:** `application/json; charset=utf-8`
- **Authentication Scheme:** `Authorization: Bearer <JWT_ACCESS_TOKEN>`
- **Character Encoding:** UTF-8 throughout all request and response bodies.
- **Date/Time Standard:** ISO 8601 (`YYYY-MM-DDTHH:mm:ss.sssZ`) UTC timestamps.

### 2.2 Standard Error Response Envelope (RFC 7807 Compliant)

All non-`2xx` HTTP status responses return a consistent error body:

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested task with ID 't-98234' could not be found.",
    "details": [
      {
        "field": "id",
        "issue": "Invalid identifier or task does not exist"
      }
    ],
    "timestamp": "2026-11-12T19:00:00.000Z",
    "path": "/api/tasks/t-98234"
  }
}
```

---

## 3. Users & Authentication Endpoints

### 3.1 Register New User
Creates a new user account with hashed password and initial role assignment.

- **Endpoint:** `POST /api/users/register`
- **Access:** Public (No authentication required)
- **HTTP Status Codes:**
  - `201 Created`: User successfully registered.
  - `400 Bad Request`: Payload validation failed (invalid email, weak password).
  - `409 Conflict`: User already exists with the provided email.

#### Request Body
```json
{
  "name": "Habib Eghdami",
  "email": "habib@example.com",
  "password": "SecurePassword#2026"
}
```

#### Response Body (`201 Created`)
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

### 3.2 User Authentication / Login
Authenticates user credentials and issues a signed JWT access token.

- **Endpoint:** `POST /api/users/login`
- **Access:** Public (No authentication required)
- **HTTP Status Codes:**
  - `200 OK`: Authentication successful, token returned.
  - `400 Bad Request`: Missing email or password.
  - `401 Unauthorized`: Invalid credentials (incorrect password or user does not exist).

#### Request Body
```json
{
  "email": "habib@example.com",
  "password": "SecurePassword#2026"
}
```

#### Response Body (`200 OK`)
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

### 3.3 Get Current User Profile
Retrieves profile and organizational membership details of the authenticated user.

- **Endpoint:** `GET /api/users/me`
- **Access:** Protected (`Bearer <JWT>` required)
- **HTTP Status Codes:**
  - `200 OK`: Profile details returned.
  - `401 Unauthorized`: Missing, expired, or invalid token.

#### Headers
```http
Authorization: Bearer <accessToken>
```

#### Response Body (`200 OK`)
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

## 4. Tasks Endpoints

### 4.1 List Tasks
Retrieves a paginated list of tasks filtered by status, priority, or assignee.

- **Endpoint:** `GET /api/tasks`
- **Access:** Protected (`Bearer <JWT>` required)
- **Query Parameters:**
  - `page` *(optional, integer, default: 1)*: Current page number.
  - `limit` *(optional, integer, default: 20, max: 100)*: Items per page.
  - `status` *(optional, enum: `TODO`, `IN_PROGRESS`, `IN_REVIEW`, `DONE`)*: Filter by task status.
  - `priority` *(optional, enum: `LOW`, `MEDIUM`, `HIGH`, `URGENT`)*: Filter by priority.
  - `assignedTo` *(optional, string)*: Filter by assignee user ID.
  - `search` *(optional, string)*: Text search in title and description.
- **HTTP Status Codes:**
  - `200 OK`: Tasks retrieved successfully.
  - `401 Unauthorized`: Missing or invalid authorization token.

#### Response Body (`200 OK`)
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

### 4.2 Create Task
Creates a new task within the team workspace.

- **Endpoint:** `POST /api/tasks`
- **Access:** Protected (`Bearer <JWT>` required)
- **HTTP Status Codes:**
  - `201 Created`: Task created successfully.
  - `400 Bad Request`: Missing mandatory fields (`title`), invalid dates, or invalid enum value.
  - `401 Unauthorized`: Missing or invalid authorization token.

#### Request Body
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

#### Response Body (`201 Created`)
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

### 4.3 Get Task Details by ID
Retrieves comprehensive details for a specific task.

- **Endpoint:** `GET /api/tasks/:id`
- **Access:** Protected (`Bearer <JWT>` required)
- **Path Parameters:**
  - `id` *(required, string)*: Unique identifier of the task.
- **HTTP Status Codes:**
  - `200 OK`: Task details returned.
  - `401 Unauthorized`: Missing or invalid token.
  - `404 Not Found`: Task with the specified ID does not exist.

#### Response Body (`200 OK`)
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

### 4.4 Update Task by ID
Updates existing task attributes (title, status, priority, assignee, due date).

- **Endpoint:** `PUT /api/tasks/:id`
- **Access:** Protected (`Bearer <JWT>` required)
- **Path Parameters:**
  - `id` *(required, string)*: Unique identifier of the task to update.
- **HTTP Status Codes:**
  - `200 OK`: Task updated successfully.
  - `400 Bad Request`: Invalid payload parameters.
  - `401 Unauthorized`: Missing or invalid token.
  - `404 Not Found`: Task does not exist.

#### Request Body
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

#### Response Body (`200 OK`)
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

### 4.5 Delete Task by ID
Removes a task from the system permanently.

- **Endpoint:** `DELETE /api/tasks/:id`
- **Access:** Protected (`Bearer <JWT>` required)
- **Path Parameters:**
  - `id` *(required, string)*: Unique identifier of the task.
- **HTTP Status Codes:**
  - `204 No Content`: Task successfully deleted (no payload body returned).
  - `401 Unauthorized`: Missing or invalid token.
  - `404 Not Found`: Task does not exist.

#### Response Body (`204 No Content`)
*(Empty response body)*

---

## 5. Summary Matrix of Endpoints

| Resource | Method | Path | Description | Expected Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| **Users** | `POST` | `/api/users/register` | Register new user account | `201`, `400`, `409` |
| **Users** | `POST` | `/api/users/login` | Authenticate user & issue JWT | `200`, `400`, `401` |
| **Users** | `GET` | `/api/users/me` | Fetch authenticated user profile | `200`, `401` |
| **Tasks** | `GET` | `/api/tasks` | List tasks with query parameters | `200`, `401` |
| **Tasks** | `POST` | `/api/tasks` | Create a new task | `201`, `400`, `401` |
| **Tasks** | `GET` | `/api/tasks/:id` | Fetch task details by ID | `200`, `401`, `404` |
| **Tasks** | `PUT` | `/api/tasks/:id` | Replace / Update full task | `200`, `400`, `401`, `404` |
| **Tasks** | `DELETE` | `/api/tasks/:id` | Delete task by ID | `204`, `401`, `404` |

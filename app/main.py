"""
Smart Team Task Manager API Server
Compliant with Chapter 3 RESTful API Contract & Modular Monolith architecture.
"""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, status, Query, Response
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(
    title="Smart Team Task Manager API",
    description="Backend API service for collaborative task and project management",
    version="1.0.0",
)


# ==========================================
# Domain Schemas & DTOs
# ==========================================
class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: str = Field("MEDIUM", pattern="^(LOW|MEDIUM|HIGH|URGENT)$")
    status: str = Field("TODO", pattern="^(TODO|IN_PROGRESS|IN_REVIEW|DONE)$")
    assignedToId: Optional[str] = None
    dueDate: Optional[str] = None


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|URGENT)$")
    status: Optional[str] = Field(None, pattern="^(TODO|IN_PROGRESS|IN_REVIEW|DONE)$")
    assignedToId: Optional[str] = None
    dueDate: Optional[str] = None


# ==========================================
# In-Memory Datastores (Simulation)
# ==========================================
users_db = [
    {
        "id": "u-45120",
        "name": "Habib Eghdami",
        "email": "habib@example.com",
        "role": "MEMBER",
        "createdAt": "2026-11-12T19:05:00.000Z",
    }
]

tasks_db = [
    {
        "id": "t-1001",
        "title": "Design Initial API Contract and Architecture",
        "description": "Formulate OpenAPI specification and Modular Monolith diagram for Chapter 3 assignment.",
        "status": "DONE",
        "priority": "HIGH",
        "assignedTo": {
            "id": "u-45120",
            "name": "Habib Eghdami",
            "email": "habib@example.com",
        },
        "dueDate": "2026-11-15T23:59:59.000Z",
        "createdAt": "2026-11-12T19:10:00.000Z",
        "updatedAt": "2026-11-12T19:20:00.000Z",
    }
]


# ==========================================
# Health Check & Root
# ==========================================
@app.get("/")
def root():
    return {
        "service": "Smart Team Task Manager API",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "UP",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "smart-team-task-manager",
    }


# ==========================================
# Users Resource
# ==========================================
@app.post("/api/users/register", status_code=status.HTTP_201_CREATED)
def register(user: UserRegisterRequest):
    for u in users_db:
        if u["email"].lower() == user.email.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )
    new_user = {
        "id": f"u-{len(users_db) + 45120}",
        "name": user.name,
        "email": user.email,
        "role": "MEMBER",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    users_db.append(new_user)
    return {"success": True, "data": new_user}


@app.post("/api/users/login", status_code=status.HTTP_200_OK)
def login(creds: UserLoginRequest):
    user = next((u for u in users_db if u["email"].lower() == creds.email.lower()), None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return {
        "success": True,
        "data": {
            "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummyJwtSignature2026",
            "tokenType": "Bearer",
            "expiresIn": 3600,
            "user": user,
        },
    }


@app.get("/api/users/me", status_code=status.HTTP_200_OK)
def get_current_user():
    return {
        "success": True,
        "data": {
            **users_db[0],
            "teams": [{"id": "team-01", "name": "Core Engineering", "role": "TEAM_LEAD"}],
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        },
    }


# ==========================================
# Tasks Resource
# ==========================================
@app.get("/api/tasks", status_code=status.HTTP_200_OK)
def list_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    results = tasks_db
    if status_filter:
        results = [t for t in results if t["status"] == status_filter]
    if priority:
        results = [t for t in results if t["priority"] == priority]

    return {
        "success": True,
        "data": {
            "items": results,
            "pagination": {
                "currentPage": page,
                "pageSize": limit,
                "totalItems": len(results),
                "totalPages": 1,
                "hasNextPage": False,
                "hasPreviousPage": False,
            },
        },
    }


@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreateRequest):
    new_task = {
        "id": f"t-{len(tasks_db) + 1001}",
        "title": payload.title,
        "description": payload.description,
        "status": payload.status,
        "priority": payload.priority,
        "createdBy": "u-45120",
        "assignedTo": {"id": payload.assignedToId or "u-45120", "name": "Habib Eghdami"},
        "dueDate": payload.dueDate,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    tasks_db.append(new_task)
    return {"success": True, "data": new_task}


@app.get("/api/tasks/{task_id}", status_code=status.HTTP_200_OK)
def get_task(task_id: str):
    task = next((t for t in tasks_db if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return {"success": True, "data": task}


@app.put("/api/tasks/{task_id}", status_code=status.HTTP_200_OK)
def update_task(task_id: str, payload: TaskUpdateRequest):
    task = next((t for t in tasks_db if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if payload.title is not None:
        task["title"] = payload.title
    if payload.description is not None:
        task["description"] = payload.description
    if payload.status is not None:
        task["status"] = payload.status
    if payload.priority is not None:
        task["priority"] = payload.priority
    if payload.dueDate is not None:
        task["dueDate"] = payload.dueDate
    task["updatedAt"] = datetime.now(timezone.utc).isoformat()
    return {"success": True, "data": task}


@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str):
    global tasks_db
    task = next((t for t in tasks_db if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    tasks_db = [t for t in tasks_db if t["id"] != task_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)

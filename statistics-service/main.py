
from fastapi import FastAPI, HTTPException
import requests
import os

app = FastAPI(title="Student Study Planner - Statistics Service")

TASK_SERVICE_URL = os.getenv(
    "TASK_SERVICE_URL",
    "http://127.0.0.1:8000"
)


@app.get("/")
def home():
    return {"message": "Welcome to the Statistics Service"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/statistics")
def get_statistics():
    try:
        response = requests.get(
            f"{TASK_SERVICE_URL}/tasks",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()

        tasks = data["tasks"]
        total = len(tasks)
        completed = sum(1 for task in tasks if task["completed"])
        pending = total - completed

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": pending
        }

    except requests.RequestException:
        raise HTTPException(
            status_code=503,
            detail="Task Service is currently unavailable"
        )

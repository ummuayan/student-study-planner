
import os
import time
import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Student Study Planner - Task Service")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://planner:plannerpass@localhost:5432/studyplanner"
)


class TaskCreate(BaseModel):
    title: str
    description: str = ""


def get_connection():
    return psycopg.connect(DATABASE_URL)


@app.on_event("startup")
def startup():
    for attempt in range(10):
        try:
            with get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL DEFAULT '',
                        completed BOOLEAN NOT NULL DEFAULT FALSE
                    )
                """)
            return
        except psycopg.OperationalError:
            if attempt == 9:
                raise
            time.sleep(2)


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Student Study Planner</title>
      <style>
        body { font-family: Arial, sans-serif; max-width: 750px;
          margin: 40px auto; padding: 20px; background: #f4f7fb; }
        h1 { color: #17365d; }
        .card { background: white; padding: 22px; border-radius: 12px;
          margin-bottom: 20px; box-shadow: 0 2px 8px #ddd; }
        input, textarea, button { box-sizing: border-box; width: 100%;
          padding: 11px; margin: 7px 0; }
        button { background: #1769aa; color: white; border: 0;
          border-radius: 6px; cursor: pointer; }
        .task { padding: 12px 0; border-bottom: 1px solid #ddd; }
        .done { color: #27823b; text-decoration: line-through; }
        .actions { display: flex; gap: 8px; }
        .actions button { width: auto; }
        #message { color: #b00020; }
      </style>
    </head>
    <body>
      <h1>Student Study Planner</h1>
      <p>Organise your study tasks and track your progress.</p>

      <div class="card">
        <h2>Add a study task</h2>
        <form id="task-form">
          <input id="title" placeholder="Task title" required>
          <textarea id="description" placeholder="Description"></textarea>
          <button type="submit">Add task</button>
        </form>
        <p id="message"></p>
      </div>

      <div class="card">
        <h2>My tasks</h2>
        <p id="stats">Loading tasks...</p>
        <div id="tasks"></div>
      </div>

      <p><a href="/docs">Open REST API documentation</a></p>

      <script>
        const message = document.getElementById("message");

        async function loadTasks() {
          try {
            const response = await fetch("/tasks");
            if (!response.ok) throw new Error("Could not load tasks");
            const data = await response.json();
            const tasks = data.tasks;
            const completed = tasks.filter(t => t.completed).length;

            document.getElementById("stats").textContent =
              `${tasks.length} tasks · ${completed} completed · ${tasks.length - completed} pending`;

            const list = document.getElementById("tasks");
            list.replaceChildren();

            tasks.forEach(task => {
              const item = document.createElement("div");
              item.className = "task";

              const heading = document.createElement("strong");
              heading.textContent = task.title;
              if (task.completed) heading.className = "done";
              item.appendChild(heading);

              const description = document.createElement("p");
              description.textContent = task.description || "";
              item.appendChild(description);

              const actions = document.createElement("div");
              actions.className = "actions";

              if (!task.completed) {
                const complete = document.createElement("button");
                complete.textContent = "Mark complete";
                complete.onclick = async () => {
                  await fetch(`/tasks/${task.id}/complete`, { method: "PATCH" });
                  loadTasks();
                };
                actions.appendChild(complete);
              }

              const remove = document.createElement("button");
              remove.textContent = "Delete";
              remove.onclick = async () => {
                await fetch(`/tasks/${task.id}`, { method: "DELETE" });
                loadTasks();
              };
              actions.appendChild(remove);
              item.appendChild(actions);
              list.appendChild(item);
            });
          } catch (error) {
            message.textContent = error.message;
          }
        }

        document.getElementById("task-form").onsubmit = async event => {
          event.preventDefault();
          message.textContent = "";

          const response = await fetch("/tasks", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              title: document.getElementById("title").value,
              description: document.getElementById("description").value
            })
          });

          if (!response.ok) {
            message.textContent = "Could not add task. Please try again.";
            return;
          }

          event.target.reset();
          loadTasks();
        };

        loadTasks();
      </script>
    </body>
    </html>
    """


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/tasks")
def get_tasks():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, description, completed FROM tasks ORDER BY id"
        ).fetchall()

    return {
        "tasks": [
            {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "completed": row[3]
            }
            for row in rows
        ]
    }


@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO tasks (title, description)
            VALUES (%s, %s)
            RETURNING id, title, description, completed
            """,
            (task.title, task.description)
        ).fetchone()

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "completed": row[3]
    }


@app.patch("/tasks/{task_id}/complete")
def complete_task(task_id: int):
    with get_connection() as conn:
        row = conn.execute(
            """
            UPDATE tasks SET completed = TRUE
            WHERE id = %s
            RETURNING id, title, description, completed
            """,
            (task_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "completed": row[3]
    }


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    with get_connection() as conn:
        row = conn.execute(
            """
            DELETE FROM tasks WHERE id = %s
            RETURNING id, title, description, completed
            """,
            (task_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task deleted", "id": row[0]}

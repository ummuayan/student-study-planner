
# Student Study Planner

## Project Description

The Student Study Planner is a web application that helps students organise their study tasks, track deadlines, and monitor their progress.

## Project Goals

- Create, view, update, and delete study tasks.
- Track completed and pending tasks.
- Store task information in a persistent database.
- Use REST APIs to enable communication between microservices.
- Deploy the application using Docker and Kubernetes.

## Architecture

The application will contain two microservices:

1. **Task Service:** Manages study tasks through a REST API.
2. **Statistics Service:** Calculates study progress by communicating with the Task Service REST API.

PostgreSQL will store the task data. Kubernetes will deploy and manage the application components.

## Technologies

- Python and FastAPI
- PostgreSQL
- Docker
- Kubernetes
- HTML, CSS, and JavaScript

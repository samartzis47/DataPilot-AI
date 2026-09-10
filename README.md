# DataPilot-AI

[![CI](https://github.com/samartzis47/DataPilot-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/samartzis47/DataPilot-AI/actions/workflows/ci.yml)

A production-oriented backend project focused on AI engineering, data engineering and modern software development practices.

The goal of DataPilot-AI is to simulate the architecture, development workflow and quality standards of a real-world production system.

---

## Features

- FastAPI backend
- PostgreSQL database
- Docker Compose
- Centralized API routing
- Environment-based configuration
- Automated testing with Pytest
- Clean project structure
- Git & GitHub workflow

---

## Continuous Integration

Every push and pull request verifies backend tests, Alembic migrations, frontend TypeScript, ESLint, frontend tests, the production frontend build, and Docker image builds.

---

## Technology Stack

- Python
- FastAPI
- PostgreSQL
- Docker
- Pytest
- Pydantic Settings
- Git

---

## Project Structure

```
DataPilot-AI/
│
├── backend/        # FastAPI application
├── frontend/       # Frontend (future)
├── docs/           # Documentation
├── compose.yaml    # Docker services
└── .gitignore
```

---

## Project Roadmap

### Completed

- [x] FastAPI setup
- [x] PostgreSQL integration
- [x] Docker Compose
- [x] Health API
- [x] Configuration management
- [x] Automated tests

### Next Steps

- [ ] SQLAlchemy models
- [ ] Database migrations
- [ ] JWT Authentication
- [ ] User Management
- [ ] Role Based Access Control
- [ ] AI Service Layer
- [ ] CI/CD
- [ ] Monitoring & Logging

---

## Development Principles

This project follows modern software engineering practices:

- Clean Architecture
- Maintainable code
- Automated testing
- Production-first mindset
- Documentation-first approach

---

## Current Status

🚧 Active Development

The project is continuously evolving with new backend features, authentication, AI capabilities and production-ready infrastructure.

## Local Docker Stack

### Prerequisites

- Docker Desktop with Docker Compose
- A local copy of this repository

Create the backend environment file once from the secrets-free template:

```powershell
Copy-Item backend/.env.example backend/.env
```

Update the local database password in `backend/.env` if needed. Keep `OPENAI_API_KEY` empty to use the deterministic rules provider.

Start the complete frontend, API, worker, PostgreSQL and Redis stack with one command:

```powershell
docker compose up -d --build
```

Check service status and logs:

```powershell
docker compose -f compose.yaml ps
docker compose logs -f frontend api worker
```

Frontend: http://127.0.0.1:3000

Swagger UI: http://127.0.0.1:8000/docs

API health: http://127.0.0.1:8000/health

Frontend health: http://127.0.0.1:3000/healthz

The frontend uses the same-origin `/api` path. Nginx removes that prefix and proxies the request to the internal `api:8000` service, so the browser never needs to know the Docker hostname.

Stop the stack with:

```powershell
docker compose down
```

This stops the services without deleting the PostgreSQL or Redis volumes. Do not add `-v` unless you intentionally want to remove those volumes.

---

## Author

Efthymis Samartzis

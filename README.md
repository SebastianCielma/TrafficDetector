---
title: Traffic AI Pro
emoji: 🚦
colorFrom: blue
colorTo: red
sdk: docker
app_port: 7860
pinned: false
---

[![CI/CD Pipeline](https://github.com/sebastiancielma/TrafficDetector/actions/workflows/ci.yaml/badge.svg)](https://github.com/sebastiancielma/TrafficDetector/actions/workflows/ci.yaml)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)
![Type Checking](https://img.shields.io/badge/types-pyright-green)

# Traffic Detection System �

A production-grade traffic detection system built with modern Python architecture, featuring asynchronous processing, distributed task queuing, and cloud-native storage.

##  Key Engineering Decisions

- **Distributed System**: Decoupling the API (FastAPI) from the Worker (Celery) allows for independent scaling and prevents server blocking during heavy AI operations.
- **Async-Sync Bridge**: Implementation of the asyncio loop pattern within synchronous Celery workers, enabling the reuse of asynchronous services (DB, S3) in background tasks.
- **Stateless Compute**: The container does not store state. Task data resides in PostgreSQL, and files in Object Storage (S3). The container can be restarted at any time without data loss.
- **Type Safety**: The codebase is 100% typed (Python 3.12) and verified by Pyright in strict mode.

## Tech Stack

| Category | Technologies | Description |
|----------|-------------|-------------|
| **Backend** | Python 3.12, FastAPI | Asynchronous application core |
| **AI / ML** | Ultralytics YOLOv8, Supervision | Object detection and visualization |
| **Database** | SQLModel (SQLAlchemy 2.0), AsyncPG | Modern ORM and the fastest async Postgres driver |
| **Queuing** | Celery, Redis | Background task management (traffic spike resilience) |
| **Storage** | aioboto3, Cloudflare R2 | Asynchronous S3-compatible file handling |
| **Frontend** | Gradio | User interface integrated with the API |
| **DevOps** | Docker, uv, GitHub Actions | Dependency management and deployment automation |

## CI/CD Process (GitHub Actions)

The project features a fully automated software delivery pipeline.

### Continuous Integration (CI)
Triggered on every push and PR:
- **Linting**: Ruff checks code style and imports
- **Type Checking**: Pyright verifies static type correctness
- **Testing**: Pytest runs a suite of unit and integration tests (utilizing S3 and Database Mocks)

### Continuous Deployment (CD)
Triggered only after successful CI on the main branch:
- Automatically pushes clean code to the Hugging Face Spaces repository
- Triggers Docker container rebuild on production

##  Quality Assurance & Testing

The project maintains a high standard of code quality with high coverage. Tests are categorized into:

- **Unit Tests (API)**: Endpoint testing with service mocking
- **Service Tests**: Business logic testing (Workflow, FileService) isolated from I/O (aiofiles/boto3 mocking)
- **Integration Tests (DB)**: Database operation testing using SQLite In-Memory

To run tests locally:
```bash
uv run pytest -v
```

## Development Roadmap

The project is actively developed. Planned features:

- [x] **Phase 1**: MVP & CI/CD (Architecture, Docker, Automation)
- [x] **Phase 2**: Persistence (SQL Database, Cloud Storage, Redis Queue)
- [ ] **Phase 3**: Observability (Sentry implementation and structured logging for error monitoring) - _In Progress_
- [ ] **Phase 4**: Advanced AI (ByteTrack algorithm implementation for vehicle tracking and counting)
- [ ] **Phase 5**: API Gateway (Rate limiting and API key endpoint protection)

## Local Setup (Docker)

**Prerequisites**: Docker and a `.env` file with cloud credentials (Neon, Upstash, Cloudflare).
```bash
# 1. Build the image
docker build -t traffic-app .

# 2. Run container (passing .env file)
docker run --env-file .env -p 7860:7860 traffic-app
```

The application will be available at: **http://localhost:7860**


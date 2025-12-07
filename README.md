# X Clone Backend API

FastAPI-based REST API for the X Clone (Twitter clone) application.

## Features

- 🔐 **Authentication**: JWT-based authentication with access and refresh tokens
- 📧 **Email Verification**: Required email verification before login
- 🔑 **Password Reset**: Secure password reset via email
- 👤 **User Management**: User profiles and account management
- 🐘 **PostgreSQL**: Async database with SQLAlchemy 2.0
- 📝 **Migrations**: Database migrations with Alembic

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with asyncpg
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Auth**: JWT (python-jose) + bcrypt
- **Email**: FastAPI-Mail
- **Validation**: Pydantic v2

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL
- UV package manager

### Installation

1. **Install dependencies using UV:**

   ```bash
   cd server
   uv sync
   ```

2. **Configure environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Create the database:**

   ```sql
   CREATE DATABASE x_clone;
   ```

4. **Run database migrations:**

   ```bash
   uv run alembic upgrade head
   ```

5. **Start the development server:**
   ```bash
   uv run uvicorn app.main:app --reload --port 8000
   ```

## API Documentation

When running in debug mode, API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication

| Method | Endpoint                           | Description                   |
| ------ | ---------------------------------- | ----------------------------- |
| POST   | `/api/v1/auth/register`            | Register new user             |
| POST   | `/api/v1/auth/login`               | Login and get tokens          |
| POST   | `/api/v1/auth/refresh`             | Refresh access token          |
| POST   | `/api/v1/auth/logout`              | Logout (revoke refresh token) |
| POST   | `/api/v1/auth/verify-email`        | Verify email address          |
| POST   | `/api/v1/auth/resend-verification` | Resend verification email     |
| POST   | `/api/v1/auth/forgot-password`     | Request password reset        |
| POST   | `/api/v1/auth/reset-password`      | Reset password                |

### Users

| Method | Endpoint           | Description              |
| ------ | ------------------ | ------------------------ |
| GET    | `/api/v1/users/me` | Get current user profile |

## Project Structure

```
server/
├── alembic/                  # Database migrations
├── app/
│   ├── api/                  # API routes
│   │   └── v1/
│   │       └── endpoints/    # Route handlers
│   ├── core/                 # Core utilities
│   ├── db/                   # Database configuration
│   ├── models/               # SQLAlchemy models
│   ├── repositories/         # Data access layer
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   └── main.py               # Application entry point
├── .env                      # Environment variables
├── alembic.ini               # Alembic configuration
└── pyproject.toml            # Project dependencies
```

## Development

### Create a new migration

```bash
uv run alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations

```bash
uv run alembic upgrade head
```

### Rollback migration

```bash
uv run alembic downgrade -1
```

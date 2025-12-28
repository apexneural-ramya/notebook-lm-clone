# NotebookLM Backend API

FastAPI backend with Apex authentication for the NotebookLM application.

## Setup

1. **Install dependencies:**
   ```bash
   cd backend
   uv sync
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database and JWT settings
   ```

3. **Set up PostgreSQL database:**
   ```bash
   # Create database
   createdb notebooklm
   # Or using psql:
   psql -U postgres
   CREATE DATABASE notebooklm;
   ```

4. **Run migrations:**
   ```bash
   cd backend
   # Make sure DATABASE_URL in .env uses postgresql+asyncpg:// (not postgresql://)
   uv run alembic revision --autogenerate -m "create_users_table"
   uv run alembic upgrade head
   ```
   
   **Troubleshooting:**
   - If you get "psycopg2 is not async" error:
     - Verify `DATABASE_URL` uses `postgresql+asyncpg://` format
     - Check asyncpg is installed: `uv run python -c "import asyncpg; print('OK')"`
     - Uninstall conflicting psycopg2: `uv pip uninstall psycopg2 psycopg2-binary`

5. **Run the server:**
   ```bash
   # Use uv run to ensure dependencies are available
   uv run python run.py
   # Server will use BACKEND_HOST and BACKEND_PORT from backend/.env
   # Default: http://localhost:8000
   ```
   
   **Important:** Always use `uv run` when running commands to ensure the virtual environment is used.

## API Endpoints

- `POST /api/auth/signup` - Create new user account
- `POST /api/auth/login` - Login and get tokens
- `GET /api/auth/me` - Get current user info (requires auth)
- `POST /api/auth/refresh` - Refresh access token

## Testing

```bash
# Replace BACKEND_URL with your actual backend URL from backend/.env
# (BACKEND_HOST:BACKEND_PORT, e.g., http://localhost:8000)

# Signup
curl -X POST ${BACKEND_URL:-http://localhost:8000}/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234","full_name":"Test User"}'

# Login
curl -X POST ${BACKEND_URL:-http://localhost:8000}/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234"}'

# Get current user
curl -X GET ${BACKEND_URL:-http://localhost:8000}/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```


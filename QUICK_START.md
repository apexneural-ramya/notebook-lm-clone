# Quick Start Guide - Running the Project

This guide shows you how to run the NotebookLM project and change port numbers.

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL database
- `uv` package manager (install: https://astral.sh/uv)

## Step-by-Step Setup

### 1. Install Backend Dependencies

```bash
cd backend
uv sync
```

### 2. Configure Backend Environment

```bash
cd backend
cp .env.example .env
# Edit backend/.env with your settings
```

**Required variables in `backend/.env`:**
- `DATABASE_URL` or database components (DATABASE_HOST, DATABASE_PORT, etc.) - PostgreSQL connection
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- `OPEN_ROUTER_API_KEY` - For LLM access
- `BACKEND_HOST` - Server host (default: 0.0.0.0)
- `BACKEND_PORT` - Server port (default: 8000)
- `FRONTEND_URL` - Frontend URL for CORS (required, no default)
- `CORS_ORIGINS` - Optional, comma-separated CORS origins (auto-generated from FRONTEND_URL if not set)

### 3. Set Up Database

```bash
# Create PostgreSQL database
createdb notebooklm

# Run migrations
cd backend
uv run alembic upgrade head
```

### 4. Configure Frontend Environment

```bash
cd frontend
cp .env.example .env.local
# Edit frontend/.env.local
```

**Required variables in `frontend/.env.local`:**
- `NEXT_PUBLIC_API_URL` - Backend API URL (e.g., http://localhost:8000)

### 5. Install Frontend Dependencies

```bash
cd frontend
npm install
```

## Running the Project

### Start Backend (Terminal 1)

```bash
cd backend
uv run python run.py
```

Backend will run on: `http://localhost:8000` (or your configured port)

### Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

Frontend will run on: `http://localhost:3000` (or your configured port)

### Access the Application

Open `http://localhost:3000` in your browser and login/signup.

---

## Changing Port Numbers

### Change Backend Port

1. **Edit `backend/.env`:**
   ```env
   BACKEND_PORT=8007
   BACKEND_API_URL=http://localhost:8007
   ```

2. **Update `frontend/.env.local`:**
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8007
   ```

3. **Restart the backend server:**
   ```bash
   cd backend
   uv run python run.py
   ```

### Change Frontend Port

**Option 1: Command Line (Recommended)**
```bash
cd frontend
npm run dev -- -p 3001
```

**Option 2: Environment Variable**
```bash
cd frontend
PORT=3001 npm run dev
```

**Option 3: Update package.json**
```json
"scripts": {
  "dev": "next dev -p 3001"
}
```

**After changing frontend port, update `backend/.env`:**
```env
FRONTEND_URL=http://localhost:3001
```

### Example: Change Both Ports

**Backend on port 8007, Frontend on port 3001:**

1. **`backend/.env`:**
   ```env
   BACKEND_PORT=8007
   BACKEND_API_URL=http://localhost:8007
   FRONTEND_URL=http://localhost:3001
   ```

2. **`frontend/.env.local`:**
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8007
   ```

3. **Start backend:**
   ```bash
   cd backend
   uv run python run.py
   ```

4. **Start frontend:**
   ```bash
   cd frontend
   npm run dev -- -p 3001
   ```

5. **Access:** `http://localhost:3001`

---

## Port Configuration Summary

| Service | Default Port | Config File | Environment Variable |
|---------|-------------|-------------|---------------------|
| **Backend** | 8000 | `backend/.env` | `BACKEND_PORT` |
| **Frontend** | 3000 | Command line or `package.json` | `PORT` (optional) |

### Important Notes

1. **When changing backend port:**
   - Update `BACKEND_PORT` in `backend/.env`
   - Update `BACKEND_API_URL` in `backend/.env`
   - Update `NEXT_PUBLIC_API_URL` in `frontend/.env.local`

2. **When changing frontend port:**
   - Use `npm run dev -- -p PORT_NUMBER`
   - Update `FRONTEND_URL` in `backend/.env`

3. **Always restart both services** after changing ports.

---

## Troubleshooting

### Port Already in Use

If you get "port already in use" error:

**Backend:**
- Change `BACKEND_PORT` in `backend/.env`
- Update `BACKEND_API_URL` accordingly

**Frontend:**
- Use a different port: `npm run dev -- -p 3001`
- Update `FRONTEND_URL` in `backend/.env`

### CORS Errors

If you see CORS errors:
- Make sure `FRONTEND_URL` in `backend/.env` matches your frontend URL
- Check `CORS_ORIGINS` in `backend/.env` includes your frontend URL

### Connection Errors

If frontend can't connect to backend:
- Verify `NEXT_PUBLIC_API_URL` in `frontend/.env.local` matches backend URL
- Check backend is running: `http://localhost:8000/health` (or your port)
- Verify `BACKEND_API_URL` in `backend/.env` matches the running backend

---

## Quick Reference

### Default Ports
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

### Environment Files
- Backend: `backend/.env`
- Frontend: `frontend/.env.local`

### Start Commands
```bash
# Backend
cd backend && uv run python run.py

# Frontend
cd frontend && npm run dev
```

### Change Ports
```bash
# Backend: Edit backend/.env
BACKEND_PORT=8007

# Frontend: Use command line
npm run dev -- -p 3001
```


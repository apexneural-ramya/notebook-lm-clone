# Production Deployment Guide for Dokploy

This guide covers deploying the NotebookLM application to production using Docker files in Dokploy.

## Pre-Deployment Checklist

### ✅ Code Status
- ✅ Landing page fixed (no redirect issues)
- ✅ Dockerfiles optimized (multi-stage builds)
- ✅ Health checks configured
- ✅ Non-root users configured
- ✅ Cache headers configured

### ⚠️ Required Configuration Before Deployment

## 1. Backend Environment Variables

Create `.env` file in `backend/` directory with production values:

```env
# Database (REQUIRED)
DATABASE_URL=postgresql+asyncpg://user:password@your-db-host:5432/notebooklm
# OR if using docker-compose with postgres service:
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/notebooklm

# JWT Security (CRITICAL - Change in production!)
JWT_SECRET_KEY=your-very-strong-random-secret-key-min-32-characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (REQUIRED - Set your production domain)
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend URL (REQUIRED for production)
FRONTEND_URL=https://yourdomain.com

# API Keys (REQUIRED)
OPENROUTER_API_KEY=your-openrouter-api-key

# Qdrant (if using external Qdrant)
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=your-qdrant-api-key
```

### 🔒 Security Requirements

1. **JWT_SECRET_KEY**: 
   - Must be a strong, random string (minimum 32 characters)
   - Generate with: `openssl rand -hex 32`
   - Never commit to git

2. **CORS Origins**:
   - Must include your production frontend domain
   - Format: `https://yourdomain.com,https://www.yourdomain.com`
   - No trailing slashes

3. **Database**:
   - Use strong passwords
   - Use SSL/TLS in production
   - Consider connection pooling

## 2. Frontend Environment Variables

Create `.env` file in `frontend/` directory:

```env
# Backend API URL (REQUIRED - Use your production backend URL)
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
# OR if backend is on same domain with different path:
# NEXT_PUBLIC_API_URL=https://yourdomain.com/api

# Port (optional, defaults to 3000)
FRONTEND_PORT=3000
```

### ⚠️ Important Notes

- `NEXT_PUBLIC_API_URL` is baked into the build at build time
- Must be set correctly before building the Docker image
- If using Dokploy, set this as a build argument

## 3. Dokploy Configuration

### Backend Service

1. **Build Context**: `backend/`
2. **Dockerfile**: `backend/Dockerfile`
3. **Build Arguments**: None required (uses .env file)
4. **Environment Variables**: Load from `backend/.env` file
5. **Port**: Map to `8000` (or your configured `BACKEND_PORT`)
6. **Health Check**: Already configured in Dockerfile

### Frontend Service

1. **Build Context**: `frontend/`
2. **Dockerfile**: `frontend/Dockerfile`
3. **Build Arguments**:
   - `NEXT_PUBLIC_API_URL` (REQUIRED) - Your production backend URL
4. **Environment Variables**: 
   - `FRONTEND_PORT` (optional, defaults to 3000)
5. **Port**: Map to `3000` (or your configured `FRONTEND_PORT`)
6. **Health Check**: Already configured in Dockerfile

### Example Dokploy Build Command

**Backend:**
```bash
# No build args needed - uses .env file
docker build -t notebooklm-backend ./backend
```

**Frontend:**
```bash
# Must pass NEXT_PUBLIC_API_URL as build arg
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://api.yourdomain.com \
  -t notebooklm-frontend \
  ./frontend
```

## 4. Database Setup

### Option A: External PostgreSQL (Recommended for Production)

1. Use managed PostgreSQL service (AWS RDS, DigitalOcean, etc.)
2. Set `DATABASE_URL` in backend `.env` to point to external database
3. Ensure network connectivity from Dokploy to database

### Option B: PostgreSQL in Dokploy

1. Deploy PostgreSQL container separately
2. Use service name in `DATABASE_URL` (e.g., `postgresql+asyncpg://user:pass@postgres:5432/notebooklm`)
3. Ensure both services are on same Docker network

## 5. Required Services

Your production deployment needs:

1. **Backend API** (FastAPI)
   - Port: 8000 (or configured port)
   - Health: `/health` endpoint

2. **Frontend** (Next.js)
   - Port: 3000 (or configured port)
   - Health: Built-in health check

3. **PostgreSQL Database**
   - Port: 5432
   - Required for user authentication and data storage

4. **Qdrant** (Optional - for vector search)
   - Port: 6333
   - Can use external Qdrant service

## 6. Reverse Proxy / Load Balancer

For production, use a reverse proxy (nginx, Traefik, Caddy) with:

- **HTTPS/SSL certificates** (Let's Encrypt recommended)
- **Domain routing**:
  - Frontend: `https://yourdomain.com`
  - Backend API: `https://api.yourdomain.com` or `https://yourdomain.com/api`

### Example nginx Configuration

```nginx
# Frontend
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Backend API
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 7. Post-Deployment Steps

1. **Run Database Migrations**:
   ```bash
   docker exec notebooklm-backend uv run alembic upgrade head
   ```

2. **Verify Health Checks**:
   - Backend: `https://api.yourdomain.com/health`
   - Frontend: `https://yourdomain.com/`

3. **Test Authentication**:
   - Create a test account
   - Verify login/logout works
   - Check JWT token generation

4. **Monitor Logs**:
   ```bash
   docker logs -f notebooklm-backend
   docker logs -f notebooklm-frontend
   ```

## 8. Security Checklist

- [ ] Strong `JWT_SECRET_KEY` set (32+ characters, random)
- [ ] `BACKEND_CORS_ORIGINS` includes only your production domain
- [ ] Database uses strong password
- [ ] HTTPS/SSL enabled via reverse proxy
- [ ] `.env` files not committed to git
- [ ] API keys stored securely (not in code)
- [ ] Database backups configured
- [ ] Health checks working
- [ ] Non-root users in containers (already configured)

## 9. Troubleshooting

### Backend Issues
- Check logs: `docker logs notebooklm-backend`
- Verify database connection
- Check CORS configuration matches frontend domain
- Verify JWT_SECRET_KEY is set

### Frontend Issues
- Check logs: `docker logs notebooklm-frontend`
- Verify `NEXT_PUBLIC_API_URL` is correct (check build logs)
- Check browser console for API connection errors
- Verify CORS allows your frontend domain

### Database Issues
- Verify `DATABASE_URL` format is correct
- Check network connectivity
- Verify database credentials
- Check if database is accessible from container

## 10. Dokploy-Specific Notes

When deploying in Dokploy:

1. **Build Arguments**: Set `NEXT_PUBLIC_API_URL` in Dokploy's build settings for frontend
2. **Environment Variables**: Use Dokploy's environment variable management
3. **Volumes**: Configure persistent volumes for:
   - `backend/logs`
   - `backend/outputs`
   - `backend/uploads`
   - `backend/qdrant_db` (if using local Qdrant)
4. **Networks**: Ensure services can communicate (same Docker network)
5. **Health Checks**: Dokploy should use the health check endpoints

## Ready for Production?

✅ All environment variables configured
✅ Strong JWT_SECRET_KEY set
✅ CORS origins configured for production domain
✅ Database connection configured
✅ HTTPS/SSL configured (via reverse proxy)
✅ Health checks working
✅ Logs accessible

Once all items are checked, you're ready to deploy!


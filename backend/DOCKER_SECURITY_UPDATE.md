# Docker Security Update - Required Actions

## ⚠️ Important Changes

After the security update, the Docker setup **requires** `DATABASE_PASSWORD` and `JWT_SECRET_KEY` to be set in your `.env` file. Default passwords have been removed for security.

## What Changed

1. **No default passwords**: `docker-compose.yml` no longer has default values for:
   - `DATABASE_PASSWORD`
   - `JWT_SECRET_KEY`

2. **Application validation**: The backend will fail to start if these values are missing or empty.

3. **Documentation updated**: All examples now use placeholders like `CHANGE_THIS_PASSWORD`.

## Required Actions

### 1. Update Your `.env` File

Make sure `backend/.env` contains **actual values** (not placeholders):

```env
# Database - REPLACE WITH YOUR ACTUAL PASSWORD
DATABASE_PASSWORD=your-actual-strong-password-here

# JWT - REPLACE WITH A GENERATED SECRET
# Generate with: openssl rand -hex 32
JWT_SECRET_KEY=your-generated-secret-key-here
```

### 2. Generate a Strong JWT Secret

**Linux/Mac:**
```bash
openssl rand -hex 32
```

**Windows PowerShell:**
```powershell
# Generate random hex string
-join ((48..57) + (97..102) | Get-Random -Count 64 | ForEach-Object {[char]$_})
```

Or use an online generator: https://www.grc.com/passwords.htm

### 3. Validate Your `.env` File (Optional)

Before running Docker, validate your configuration:

**Linux/Mac:**
```bash
cd backend
chmod +x validate-env.sh
./validate-env.sh
```

**Windows PowerShell:**
```powershell
cd backend
.\validate-env.ps1
```

### 4. Update DATABASE_URL

If you're using `DATABASE_URL` directly, make sure it includes your actual password:

```env
# For docker-compose (using postgres service)
DATABASE_URL=postgresql+asyncpg://postgres:your-actual-password@postgres:5432/notebooklm

# For standalone Docker (connecting to host PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:your-actual-password@host.docker.internal:5432/notebooklm
```

## Running Docker

### With Docker Compose

```bash
cd backend
docker-compose up -d
```

**If you see errors about missing passwords:**
1. Check that your `.env` file exists in `backend/` directory
2. Verify `DATABASE_PASSWORD` and `JWT_SECRET_KEY` are set
3. Make sure they're not using placeholder values

### With Dockerfile Only

```bash
cd backend

# Linux/Mac
./run-docker.sh

# Windows PowerShell
.\run-docker.ps1
```

## Troubleshooting

### Error: "DATABASE_PASSWORD must be set in .env file"

**Solution:** Add `DATABASE_PASSWORD=your-password` to `backend/.env`

### Error: "JWT_SECRET_KEY must be set in .env file"

**Solution:** 
1. Generate a secret: `openssl rand -hex 32`
2. Add `JWT_SECRET_KEY=generated-secret` to `backend/.env`

### Error: PostgreSQL container fails to start

**Solution:** Make sure `DATABASE_PASSWORD` is set in `.env` - PostgreSQL requires a password.

### Error: Backend container exits immediately

**Solution:** Check logs:
```bash
docker-compose logs backend
```

Look for `ValueError` messages about missing `DATABASE_PASSWORD` or `JWT_SECRET_KEY`.

## Security Best Practices

1. ✅ **Never commit `.env` files** to Git
2. ✅ **Use strong passwords** (minimum 12 characters, mix of letters, numbers, symbols)
3. ✅ **Use unique JWT secrets** (64+ character random hex strings)
4. ✅ **Rotate secrets regularly** in production
5. ✅ **Use different secrets** for development and production

## Example `.env` File

```env
# Database Configuration
DATABASE_USER=postgres
DATABASE_PASSWORD=MyStr0ng!P@ssw0rd
DATABASE_NAME=notebooklm
DATABASE_PORT=5432

# For docker-compose
DATABASE_URL=postgresql+asyncpg://postgres:MyStr0ng!P@ssw0rd@postgres:5432/notebooklm

# JWT Configuration
JWT_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Server
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend URL
FRONTEND_URL=http://localhost:3000

# API Keys
OPENROUTER_API_KEY=your-actual-api-key-here
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=your-qdrant-api-key-here
```

## Need Help?

If you encounter issues:
1. Check `backend/.env` exists and has all required variables
2. Run the validation script: `./validate-env.sh` or `.\validate-env.ps1`
3. Check Docker logs: `docker-compose logs backend`
4. Verify no placeholder values remain (like `CHANGE_THIS_PASSWORD`)


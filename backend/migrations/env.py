"""Alembic environment configuration for Apex"""
import asyncio
import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Add backend directory to Python path
# Get the directory containing this env.py file (migrations/)
migrations_dir = Path(__file__).parent
# Get the backend directory (parent of migrations/)
backend_dir = migrations_dir.parent
# Ensure backend directory is in Python path
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Import config and models AFTER adding to path
from app.config import DATABASE_URL

# Import Apex Base and User model - CRITICAL for migrations
# Must import AFTER adding backend to path
from apex import Base
from app.models.user import User  # Import to register with Base

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
# Only call fileConfig if config_file_name is available
# This prevents errors when the module is imported outside of Alembic context
try:
    if config.config_file_name is not None:
        fileConfig(config.config_file_name)
except (AttributeError, KeyError):
    # If config_file_name is not available, skip fileConfig
    # This can happen when the module is imported directly
    pass

# Set target metadata to Apex's Base
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = DATABASE_URL.replace("+asyncpg", "")  # Use sync URL for offline
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    """Run migrations with connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Ensure we're using asyncpg, not psycopg2
    db_url = DATABASE_URL
    
    # Force asyncpg driver - replace any postgresql:// with postgresql+asyncpg://
    if "postgresql+asyncpg://" not in db_url:
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
        else:
            # If it has a different driver, replace it
            import re
            db_url = re.sub(r'postgresql\+[^:]+://', 'postgresql+asyncpg://', db_url)
    
    # Verify asyncpg is available
    try:
        import asyncpg
    except ImportError:
        raise ImportError(
            "asyncpg is required but not installed. Install it with: uv pip install asyncpg"
        )
    
    # Create engine with explicit asyncpg driver
    connectable = create_async_engine(db_url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

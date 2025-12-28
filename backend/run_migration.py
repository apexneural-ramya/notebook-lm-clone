"""Helper script to run Alembic migrations using Python API
This works around the 'Failed to canonicalize script path' issue on Windows
when using the alembic CLI directly.
"""
import sys
import os
from pathlib import Path
from alembic import command
from alembic.config import Config

# Ensure we're in the backend directory
backend_dir = Path(__file__).parent
os.chdir(backend_dir)

# Load Alembic config
config = Config('alembic.ini')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific command
        cmd = sys.argv[1]
        if cmd == "upgrade":
            revision = sys.argv[2] if len(sys.argv) > 2 else "head"
            command.upgrade(config, revision)
        elif cmd == "downgrade":
            revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
            command.downgrade(config, revision)
        elif cmd == "current":
            command.current(config, verbose=True)
        elif cmd == "history":
            command.history(config, verbose=True)
        elif cmd == "revision":
            message = sys.argv[2] if len(sys.argv) > 2 else "auto migration"
            autogenerate = "--autogenerate" in sys.argv
            command.revision(config, message=message, autogenerate=autogenerate)
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python run_migration.py [upgrade|downgrade|current|history|revision] [revision]")
    else:
        # Default: upgrade to head
        print("Running: alembic upgrade head")
        command.upgrade(config, "head")


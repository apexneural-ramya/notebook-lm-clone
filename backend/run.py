"""Run the FastAPI backend server"""
import uvicorn
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend directory only
backend_dir = Path(__file__).parent
env_file = backend_dir / '.env'
load_dotenv(dotenv_path=env_file)

# Add backend directory to path (for src imports)
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Import config after path is set
from app.config import BACKEND_HOST, BACKEND_PORT

if __name__ == "__main__":
    uvicorn.run(
        "app.api:app",
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        reload=True,
        log_level="info"
    )


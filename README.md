# NotebookLM Clone
In this project we build an open-source implementation of Google's NotebookLM that grounds AI responses in your documents with accurate citations. Built with modern AI technologies including RAG (Retrieval-Augmented Generation), vector databases, and conversational memory.

> **📖 Quick Start Guide**: See [QUICK_START.md](QUICK_START.md) for step-by-step instructions on running the project and changing port numbers.

## Overview

NotebookLM Clone is a document-grounded AI assistant that allows you to:

- Upload and process multiple document types (PDF, text, audio, YouTube videos, web pages)
- Ask questions and receive cited, verifiable answers
- Maintain conversational context intelligently across sessions
- Generate AI podcasts from your documents
- Clean and intuitive web interface inspired by NotebookLM

### Tech Stack

- PyMuPDF for complex document parsing with PDF, TXT and Markdown support.
- AssemblyAI for audio transcription with speaker diarization.
- Firecrawl for scraping and content extraction from websites.
- Qdrant vector database for efficient semantic search.
- Zep's temporal knowledge graphs as the memory layer.
- Coqui TTS as the open source Text-to-Speech model.
- Next.js 14 (React/TypeScript) for the modern web frontend.
- FastAPI for the backend API.

### NotebookLM UI

- NotebookLM-Inspired Design: Three-Panel Layout with sources panel, chat interface, and studio features.
- Add your documents via the Upload panel.
- Interactive source citations with detailed metadata in chat responses.
- Podcast Generation: AI podcast creation with script generation and multi speaker TTS

## Architecture

![architecture-diagram](assets/flow-diagram.jpg)

## Data Flow
1. User Authentication: Secure signup/login with JWT token management
2. Document Ingestion: User uploads PDF, audio, video, text, or web URL
3. Processing: Content extracted with metadata (page numbers, timestamps, and other metadata)
4. Chunking: Text split into overlapping segments preserving context
5. Embedding: Chunks converted to vector representations
6. Storage: Vectors stored in Qdrant with citation metadata and user_id for isolation
7. Query: User asks question → Query embedded → Semantic search (filtered by user_id)
8. Retrieval: Top-k relevant chunks retrieved with metadata (user-specific)
9. Generation: Agent generates cited response using memory
10. Memory: Conversation saved to Zep for future context
11. Source Management: Users can view, delete, and manage their uploaded sources

## Installation & Setup

**Prerequisites**: Python 3.11, PostgreSQL database

**Note for Windows Users**: Due to Windows path issues with HuggingFace model caching, the embedding model will be automatically downloaded to a `backend/.embedding_model` directory on first run. This is a one-time download (~400MB).

**Important**: All Python project files (`pyproject.toml`, `uv.lock`, `.python-version`) are now in the `backend/` directory. Run all `uv` commands from the `backend/` directory.

### Authentication Setup

The project includes a FastAPI backend with Apex authentication. **Authentication is integrated into the Next.js frontend** - users must login to access the application.

To enable authentication:

1. **Set up PostgreSQL database:**
   ```bash
   # Create database
   createdb notebooklm
   ```

2. **Configure backend:**
   ```bash
   cd backend
   cp .env.example .env
   # Edit backend/.env with your DATABASE_URL and JWT_SECRET_KEY
   # IMPORTANT: DATABASE_URL must use postgresql+asyncpg:// (not postgresql://)
   ```

3. **Run database migrations:**
   ```bash
   cd backend
  # uv run alembic revision --autogenerate -m "create_users_table"
   uv run alembic upgrade head
   ```
   
   **Troubleshooting migration errors:**
   - If you get "psycopg2 is not async" error:
     - Verify `DATABASE_URL` in `backend/.env` uses `postgresql+asyncpg://` format
     - Check asyncpg is installed: `uv run python -c "import asyncpg; print('OK')"`
     - Uninstall conflicting psycopg2: `uv pip uninstall psycopg2 psycopg2-binary`
   - If you get "Can't locate revision" error:
     - The database may have old migration history. Reset it:
       ```bash
       cd backend
       uv run python -c "import asyncio; from sqlalchemy.ext.asyncio import create_async_engine; from sqlalchemy import text; from app.config import DATABASE_URL; import re; db_url = re.sub(r'postgresql\+[^:]+://', 'postgresql+asyncpg://', DATABASE_URL) if 'postgresql+asyncpg://' not in DATABASE_URL else DATABASE_URL; engine = create_async_engine(db_url); async def reset(): async with engine.connect() as conn: await conn.execute(text('DROP TABLE IF EXISTS alembic_version')); await conn.commit(); asyncio.run(reset())"
       ```
     - Then run migrations again

4. **Configure environment variables:**
   ```bash
   # Backend configuration
   cd backend
   cp .env.example .env
   # Edit backend/.env with your database and server settings
   
   # Frontend configuration
   cd ../frontend
   cp .env.example .env.local
   # Edit frontend/.env.local with your backend API URL
   ```

5. **Start backend server:**
   ```bash
   cd backend
   uv run python run.py
   # Backend runs on the host/port specified in backend/.env:
   # - BACKEND_HOST (default: 0.0.0.0)
   # - BACKEND_PORT (default: 8000)
   # Access at: http://localhost:8000 (or your configured host:port)
   ```
   
   **Important:** Always use `uv run` to ensure dependencies are available.

6. **Start Next.js frontend:**
   ```bash
   # In frontend directory (new terminal window)
   cd frontend
   npm install
   npm run dev
   # Frontend runs on http://localhost:3000 (Next.js default)
   # To change port: npm run dev -- -p 3001
   # Configure NEXT_PUBLIC_API_URL in frontend/.env.local to match your backend
   ```
   
   **Note:** The Next.js app requires authentication. On first launch, you'll see a login/signup screen. Create an account or login to access the NotebookLM features.
   
   **Important:** 
   - Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` to match your backend URL
   - Format: `NEXT_PUBLIC_API_URL=http://localhost:8000` (or your configured backend host:port)
   - If you change the frontend port, update `FRONTEND_URL` in `backend/.env` to match
    
1. **Install backend dependencies:**
    First, install `uv` and set up the environment:
    ```bash
    # MacOS/Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Windows
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

    Install Python dependencies:
    ```bash
    # Install dependencies (from backend directory)
    cd backend
    uv sync

    # Additional steps (recommended)
    uv add -U yt-dlp           # for latest version
    # TTS will automatically download models on first use
    ```

2. **Install frontend dependencies:**
    ```bash
    cd frontend
    npm install
    # or
    yarn install
    # or
    pnpm install
    ```

2. **Set up backend environment variables:**
   ```bash
   cd backend
   cp .env.example .env
   # Edit backend/.env with your settings
   ```
   
   Required variables in `backend/.env`:
   - `DATABASE_URL` - PostgreSQL connection string (required)
   - `JWT_SECRET_KEY` - Secret key for JWT tokens (required, change in production!)
   - `OPEN_ROUTER_API_KEY` - For LLM access (required)
   - `ASSEMBLYAI_API_KEY` - For audio transcription (optional)
   - `FIRECRAWL_API_KEY` - For web scraping (optional)
- `ZEP_API_KEY` - For conversational memory (optional)
- `ENABLE_TTS` - Enable/disable Text-to-Speech (optional, default: true)
- `BACKEND_CORS_ORIGINS` - Comma-separated list of allowed CORS origins (required for production)
- `FRONTEND_URL` - Frontend URL for redirects (optional, for production)
   
   Get the API keys here:
   - [OpenRouter →](https://openrouter.ai/) (for LLM access)
   - [Assembly AI →](https://www.assemblyai.com/)
   - [Zep AI →](https://www.getzep.com/)
   - [Firecrawl →](https://www.firecrawl.dev/)


## Usage

### Running the Application

**Important:** Both backend and frontend must be running simultaneously.

1. **Start the Backend (FastAPI):**
   ```bash
   cd backend
   uv run python run.py
   # Backend runs on host:port from backend/.env (BACKEND_HOST:BACKEND_PORT)
   # Default: http://localhost:8000
   ```

2. **Start the Frontend (Next.js):**
   ```bash
   # In a new terminal window
   cd frontend
   npm run dev
   # Frontend runs on http://localhost:3000 (Next.js default)
   # To change port: npm run dev -- -p 3001
   # If you change the frontend port, update FRONTEND_URL in backend/.env to match
   ```

3. **Access the Application:**
   - Open http://localhost:3000 in your browser (or your configured frontend URL)
   - You'll see the landing page with features and navigation
   - Click "Get Started" or "Sign In" to access authentication
   - Create an account or login to access the NotebookLM features
   - Upload documents, ask questions, generate podcasts, and manage your sources!

![app UI](assets/app-UI.png)


## Project Structure
```
├── 📂 backend/                        # FastAPI backend (all backend code)
│   ├── 📂 app/                        # Backend application
│   │   ├── 📂 routes/                # API routes
│   │   ├── 📂 models/                # Database models
│   │   └── api.py                    # FastAPI app
│   ├── 📂 src/                        # Main source code (moved here)
│   │   ├── 📂 audio_processing/      # Audio transcription and processing
│   │   │   ├── 🎵 audio_transcriber.py
│   │   │   └── 🎥 youtube_transcriber.py
│   │   ├── 📂 document_processing/   # Document parsing and chunking
│   │   │   └── 📄 doc_processor.py
│   │   ├── 📂 embeddings/            # Vector embeddings generation
│   │   │   └── 🧠 embedding_generator.py
│   │   ├── 📂 generation/            # RAG pipeline and response generation
│   │   │   └── 🤖 rag.py
│   │   ├── 📂 memory/                # Conversation memory management
│   │   │   └── 🧠 memory_layer.py
│   │   ├── 📂 podcast/               # Podcast generation system
│   │   │   ├── 📝 script_generator.py
│   │   │   └── 🎙️ text_to_speech.py
│   │   ├── 📂 vector_database/       # Vector storage and search
│   │   │   └── 🗄️ qdrant_vector_db.py
│   │   └── 📂 web_scraping/          # Web content extraction
│   │       └── 🌐 web_scraper.py
│   ├── 📂 migrations/                # Database migrations
│   ├── 📂 qdrant_db/                 # Qdrant vector database (local)
│   ├── 📂 data/                      # Sample documents and test data
│   ├── 📂 notebooks/                  # Jupyter notebooks
│   ├── 📂 outputs/                   # Generated outputs (podcasts, etc.)
│   ├── 📂 .embedding_model/          # Embedding model cache
│   ├── run.py                        # Server entry point
│   └── .env.example                  # Backend environment template
│
├── 📂 frontend/                       # Next.js frontend application
│   ├── 📂 app/                        # Next.js app directory
│   │   ├── page.tsx                   # Landing page
│   │   ├── login/                     # Login page
│   │   ├── signup/                    # Signup page
│   │   ├── app/                       # Main application (requires auth)
│   │   ├── privacy/                  # Privacy Policy page
│   │   └── terms/                     # Terms and Conditions page
│   ├── 📂 components/                 # React components
│   │   ├── SourcesSidebar.tsx         # Sources panel with delete functionality
│   │   ├── SourceUpload.tsx           # Upload interface with processing loaders
│   │   ├── ChatInterface.tsx          # Chat with citations
│   │   ├── StudioTab.tsx              # Podcast generation with speaker colors
│   │   └── Citation.tsx               # Citation component
│   ├── 📂 lib/                        # Utilities and API client
│   │   ├── api-client.ts              # API client with auth
│   │   └── store.ts                   # Zustand state management
│   └── 📋 package.json                # Frontend dependencies
│
├── 📂 tests/                          # Pipeline integration tests
├── 📂 data/                           # Sample documents
├── 📂 notebooks/                      # Walkthrough notebook
├── 📂 outputs/                        # Generated content
├── 📂 assets/                         # Sample images
│
├── 📋 pyproject.toml                  # Python project configuration
├── 📋 uv.lock                         # UV lock file
├── 📝 README.md                       # Project documentation
```

## Key Features

- **Citation-First Approach**: Every claim is backed by specific sources with page numbers and references as in the original NotebookLM.
- **Memory-Powered**: Uses temporal knowledge graphs to remember context and preferences during conversations.
- **Multi-Format Support**: Process PDFs, text files, audio recordings, YouTube videos and web content seamlessly.
- **Efficient Retrieval**: All relevant chunks retrieved intelligently along with citation metadata.
- **AI Podcast Generation**: Transform documents into engaging multi-speaker podcast conversations with distinct speaker colors.
- **User Authentication**: Secure signup, login, password reset, and change password functionality with JWT tokens.
- **User-Specific Data Isolation**: Each user's documents, sources, and chat history are completely isolated for privacy and security.
- **Source Management**: View, delete, and manage uploaded sources with visual feedback and processing loaders.
- **Modern UI**: Responsive Next.js frontend with red and black theme, landing page, and legal pages.
- **Landing Page**: Professional landing page with features showcase before authentication.
- **Privacy & Terms**: Dedicated Privacy Policy and Terms and Conditions pages with footer links.

# NotebookLM Frontend (Next.js)

This is the Next.js frontend for the NotebookLM Clone application.

## Setup

1. Install dependencies:
```bash
npm install
# or
yarn install
# or
pnpm install
```

2. Create `.env.local` file:
```env
# Backend API URL - must match your backend server configuration
# Format: http://host:port (e.g., http://localhost:8000)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Frontend Port (optional - Next.js default is 3000)
# To change the port, use: npm run dev -- -p 3001
# Or set PORT environment variable: PORT=3001 npm run dev
# PORT=3000
```

3. Run the development server:
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# To run on a different port: npm run dev -- -p 3001
```

**Note:** If you change the frontend port, make sure to update `FRONTEND_URL` in `backend/.env` to match.

Open http://localhost:3000 in your browser (or your configured frontend URL).

## Project Structure

```
frontend/
├── app/              # Next.js app directory
│   ├── login/        # Login page
│   ├── signup/       # Signup page
│   ├── app/          # Main application
│   └── globals.css   # Global styles
├── components/       # React components
├── lib/              # Utilities and API client
└── public/           # Static assets
```

## Features

- Authentication (Login/Signup)
- Document upload and processing
- Chat interface with citations
- Podcast generation
- Three-panel layout (Sources, Chat, Studio)


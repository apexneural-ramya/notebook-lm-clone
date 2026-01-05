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
│   ├── page.tsx      # Landing page
│   ├── login/        # Login page
│   ├── signup/       # Signup page
│   ├── app/          # Main application (requires auth)
│   ├── privacy/      # Privacy Policy page
│   ├── terms/        # Terms and Conditions page
│   └── globals.css   # Global styles
├── components/       # React components
│   ├── SourcesSidebar.tsx    # Sources panel with delete
│   ├── SourceUpload.tsx      # Upload with loaders
│   ├── ChatInterface.tsx     # Chat with citations
│   ├── StudioTab.tsx         # Podcast generation
│   └── Citation.tsx          # Citation component
├── lib/              # Utilities and API client
│   ├── api-client.ts # API client with auth
│   └── store.ts      # Zustand state management
└── public/           # Static assets
```

## Features

- **Landing Page**: Professional landing page with features showcase before authentication
- **Authentication**: Login/Signup with password reset and change password functionality
- **Document Upload**: Multi-format support (PDF, text, audio, YouTube, web URLs) with processing loaders
- **Source Management**: View and delete uploaded sources with visual feedback
- **Chat Interface**: Interactive chat with accurate citations and source references
- **Podcast Generation**: AI-powered podcast creation with distinct speaker colors (Speaker 1 & Speaker 2)
- **User-Specific Data**: Complete data isolation - each user only sees their own sources and chat history
- **Three-Panel Layout**: Sources sidebar, Chat interface, and Studio tab
- **Modern UI**: Red and black theme with responsive design
- **Legal Pages**: Privacy Policy and Terms and Conditions pages with footer links


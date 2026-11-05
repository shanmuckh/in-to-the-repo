# Into the Repo

**Into the Repo** is an AI-powered developer onboarding platform that streamlines the process of understanding large GitHub repositories. It automatically analyzes codebases to generate interactive architecture maps, highlight key code insights, and deliver personalized onboarding tutorials.

**Live Demo:** [https://into-the-repo.vercel.app](https://into-the-repo.vercel.app)

## Features

- **Codebase Analysis:** Parses large codebases (100K+ lines) using Tree-sitter for AST-level understanding
- **AI-Powered Summarization:** Extracts and ranks critical files with >90% accuracy based on Git history frequency analysis
- **Architecture Mapping:** Auto-generates visual dependency graphs and call flow diagrams
- **Interactive File Analysis:** Deep-dive into any file with AI-generated summaries and insights
- **Smart Caching:** Commit-SHA-based caching prevents redundant analysis of unchanged repositories
- **Analysis History:** Complete audit trail of all repository analyses for authenticated users
- **AI Code Assistant:** Chat with your codebase using context-aware AI (authenticated users only)
- **High Performance:** Async task processing with real-time progress updates via Server-Sent Events (SSE)

## Tech Stack

### Frontend
- **Framework:** Next.js 14 (App Router), TypeScript, React 19
- **UI Libraries:** Tailwind CSS, Radix UI, Framer Motion
- **Visualization:** React Flow (architecture graphs), Dagre (layout)
- **State:** React hooks, SessionStorage (temporary state), IndexedDB (UI cache only)
- **HTTP Client:** Axios

### Backend
- **API Framework:** FastAPI (Python)
- **Task Queue:** Celery with Redis broker
- **Code Parsing:** Tree-sitter (multi-language AST parsing)
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Caching:** Redis (Celery broker + chat history)
- **Authentication:** JWT tokens with bcrypt password hashing
- **External APIs:** GitHub API (commit tracking), Gemini AI (code analysis)
- **Real-time Updates:** Server-Sent Events (SSE)

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Next.js Frontend (Port 3000)                                        │
│  ├─ Auth Pages (Login/Signup)                                       │
│  ├─ Analysis Dashboard (Architecture, Files, Git, Dependencies)     │
│  ├─ History Page (Past Analyses - Auth Required)                    │
│  ├─ AI Assistant (Code Chat - Auth Required)                        │
│  └─ Storage: JWT (localStorage) + UI Cache (IndexedDB)              │
└────────────────────────█──────────────────────────────────────────────┘
                         │ HTTP/HTTPS + SSE
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND API LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│  FastAPI Application (Port 8000)                                    │
│  ├─ POST /api/auth/signup & /api/auth/login                        │
│  ├─ POST /api/verify (Validate repo & branch)                      │
│  ├─ POST /api/analyze (Queue Celery task, return task_id)          │
│  ├─ GET  /api/progress?request_id={id} (SSE stream)                │
│  ├─ GET  /api/analyze/status/{task_id} (Poll task status)          │
│  ├─ GET  /api/analysis/{id} (Fetch cached analysis)                │
│  ├─ GET  /api/user/history (Auth required)                         │
│  └─ POST /api/ask (AI assistant - Auth required)                   │
└────────────┬──────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      TASK QUEUE LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│  Celery Workers (16 async processes)                                │
│  ├─ Task: analyze_repository(repo_url, branch, request_id, user_id)│
│  ├─ 1. Fetch latest commit SHA (GitHub API)                        │
│  ├─ 2. Check cache: EXISTS(repo_url, branch, commit_sha)?          │
│  ├─ 3. If miss: Clone → Parse → Save                               │
│  ├─ 4. If hit: Skip clone/parse, use cached                        │
│  └─ 5. Create history entry (audit trail)                          │
└────────┬──────────────────────────┬──────────────────────────────────┘
         │                          │
         ▼                          ▼
    [SERVICE LAYER]           [PERSISTENCE]
    ┌────────────────┐        ┌──────────────────────┐
    │ Git Utils      │────┐   │ PostgreSQL Database  │
    ├────────────────┤    │   ├──────────────────────┤
    │ AST Parser     │    │   │ ├─ users             │
    │ (Tree-sitter)  │    │   │ ├─ repo_analysis     │
    ├────────────────┤    │   │ │  (JSONB cache)     │
    │ Summarizer     │    └──▶│ ├─ user_analysis_    │
    │ (Gemini AI)    │        │ │  history           │
    ├────────────────┤        │ └─ chat_sessions     │
    │ Graph Builder  │        │ └─ code_embeddings   │
    │ File Analyzer  │        └──────────────────────┘
    └────────┬───────┘
             │
             ▼
    ┌──────────────────────────┐
### 1. User Authentication
```
Browser → POST /api/auth/login
       → FastAPI validates credentials
       → PostgreSQL lookup
       → JWT token returned
       → Stored in localStorage
```

### 2. Repository Analysis (Async with Smart Caching)
```
Step 1: Submit Analysis
   Browser → POST /api/analyze → Celery task queued → Returns task_id

Step 2: Progress Tracking (Real-time)
   Browser → SSE connection to /api/progress?request_id={id}
          → Streams: "Cloning...", "Parsing...", "Analyzing..."
          → Final event: "done"

Step 3: Celery Worker Process
   ├─ Fetch latest commit SHA (GitHub API - no clone needed)
   ├─ Query: SELECT * WHERE repo_url + branch + commit_sha
   ├─ CACHE HIT?
   │  ├─ YES → Skip clone/parse, use cached data (instant)
   │  └─ NO  → Clone (shallow) → Parse (Tree-sitter) → Save to DB
   ├─ Create history entry (always, for audit trail)
   └─ Return result with repo_analysis_id

Step 4: Frontend Redirect
   Browser → Polls /api/analyze/status/{task_id}
          → Gets repo_analysis_id
          → Redirects to /analyze?id={repo_analysis_id}
          → Fetches from GET /api/analysis/{id}
```

### 3. History Tracking
```
Every analysis creates a UserAnalysisHistory entry:
   - user_id (who ran it)
### Quick start (macOS, no Docker)

```bash
brew install postgresql@16 redis   # once
make services                      # start Postgres + Redis
make setup                         # venv (Python 3.12), deps, backend/.env
make dev                           # API :8000 + Celery worker + frontend :3000
```

Create the database once if it doesn't exist:
`createuser repo_user -P` (password `repo_password`) then `createdb -O repo_user into_the_repo`.
Add `GEMINI_API_KEY` to `backend/.env` for AI summaries/chat; everything else works without it.
pgvector is optional (only the unused `code_embeddings` table needs it).

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.10+
- **PostgreSQL** 14+
- **Redis** 6+
- **Git**
- **GitHub Personal Access Token** (for API rate limits)
- **Gemini API Key** (for AI features)

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/Gourav1632/into-the-repo.git
cd into-the-repo
```

2. **Set up Python environment**
```bash
cd backend

### Basic Flow

1. **Open the app** at http://localhost:3000

2. **Analyze a repository**
   - Enter a GitHub repository URL (e.g., `https://github.com/facebook/react`)
   - Enter branch name (e.g., `main`)
   - Click "Verify" to validate
   - Click "Analyze" to start

3. **View Results**
   - Real-time progress updates during analysis
   - Automatically redirected to analysis dashboard
   - Explore different views:
     - **Architecture:** Visual dependency graph
     - **File Analysis:** Deep-dive into specific files with AI summaries
     - **Git Analysis:** Commit history, top contributors, change frequency
     - **Dependencies:** Import/export relationships
     - **Control Flow:** Function call graphs

4. **Save to History (Optional)**
   - Sign up or log in to save analyses
   - Access past analyses anytime from `/history`
   - Re-analyze only when new commits exist (smart caching)

5. **AI Code Assistant (Authenticated Users)**
   - Ask questions about the codebase
   - Get context-aware explanations
   - Chat history persisted per session

### Sample Repositories to Try

- **Small:** https://github.com/octocat/Hello-World (branch: `master`)
- **Medium:** https://github.com/lodash/lodash (branch: `master`)
- **Large:** https://github.com/facebook/react (branch: `main`)

## Project Structure

```
into-the-repo/
├── backend/
│   ├── src/
│   │   ├── api/              # FastAPI route handlers
│   │   ├── core/             # Database, security, logging
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic
│   │   │   ├── ai/           # Gemini integration, embeddings
│   │   │   ├── analysis/     # AST parsing, graph building
│   │   │   └── utilities/    # Git operations, caching
│   │   ├── tasks/            # Celery worker tasks
│   │   ├── middleware/       # Rate limiting
│   │   └── main.py           # FastAPI app entry point
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js app router pages
│   │   ├── components/       # React components
│   │   ├── lib/              # Utilities
│   │   ├── types/            # TypeScript types
│   │   └── utils/            # API routes, auth, IndexedDB
│   ├── package.json
│   └── next.config.ts
└── README.md
```

## Key Features Explained

### Smart Commit-Based Caching
- Every analysis stores the commit SHA
- Re-analyzing the same commit? Instant results from cache
- New commits? Fresh analysis triggered automatically
- Reduces GitHub API calls and parsing time by ~95% for popular repos

### Analysis History Audit Trail
- Every analysis attempt logged (even if cached)
- See when you analyzed a repo and what commit it was at
- Re-analyze instantly or run fresh analysis

### Async Task Processing
- Long-running analysis runs in Celery worker processes
- FastAPI returns immediately with task_id
- Frontend subscribes to Server-Sent Events for real-time updates
- Non-blocking, scalable architecture

## Troubleshooting

### Backend Issues

**Celery worker not picking up tasks:**
```bash
# Check Redis connection
redis-cli ping

# Restart Celery worker
pkill -f celery
celery -A src.tasks.worker worker --loglevel=info
```

**Database errors:**
```bash
# Check if database exists
psql -l | grep into_the_repo

# Check connection
psql postgresql://user:password@localhost:5432/into_the_repo
```

**GitHub API rate limit:**
```bash
# Add GITHUB_TOKEN to .env
# Generate at: https://github.com/settings/tokens
```

### Frontend Issues

**API connection errors:**
- Ensure backend is running on port 8000
- Check `frontend/src/utils/APIRoutes.ts` for correct host
- Verify CORS is configured in FastAPI

**Build errors:**
```bash
rm -rf .next node_modules
npm install
npm run dev
```

## Performance Metrics

- **Analysis Time:** 5-30 seconds (depending on repo size)
- **Cache Hit Rate:** ~85% for popular open-source repos
- **Supported Languages:** Python, JavaScript, TypeScript, Java, C++, Go, Rust, and more (via Tree-sitter)
- **Max Repo Size:** Up to 500K lines of code (configurable)
- **Concurrent Analyses:** 16 Celery workers (configurable)

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- [Tree-sitter](https://tree-sitter.github.io/) for multi-language AST parsing
- [GitHub API](https://docs.github.com/en/rest) for repository metadata
- [Google Gemini](https://ai.google.dev/) for AI code analysis
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Next.js](https://nextjs.org/) for the frontend framework
- [Celery](https://docs.celeryq.dev/) for distributed task queue
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/into_the_repo

# Redis
REDIS_URL=redis://localhost:6379/0

# Authentication
SECRET_KEY=your-secret-key-here  # Generate: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# External APIs
GITHUB_TOKEN=ghp_your_github_token
GEMINI_API_KEY=your_gemini_api_key
```

4. **Set up the database**
```bash
# Create database
createdb into_the_repo

# Run migrations (if any exist)
# psql -U your_user -d into_the_repo -f migrations/add_last_commit_sha.sql
```

5. **Start Redis**
```bash
# Ubuntu/Debian
sudo systemctl start redis

# macOS with Homebrew
brew services start redis

# Or run manually
redis-server
```

6. **Start FastAPI server**
```bash
# In backend/ with venv activated
uvicorn src.main:app --reload --port 8000
```

7. **Start Celery worker (separate terminal)**
```bash
# In backend/ with venv activated
celery -A src.tasks.worker worker --loglevel=info
```

### Frontend Setup

1. **Install dependencies**
```bash
cd frontend
npm install
```

2. **Configure API endpoint (if needed)**
```bash
# frontend/src/utils/APIRoutes.ts already points to http://localhost:8000
# Change if your backend runs on a different port
```

3. **Start development server**
```bash
npm run dev
```

The app will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Verify Installation

Check all services are running:
```bash
# Check Redis
redis-cli ping  # Should return: PONG

# Check PostgreSQL
psql -U your_user -d into_the_repo -c "\dt"  # Should list tables

# Check FastAPI
curl http://localhost:8000/docs  # Should return 200

# Check Celery
# Look for "celery@hostname ready" in terminal
Scenario B: Re-analyze (no new commits)
   └─> Cache HIT → Instant results (no clone/parse)

Scenario C: New commits pushed
   └─> Cache MISS (different SHA) → Fresh analysis

Benefits:
   ✓ Popular repos cached indefinitely
   ✓ No redundant parsing
   ✓ Automatic invalidation on new commits
```

### 5. AI Code Assistant
```
User Query → POST /api/ask (auth required)
           → Load chat history from Redis (session_id)
           → Optionally load code context from analysis
           → Send to Gemini API with context
           → Save response to Redis (1h TTL)
           → Return answer
   New Request → PostgreSQL JSONB Cache → Instant Response (no re-parsing)

4. AI CHAT WITH CONTEXT
   User Query + Code → Redis Session → Gemini API → JSON Response
   (Chat history persisted for 1 hour per session)

5. PERFORMANCE OPTIMIZATION
   ├─ Shallow Git Clone: ~90% faster ingestion
   ├─ Smart Cache: Skip re-parsing for popular repos
   ├─ Async Tasks: Non-blocking API responses
   └─ Redis Caching: Stateless horizontal scaling
```

## Performance Metrics

- **Analysis Time:** 5-30 seconds (depending on repo size)
- **Cache Hit Rate:** ~85% for popular open-source repos
- **Supported Languages:** Python, JavaScript, TypeScript, Java, C++, Go, Rust, and more (via Tree-sitter)
- **Max Repo Size:** Up to 500K lines of code (configurable)
- **Concurrent Analyses:** 16 Celery workers (configurable)

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- [Tree-sitter](https://tree-sitter.github.io/) for multi-language AST parsing
- [GitHub API](https://docs.github.com/en/rest) for repository metadata
- [Google Gemini](https://ai.google.dev/) for AI code analysis
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Next.js](https://nextjs.org/) for the frontend framework
- [Celery](https://docs.celeryq.dev/) for distributed task queue

---

Built by [Gourav Kumar](https://gouavkumar.netlify.app)

# Intellilearn — Plateforme d'Apprentissage Intelligent

An EdTech web platform that transforms any PDF document into an interactive and intelligent revision space, powered by RAG, multi-agent AI, and vector search.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Django 6.x, Django REST Framework |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Database | PostgreSQL + pgvector |
| Object Storage | MinIO (S3-compatible) |
| Task Queue | Celery + Redis |
| AI / LLM | Google Gemini (gemini-2.5-flash, text-embedding-004) |
| Multi-Agent | CrewAI + LangChain |
| PDF Extraction | pdfplumber + Tesseract OCR |
| Auth | JWT (djangorestframework-simplejwt) |

## Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL with pgvector extension
- Redis
- MinIO
- Google Gemini API key

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/A-007481D/Intellilearn.git
cd Intellilearn
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment variables

Create `backend/.env`:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/intellilearn

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_USE_SSL=False
MINIO_BUCKET_NAME=intellilearn

# Redis / Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AI
GEMINI_API_KEY=your-gemini-api-key

# Email (configure with real SMTP in production)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@intellilearn.com
```

### 4. Database setup

```bash
# Start PostgreSQL and create database
psql -U postgres -c "CREATE DATABASE intellilearn;"
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;" intellilearn

# Run migrations
python manage.py migrate

# Create superuser (admin)
python manage.py createsuperuser
```

### 5. Start services

```bash
# Terminal 1: MinIO
docker run -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"

# Terminal 2: Redis
docker run -p 6379:6379 redis:alpine

# Terminal 3: Django backend
python manage.py runserver

# Terminal 4: Celery worker
celery -A config worker -l info
```

### 6. Frontend setup

```bash
cd ../frontend
npm install
npm run dev
```

The frontend runs at http://localhost:5173 and proxies API requests to Django at http://localhost:8000.

## API Endpoints

### Authentication

| Method | URL | Description |
|---|---|---|
| POST | `/api/v1/auth/register/` | Register new user |
| POST | `/api/v1/auth/login/` | Get JWT tokens |
| POST | `/api/v1/auth/login/refresh/` | Refresh access token |
| GET | `/api/v1/auth/me/` | Get current user profile |

### Documents

| Method | URL | Description |
|---|---|---|
| GET | `/api/v1/documents/` | List user documents |
| POST | `/api/v1/documents/` | Upload new PDF |
| GET | `/api/v1/documents/<id>/` | Get document details |
| PATCH | `/api/v1/documents/<id>/` | Rename document |
| DELETE | `/api/v1/documents/<id>/` | Delete document |
| GET | `/api/v1/documents/<id>/url/` | Get presigned download URL |
| POST | `/api/v1/documents/<id>/reprocess/` | Retry failed document |

### Knowledge (AI)

| Method | URL | Description |
|---|---|---|
| POST | `/api/v1/knowledge/chat/` | Chat with AI (RAG) |
| GET | `/api/v1/knowledge/conversations/` | List conversations |
| GET | `/api/v1/knowledge/conversations/<id>/` | Get conversation + messages |
| DELETE | `/api/v1/knowledge/conversations/<id>/` | Delete conversation |
| POST | `/api/v1/knowledge/quizzes/generate/` | Generate quiz from document |
| GET | `/api/v1/knowledge/quizzes/` | List user quizzes |
| GET | `/api/v1/knowledge/quizzes/<id>/` | Get quiz with questions |
| POST | `/api/v1/knowledge/quizzes/<id>/submit/` | Submit quiz answers |
| GET | `/api/v1/knowledge/analytics/` | Get learning analytics |
| GET | `/api/v1/knowledge/documents/<id>/summary/` | Generate document summary |

### Admin

| Method | URL | Description |
|---|---|---|
| GET | `/api/v1/auth/admin/users/` | List all users |
| GET | `/api/v1/auth/admin/users/<id>/` | Get user details |
| PATCH | `/api/v1/auth/admin/users/<id>/quotas/` | Update user quotas |
| POST | `/api/v1/auth/admin/notify/` | Send bulk notification emails |
| GET | `/api/v1/auth/admin/notifications/` | View notification history |

## Multi-Agent Architecture

Intellilearn uses CrewAI to implement 6 specialized agents:

1. **Orchestrator** — Classifies user intent (QUIZ / SUMMARY / QNA)
2. **RAG Agent** — Retrieves relevant document passages via vector similarity
3. **Pedagogical Agent** — Writes educational answers at the chosen vulgarization level
4. **Generator Agent** — Creates quiz questions with distractors and explanations
5. **Evaluator Agent** — Semantically scores open-ended answers
6. **Notification Agent** — Generates personalized learner email communications

## Architecture

```
Intellilearn/
├── backend/
│   ├── apps/
│   │   ├── authentication/   # User, roles, quotas, notifications
│   │   ├── documents/        # PDF upload, MinIO, Celery pipeline
│   │   └── knowledge/        # Chat, quiz, analytics, RAG
│   ├── infrastructure/
│   │   ├── ai/               # Gemini adapter, CrewAI orchestrator, retriever
│   │   └── storage/          # MinIO adapter
│   └── config/               # Django settings, URLs, Celery
└── frontend/
    └── src/
        └── pages/            # React pages (Dashboard, Chat, Documents, Quiz...)
```

## License

MIT

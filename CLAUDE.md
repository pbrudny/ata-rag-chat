# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

Implemented — all 7 build phases done (single commit `2678596`). Backend (FastAPI + pipeline), frontend (Next.js), Docker Compose stack, and test suites are in place. See `prd.md` for original requirements.

This directory lives inside the `~/agenty` monorepo — follow the root `~/agenty/CLAUDE.md` rules (scope, secrets handling, `loaded-context/`, `tools/TOOLS.md`) in addition to what's below.

## Commands

**Backend** (`backend/`, Python 3.12+, uv):
```bash
cd backend
uv sync
uv run alembic upgrade head              # apply DB migrations
uv run uvicorn app.main:app --reload     # run API (port 8000)
uv run python -m app.scheduler.main      # run daily crawl scheduler
uv run pytest                            # unit + integration tests
uv run ruff check app/ tests/
uv run ruff format app/ tests/
```

**Frontend** (`frontend/`, Next.js 14):
```bash
cd frontend
npm install
npm run dev       # Vite/Next dev server (port 3000)
npm run build
npm run test       # Vitest
npm run lint
```

**Full stack** (from repo root, requires `.env` — copy from `.env.example`):
```bash
docker compose up
```
Services: `db` (pgvector/pg16), `backend` (FastAPI, runs migrations then uvicorn), `scheduler` (APScheduler daily crawl), `frontend` (Next.js dev), `nginx` (reverse proxy on port 80).

## Project Overview

AkademiaTA AI Assistant: a RAG chatbot for https://akademiata.edu.pl that answers prospective/current student questions (admissions, tuition, programs, offices, deadlines) using only content retrieved from the university's public website. It must never hallucinate, must cite sources, and must refresh its knowledge base daily via crawling. Full requirements are in `prd.md`.

Non-goals for v1: authentication, Moodle integration, student records, administrative workflows.

## Architecture

Pipeline (per `prd.md`, Architecture section):

```
Website → Crawler → Content Cleaner → Markdown → Chunking → Embeddings →
PostgreSQL + pgvector → Retrieval → LLM → Chat API → Next.js UI
```

Key design points:

- **Crawling (FR-1/FR-12):** Recursive crawl of akademiata.edu.pl, HTML + PDF, change detection for incremental updates, daily re-sync with cleanup of stale content. Implemented with a custom httpx-based crawler (`app/crawler/httpx_crawler.py`), not Firecrawl — see Tech Stack.
- **Content processing (FR-2/FR-3):** Strip nav/header/footer/cookie banners, convert to Markdown preserving headings/tables/lists/links, then heading-aware chunking at 700–900 tokens with 100-token overlap.
- **Metadata (FR-4):** Every chunk carries URL, title, section, language, last-modified, document ID, chunk ID, content hash, and source type — content hash is what drives "regenerate embeddings only on change" (FR-5).
- **Storage & retrieval (FR-6/FR-10):** PostgreSQL + pgvector, cosine similarity, metadata filtering, incremental indexing. Retrieval flow: question → embedding → vector search → top-K → optional reranker → LLM → answer.
- **Chat API (FR-7/FR-8/FR-9/FR-11):** `POST /api/chat` streaming via SSE, response includes answer + sources + confidence, every answer cites page title + URL, and low-confidence retrieval must return the fixed fallback: "I couldn't find this information on the AkademiaTA website."
- **Bilingual:** Must support Polish and English end to end (crawled content, chunk metadata `language` field, and chat responses).
- **Security:** Sanitize indexed HTML before storage; reject prompt injection attempts in both crawled content and user input.

## Tech Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy, Alembic, APScheduler
- Frontend: Next.js 14, React 18, Tailwind CSS
- AI: GPT-5.5 for generation (`app/services/llm_client.py`), `text-embedding-3-small` for embeddings (`app/embeddings/embedder.py`)
- Database: PostgreSQL + pgvector (`app/db/`, `app/models/`)
- Crawler: httpx-based crawler (`app/crawler/httpx_crawler.py`) — not Firecrawl; PDF handling in `app/crawler/pdf_handler.py`
- Deployment: Docker Compose (`docker-compose.yml`, `nginx.conf`)

## Non-functional targets

- Initial response < 2s; streaming starts < 1s; vector search latency < 300ms
- 100 concurrent users

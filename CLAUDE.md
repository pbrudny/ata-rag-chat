# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

Spec only — no implementation exists yet. The only file in this directory is `prd.md`. There are no build, lint, or test commands to run because there is no code. When implementation begins, update this file with the actual commands and architecture notes.

This directory lives inside the `~/agenty` monorepo — follow the root `~/agenty/CLAUDE.md` rules (scope, secrets handling, `loaded-context/`, `tools/TOOLS.md`) in addition to what's below.

## Project Overview

AkademiaTA AI Assistant: a RAG chatbot for https://akademiata.edu.pl that answers prospective/current student questions (admissions, tuition, programs, offices, deadlines) using only content retrieved from the university's public website. It must never hallucinate, must cite sources, and must refresh its knowledge base daily via crawling. Full requirements are in `prd.md`.

Non-goals for v1: authentication, Moodle integration, student records, administrative workflows.

## Planned Architecture

Pipeline (per `prd.md`, Architecture section):

```
Website → Crawler → Content Cleaner → Markdown → Chunking → Embeddings →
PostgreSQL + pgvector → Retrieval → LLM → Chat API → Next.js UI
```

Key design points to preserve when implementing:

- **Crawling (FR-1/FR-12):** Recursive crawl of akademiata.edu.pl, HTML + PDF, change detection for incremental updates, daily re-sync with cleanup of stale content. Firecrawl is the preferred crawler.
- **Content processing (FR-2/FR-3):** Strip nav/header/footer/cookie banners, convert to Markdown preserving headings/tables/lists/links, then heading-aware chunking at 700–900 tokens with 100-token overlap.
- **Metadata (FR-4):** Every chunk carries URL, title, section, language, last-modified, document ID, chunk ID, content hash, and source type — content hash is what drives "regenerate embeddings only on change" (FR-5).
- **Storage & retrieval (FR-6/FR-10):** PostgreSQL + pgvector, cosine similarity, metadata filtering, incremental indexing. Retrieval flow: question → embedding → vector search → top-K → optional reranker → LLM → answer.
- **Chat API (FR-7/FR-8/FR-9/FR-11):** `POST /api/chat` streaming via SSE, response includes answer + sources + confidence, every answer cites page title + URL, and low-confidence retrieval must return the fixed fallback: "I couldn't find this information on the AkademiaTA website."
- **Bilingual:** Must support Polish and English end to end (crawled content, chunk metadata `language` field, and chat responses).
- **Security:** Sanitize indexed HTML before storage; reject prompt injection attempts in both crawled content and user input.

## Tech Stack (planned)

- Backend: Python, FastAPI, SQLAlchemy
- Frontend: Next.js, React, Tailwind CSS
- AI: GPT-5.5 for generation, `text-embedding-3-small` for embeddings
- Database: PostgreSQL + pgvector
- Crawler: Firecrawl (preferred)
- Deployment: Docker Compose

## Non-functional targets

- Initial response < 2s; streaming starts < 1s; vector search latency < 300ms
- 100 concurrent users

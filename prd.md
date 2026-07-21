# Product Requirements Document (PRD)

## AkademiaTA AI Assistant (RAG Chatbot)

**Version:** 1.0\
**Status:** Ready for Implementation

# Project Overview

Build an AI-powered chatbot for **https://akademiata.edu.pl** that
answers questions using Retrieval-Augmented Generation (RAG) over the
university's public website.

The chatbot must never hallucinate and should answer only using
retrieved knowledge from the website. The system should automatically
crawl the website daily, update its knowledge base, and provide answers
with citations.

# Product Vision

Students and prospective students should be able to ask questions such
as: - How do I apply? - What documents are required? - How much is
tuition? - Where is the Dean's Office? - What study programs are
available? - Who is the rector? - When does the semester begin?

# Goals

## Primary Goals

-   Answer using official university information
-   Cite sources
-   Automatically update knowledge
-   Support Polish and English
-   Stream responses
-   Work on desktop and mobile

## Non-goals

Version 1 will not include: - Authentication - Moodle integration -
Student records - Administrative workflows

# Functional Requirements

## FR-1 Website Crawling

-   Crawl https://akademiata.edu.pl recursively
-   Follow internal links
-   Support HTML and PDF
-   Detect changed pages
-   Incremental updates
-   Ignore login/admin/search pages

## FR-2 Content Processing

-   Remove navigation, headers, footers and cookie banners
-   Convert HTML to Markdown
-   Preserve headings, tables, lists and links

## FR-3 Chunking

-   Heading-aware chunking
-   Target chunk size: 700--900 tokens
-   Overlap: 100 tokens

## FR-4 Metadata

Each chunk stores: - URL - Title - Section - Language - Last Modified -
Document ID - Chunk ID - Content Hash - Source Type

## FR-5 Embeddings

-   Use text-embedding-3-small
-   Regenerate only when content changes

## FR-6 Vector Storage

-   PostgreSQL + pgvector
-   Cosine similarity
-   Metadata filtering
-   Incremental indexing

## FR-7 Chat API

POST /api/chat

Response: - answer - sources - confidence

## FR-8 Streaming

-   Server-Sent Events (SSE)

## FR-9 Citations

Every answer includes page title and URL.

## FR-10 Retrieval Pipeline

Question → Embedding → Vector Search → Top-K → (Optional Reranker) → LLM
→ Answer

## FR-11 Unknown Questions

If confidence is low: "I couldn't find this information on the
AkademiaTA website."

## FR-12 Daily Synchronization

Daily crawl, change detection, re-embedding and cleanup.

# Non-functional Requirements

-   Initial response \<2 seconds
-   Streaming starts \<1 second
-   Search latency \<300 ms
-   100 concurrent users
-   Sanitize indexed HTML
-   Reject prompt injection attempts

# Architecture

Website → Crawler → Content Cleaner → Markdown → Chunking → Embeddings →
PostgreSQL + pgvector → Retrieval → LLM → Chat API → Next.js UI

# Tech Stack

Backend: - Python - FastAPI - SQLAlchemy

Frontend: - Next.js - React - Tailwind CSS

AI: - GPT-5.5 - text-embedding-3-small

Database: - PostgreSQL - pgvector

Crawler: - Firecrawl (preferred)

Deployment: - Docker Compose

# Admin Dashboard

Display: - Number of pages - Number of chunks - Last crawl - Failed
pages - Retrieval metrics - Top questions - Unanswered questions

# Definition of Done

-   Automatic crawling
-   Daily updates
-   Grounded answers only
-   Citations included
-   Graceful handling of unknown answers
-   Streaming UI
-   Dockerized deployment
-   Automated tests
-   Clean architecture


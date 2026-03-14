# AI Note Community

AI Note Community is an open, community-scoped note workspace derived from the broader LabNote AI product direction.

This repository is intentionally narrow. It focuses on core note management and collaboration workflows that can stand on their own without private or premium product dependencies.

## Scope

The community edition currently targets these areas:

1. Note editing
2. Member management
3. Backup and restore
4. Embedding search
5. Note graph

Community feedback is also included as a first-class workflow, with support for screenshot attachments and an optional GitHub issue bridge.

## Out of Scope

The following product areas are explicitly excluded from this repository:

- AI librarian chat
- AI reviewer
- AI co-scientist
- Protocol library
- Zotero integration
- Compliance and enterprise controls
- Factory appliance activation
- Billing and feature gates

## Current Stack

- Backend: FastAPI
- Frontend: React + Vite
- Database: PostgreSQL with `pgvector`
- Local persistence: lightweight JSON-backed shell components where needed

## Features Included Today

- Authentication, signup, and setup flow
- Notes and notebooks
- Workspace member management
- Search and graph views
- Snapshot and backup settings
- Feedback submission with up to 3 screenshots
- Optional GitHub issue sync for feedback

## Quick Start

### Option 1: One-command bootstrap

```bash
./install.sh
```

This script:

- creates `.env` from `.env.example` if needed
- generates local secrets
- starts the Docker stack
- runs database migrations

After startup:

- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8001/docs`

### Option 2: Manual Docker startup

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec -T backend alembic upgrade head
```

## Environment Variables

Main configuration lives in `.env`.

Important values:

- `DATABASE_URL`: backend database connection string
- `JWT_SECRET`: secret used for access and refresh tokens
- `OPENAI_API_KEY`: required if embedding-based search is connected to OpenAI
- `APP_BASE_URL`: frontend base URL
- `GITHUB_FEEDBACK_REPO`: optional target repo for feedback issue creation
- `GITHUB_FEEDBACK_TOKEN`: optional token for GitHub feedback sync

See [.env.example](/mnt/docker/ainote-community/.env.example) for the full template.

## Repository Layout

- [backend](/mnt/docker/ainote-community/backend): FastAPI app, config, storage layer, and tests
- [frontend](/mnt/docker/ainote-community/frontend): React application
- [docs](/mnt/docker/ainote-community/docs): scope and extraction documentation
- [scripts](/mnt/docker/ainote-community/scripts): extraction and support scripts

## Development Notes

- The current implementation is intentionally lightweight and independent.
- Backend validation can be run with `cd backend && pytest tests/test_community_shell.py`.
- This repository should remain community-scoped and should not import private-product modules unless that boundary is explicitly approved.

## Project Boundary

This repository is not intended to be a full mirror of the private product. It is a clean, community-oriented extraction path. Any future expansion should preserve that boundary and avoid reintroducing premium-only or internal-only concerns.

## Source Context

The original reference product is the private `labnote-ai` codebase, but this repository is meant to operate independently.

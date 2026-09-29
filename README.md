# LinkFolio

A "link in bio" tool — one public page listing all your links, plus a dashboard with real click
analytics. Think Linktree, but you can see exactly which links people are actually clicking, and
when.

## Features

- **Auth** — register/login with JWT, bcrypt password hashing
- **Your page** — a public profile at `/u/:username` listing your active links, with no login
  required to view it
- **Link management** — add, edit, hide, delete, and reorder links from a dashboard
- **Real click tracking** — every public link is actually a tracked redirect
  (`/api/public/links/:id/go`): the visitor clicks, a click gets recorded, then they're bounced to
  the real URL. No client-side JS is needed for tracking to work.
- **Analytics dashboard** — total clicks, clicks per link, and a 30-day daily trend, charted

## Stack

| Layer | Tech |
| --- | --- |
| API | FastAPI, SQLAlchemy 2.0, SQLite |
| Auth | JWT (`python-jose`), `bcrypt` for password hashing |
| Client | React 19 (JS), React Router, Recharts |
| Tests | pytest + FastAPI's `TestClient` (28 examples), Vitest + React Testing Library (14 examples) |

No paid services or cloud accounts are required to run this locally.

## Project layout

```
server/   # FastAPI app (routers, SQLAlchemy models, the JWT/bcrypt auth)
client/   # React frontend (dashboard + the public /u/:username page)
```

## Running it locally

### API

```bash
cd server
python -m venv venv
source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Tables are created automatically on first run (`Base.metadata.create_all`) — no separate
migration step for a project this size.

Run the backend tests:

```bash
cd server
pytest -q
```

### Client

```bash
cd client
cp .env.example .env.local   # adjust VITE_API_BASE_URL if needed
npm install
npm run dev
```

Run the frontend tests:

```bash
cd client
npm test
```

## How click tracking works

A link on the public page doesn't point straight at its target URL — it points at
`GET /api/public/links/:id/go`. That endpoint:

1. Looks up the link (404s if it's missing or hidden)
2. Records a `Click` row (timestamp + referrer only — never an IP address or anything else that
   could identify a visitor)
3. Issues an HTTP 302 redirect to the real URL

The browser follows the redirect transparently, so visitors never see or feel the extra hop — but
now every click is real, queryable data. `GET /api/analytics/summary` aggregates it into total
clicks, a per-link breakdown, and a 30-day daily series (zero-filled, so the chart always has a
continuous 30-day axis even for a brand-new account).

## Notes on the auth design

- Unlike the other two projects in this set, LinkFolio has **no teams or workspaces** — a
  Linktree-style tool is inherently single-creator, so authorization here is simple ownership
  (`link.user_id == current_user.id`), not roles. Every link/profile endpoint checks that, and an
  attempt to touch someone else's link 404s rather than 403s, so it doesn't even confirm the link
  exists.
- Passwords are hashed with `bcrypt` directly (not `passlib`) — `passlib`'s bcrypt wrapper is
  effectively unmaintained and breaks on bcrypt >= 4.1's package layout.
- The JWT secret key has a dev-only default in `app/config.py`; set `LINKFOLIO_SECRET_KEY` before
  deploying anywhere real.

## What's intentionally left out

This is a portfolio-scale MVP, not a production SaaS. A few things that would come next: custom
domains, link scheduling (start/end dates), UTM-tagged short links, and per-day/per-referrer
breakdowns in the analytics view instead of just per-link totals.

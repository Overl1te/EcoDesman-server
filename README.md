# ЭкоВыхухоль Server

Django API for the `ЭкоВыхухоль` mobile client.

## Implemented

- JWT auth: `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `GET/PATCH /api/v1/auth/me`
- public profiles: `GET /api/v1/profiles/{id}`
- posts feed with pagination and author filter: `GET /api/v1/posts`, `GET /api/v1/posts?author_id={id}`
- post details with comments, likes, and views: `GET /api/v1/posts/{id}`
- post creation and editing: `POST /api/v1/posts`, `PATCH /api/v1/posts/{id}`, `DELETE /api/v1/posts/{id}`
- likes: `POST /api/v1/posts/{id}/like`, `DELETE /api/v1/posts/{id}/like`
- comments: `GET/POST /api/v1/posts/{id}/comments`
- healthcheck: `GET /api/v1/health/`
- roles: `admin`, `moderator`, `user`

## Docker-first Run

The server is expected to be started via Docker Compose.

```bash
docker compose up --build -d
docker compose ps
```

Stop it with:

```bash
docker compose down
```

If you also want to remove the Postgres volume:

```bash
docker compose down -v
```

## Environment

Compose already provides defaults for local development:

- `POSTGRES_DB=econizhny`
- `POSTGRES_USER=econizhny`
- `POSTGRES_PASSWORD=econizhny`
- `WEB_PORT=8000`
- `DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0`

Override them through shell env vars or a `.env` file before `docker compose up`.

## VPS Deploy

Target server:

- Ubuntu
- IP: `130.49.150.192`
- repo: `git@github.com:Overl1te/EcoNizhny-server.git`

There is a standalone deploy script prepared for `~/deploy_econizhny_server.sh`:

- `deploy_econizhny_server.sh`

What it does:

- installs `git`, Docker Engine and Docker Compose plugin
- expects the repo to already exist in `~/EcoNizhny-server`
- updates the existing checkout with `git fetch` + `git pull`
- creates `~/EcoNizhny-server/.env` if it does not exist
- builds and starts the stack with `docker compose up --build -d`
- waits for `http://127.0.0.1/api/v1/health/`

If `~/EcoNizhny-server` is missing or is not a git repo, the script will stop and ask you to clone the repo there first.

Environment template for production:

- `.env.production.example`

## Demo Accounts

- `anna@econizhny.local` / `demo12345`
- `ivan@econizhny.local` / `demo12345`
- `admin@econizhny.local` / `demo12345`

## Verification

```bash
python manage.py test
docker compose config
docker compose up --build -d
```

After startup:

```bash
curl http://127.0.0.1:8000/api/v1/health/
```

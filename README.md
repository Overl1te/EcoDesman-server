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

Runtime logs are written into:

- `./runtime_logs/gunicorn_access.log`
- `./runtime_logs/gunicorn_error.log`
- `./runtime_logs/django.log`
- `./runtime_logs/django.error.log`
- `./runtime_logs/backup.log`

## Environment

Compose already provides defaults for local development:

- `POSTGRES_DB=econizhny`
- `POSTGRES_USER=econizhny`
- `POSTGRES_PASSWORD=econizhny`
- `WEB_PORT=8000`
- `DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0`

Override them through shell env vars or a `.env` file before `docker compose up`.

## S3 Media Storage

Media uploads can be switched from the local `/media` volume to an S3-compatible bucket.

Set these env vars in `.env`:

- `DJANGO_USE_S3_MEDIA=true`
- `DJANGO_SERVE_MEDIA=false`
- `AWS_STORAGE_BUCKET_NAME=<bucket-name>`
- `AWS_S3_ENDPOINT_URL=<s3-endpoint-with-scheme>`
- `AWS_S3_ACCESS_KEY_ID=<access-key>`
- `AWS_S3_SECRET_ACCESS_KEY=<secret-key>`

Optional:

- `AWS_S3_CUSTOM_DOMAIN=<public-bucket-domain>`
- `AWS_S3_ADDRESSING_STYLE=virtual` or `path`
- `AWS_S3_VERIFY=/usr/lib/ssl/cert.pem` for S3-compatible endpoints that need the system CA bundle inside Docker
- `AWS_QUERYSTRING_AUTH=false` for public media
- `AWS_DEFAULT_ACL=public-read` or `AWS_S3_OBJECT_ACL=public-read` if your bucket policy requires object ACLs
- `AWS_LOCATION=uploads` if you want a prefix for all media objects

For REG.RU S3 the safer default is:

- `AWS_S3_ADDRESSING_STYLE=path`
- `AWS_S3_VERIFY=/usr/lib/ssl/cert.pem`
- leave `AWS_S3_CUSTOM_DOMAIN` empty until the public bucket URL is verified
- make the bucket publicly readable if you expect plain image URLs from the API

## Daily Backups

Compose now also starts a `backup` service.

What it does:

- creates a PostgreSQL dump once per day
- archives the current runtime logs
- uploads both archives to S3
- deletes old local and remote archives by retention period

Config:

- `BACKUP_TIMEZONE=Europe/Moscow`
- `BACKUP_SCHEDULE_HOUR=3`
- `BACKUP_SCHEDULE_MINUTE=0`
- `BACKUP_RETENTION_DAYS=7`
- `BACKUP_S3_PREFIX=ops`
- `BACKUP_S3_BUCKET_NAME=` if backups should go to another bucket
- `BACKUP_RUN_ON_START=false`

Local files:

- `./backups/db/*.dump`
- `./backups/logs/*.tar.gz`

Manual restore:

```bash
./restore_db.sh ops/db/econizhny-20260402-030000.dump
```

You can also pass a local file path instead of an S3 key.

When S3 is enabled, upload URLs are returned from the storage backend directly instead of local `/media/...` URLs.

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

FROM python:3.12-slim-bookworm AS python-runtime

FROM postgres:16-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Reuse the official Python runtime on top of the PostgreSQL image so the
# container has both Python and pg_dump/pg_restore without apt-get at build time.
COPY --from=python-runtime /usr/local /usr/local

COPY requirements ./requirements
RUN pip install --no-cache-dir -r requirements/base.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]

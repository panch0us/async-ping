FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /bin/

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app

RUN uv sync

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "main.py"]
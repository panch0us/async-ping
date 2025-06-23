FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /bin/

ADD . /app

WORKDIR /app

RUN uv sync

ENV PATH="/app/.venv/bin:$PATH"

VOLUME /app/logs

CMD ["uv", "run", "main.py"]
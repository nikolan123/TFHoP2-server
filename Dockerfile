FROM ghcr.io/astral-sh/uv:0.10.2 AS uv

FROM python:3.13-slim

COPY --from=uv /uv /uvx /bin/

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TFHOP2_DATABASE_PATH=/data/portal.db \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN mkdir -p /data

VOLUME ["/data"]
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

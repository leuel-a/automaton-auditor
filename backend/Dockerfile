# STAGE 1: Base
ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS base

RUN pip install --no-cache-dir uv

WORKDIR /app

# STAGE 2: Dependencies
FROM base AS deps

COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen --no-dev

# STAGE 3: Runner
FROM python:${PYTHON_VERSION}-slim AS runner

WORKDIR /app

COPY --from=deps /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]

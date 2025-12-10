FROM python:3.11-slim

ENV UV_SYSTEM_BIN=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml .

RUN uv sync --no-dev

COPY training ./training

ENTRYPOINT ["python", "-m", "training.train"]

FROM python:3.11-slim

ENV UV_SYSTEM_BIN=1

WORKDIR /src

RUN pip install --no-cache-dir uv

COPY pyproject.toml .

RUN uv sync --no-dev

COPY src/train.py /src/

ENTRYPOINT ["python", "-m", "src.train"]

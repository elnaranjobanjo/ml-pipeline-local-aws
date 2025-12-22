"""Symbolic training routine for the LocalStack demo.

The Lambda still exercises the same S3 ingress/egress pattern as the original
model, but it now keeps the deployment package tiny by relying only on boto3
for AWS IO and Python's stdlib for basic CSV summarization.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Sequence

import boto3

logger = logging.getLogger(__name__)


@dataclass
class TrainingResult:
    """Container for the symbolic training output."""

    metrics: Dict[str, float]
    columns: Sequence[str]
    preview_rows: Sequence[Dict[str, str]]
    artifact_bucket: str | None = None
    artifact_key: str | None = None


def _s3_client(endpoint_url: str | None):
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def _summarize_csv(stream: io.BufferedReader) -> tuple[list[str], int, list[Dict[str, str]]]:
    """Return the header, row count, and a few preview rows from a CSV stream."""
    text_stream = io.TextIOWrapper(stream, encoding="utf-8")
    reader = csv.reader(text_stream)
    header = next(reader, [])
    columns = [col.strip() or f"column_{idx+1}" for idx, col in enumerate(header)]
    preview_rows: list[Dict[str, str]] = []
    row_count = 0
    for row in reader:
        if not any(cell.strip() for cell in row):
            continue
        row_count += 1
        if len(preview_rows) < 5 and columns:
            preview_rows.append(
                {
                    column: row[idx].strip() if idx < len(row) else ""
                    for idx, column in enumerate(columns)
                }
            )
    return columns, row_count, preview_rows


def run_training(
    *,
    bucket: str,
    key: str,
    endpoint_url: str | None,
    artifact_bucket: str | None = None,
    artifact_key: str | None = None,
    test_size: float = 0.2,
    random_state: int = 137,
) -> TrainingResult:
    """Summarize a CSV in S3 and push a JSON artifact with basic metrics."""
    del test_size, random_state  # kept for compatibility with existing callers
    client = _s3_client(endpoint_url)
    logger.info("Loading dataset from s3://%s/%s", bucket, key)
    response = client.get_object(Bucket=bucket, Key=key)
    byte_size = int(response.get("ContentLength") or 0)
    with closing(response["Body"]) as body:
        columns, row_count, preview_rows = _summarize_csv(body)

    metrics: Dict[str, float] = {
        "row_count": float(row_count),
        "column_count": float(len(columns)),
        "byte_size": float(byte_size),
    }
    logger.info("Dataset metrics: %s", json.dumps(metrics))
    result = TrainingResult(metrics=metrics, columns=columns, preview_rows=preview_rows)

    if artifact_bucket and artifact_key:
        _persist_artifact(
            metrics=metrics,
            columns=columns,
            preview_rows=preview_rows,
            bucket=artifact_bucket,
            key=artifact_key,
            endpoint_url=endpoint_url,
            source_bucket=bucket,
            source_key=key,
        )
        result.artifact_bucket = artifact_bucket
        result.artifact_key = artifact_key

    return result


def _persist_artifact(
    *,
    metrics: Dict[str, float],
    columns: Sequence[str],
    preview_rows: Sequence[Dict[str, str]],
    bucket: str,
    key: str,
    endpoint_url: str | None,
    source_bucket: str,
    source_key: str,
) -> None:
    """Store a small JSON summary of the dataset back in S3."""
    payload = json.dumps(
        {
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "source": {"bucket": source_bucket, "key": source_key},
            "metrics": metrics,
            "columns": list(columns),
            "preview_rows": list(preview_rows),
        }
    ).encode("utf-8")
    logger.info("Uploading summary artifact to s3://%s/%s", bucket, key)
    client = _s3_client(endpoint_url)
    client.put_object(Bucket=bucket, Key=key, Body=payload, ContentType="application/json")

"""Synthetic data ingest Lambda.

The function fabricates a short CSV batch and ships it to S3 so LocalStack
demonstrations have a repeatable upstream dependency.
"""

from __future__ import annotations

import csv
import io
import json
import os
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Sequence

import boto3


def _s3_client(endpoint_url: str | None):
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def _generate_rows(*, batch_size: int, symbol: str) -> List[Dict[str, Any]]:
    """Create pseudo market data rows."""
    price = 20000.0
    rows: List[Dict[str, Any]] = []
    for idx in range(batch_size):
        drift = random.uniform(-35, 35)
        price = max(50.0, price + drift)
        volume = random.uniform(5.0, 15.0)
        direction = "up" if drift >= 0 else "down"
        rows.append(
            {
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "symbol": symbol,
                "sequence": idx,
                "price": round(price, 2),
                "volume": round(volume, 4),
                "label": direction,
            }
        )
    return rows


def _rows_to_csv(rows: Sequence[Mapping[str, Any]]) -> str:
    """Serialize rows to CSV with a fixed schema."""
    columns = ["timestamp", "symbol", "sequence", "price", "volume", "label"]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def lambda_handler(event: Mapping[str, Any] | None, _context: Any) -> Dict[str, Any]:
    """Generate a CSV batch and upload it to S3."""
    payload = event or {}
    bucket = payload.get("bucket") or os.getenv("INGEST_BUCKET", "ml-data-demo")
    key = payload.get("key") or os.getenv("INGEST_KEY", "data/ingest_batch.csv")
    batch_size = int(payload.get("batch_size") or os.getenv("INGEST_BATCH_SIZE", "32"))
    symbol = payload.get("symbol") or os.getenv("INGEST_SYMBOL", "BTC-USD")
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")

    rows = _generate_rows(batch_size=batch_size, symbol=symbol)
    csv_blob = _rows_to_csv(rows).encode("utf-8")
    upload_key = key.replace("${uuid}", str(uuid.uuid4()))
    client = _s3_client(endpoint_url)
    client.put_object(
        Bucket=bucket,
        Key=upload_key,
        Body=csv_blob,
        ContentType="text/csv",
    )

    body = {
        "bucket": bucket,
        "key": upload_key,
        "records": batch_size,
        "sample": rows[:3],
    }
    return {"statusCode": 200, "body": json.dumps(body)}

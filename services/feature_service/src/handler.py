"""Feature engineering Lambda for the LocalStack ML demo."""

from __future__ import annotations

import csv
import io
import json
import os
import uuid
from statistics import fmean
from typing import Any, Dict, Iterable, List, Mapping

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


def _read_csv(client, bucket: str, key: str) -> List[Dict[str, Any]]:
    response = client.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(body))
    rows: List[Dict[str, Any]] = []
    for record in reader:
        try:
            rows.append(
                {
                    "timestamp": record.get("timestamp") or "",
                    "symbol": record.get("symbol") or "",
                    "sequence": int(record.get("sequence") or 0),
                    "price": float(record.get("price") or 0),
                    "volume": float(record.get("volume") or 0),
                    "label": record.get("label") or "",
                }
            )
        except ValueError:
            continue
    return rows


def _engineer_features(rows: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Compute a couple of simple derived values."""
    rows = list(rows)
    max_volume = max((row["volume"] for row in rows), default=0.0)
    avg_price = fmean((row["price"] for row in rows)) if rows else 0.0
    feats: List[Dict[str, Any]] = []
    last_price = None
    for row in rows:
        price = row["price"]
        change = 0.0 if last_price is None else price - last_price
        pct_change = 0.0 if avg_price == 0 else change / avg_price
        normalized_volume = 0.0 if max_volume == 0 else row["volume"] / max_volume
        feats.append(
            {
                "timestamp": row["timestamp"],
                "symbol": row["symbol"],
                "sequence": row["sequence"],
                "label": row["label"],
                "price": round(price, 4),
                "price_change": round(change, 4),
                "price_change_pct_of_avg": round(pct_change, 6),
                "normalized_volume": round(normalized_volume, 6),
            }
        )
        last_price = price
    return feats


def lambda_handler(event: Mapping[str, Any] | None, _context: Any) -> Dict[str, Any]:
    payload = event or {}
    source_bucket = payload.get("source_bucket") or os.getenv(
        "FEATURE_SOURCE_BUCKET", "ml-data-demo"
    )
    source_key = payload.get("source_key") or os.getenv(
        "FEATURE_SOURCE_KEY", "data/ingest_batch.csv"
    )
    feature_bucket = payload.get("feature_bucket") or os.getenv(
        "FEATURE_BUCKET", "ml-data-demo"
    )
    feature_key = payload.get("feature_key") or os.getenv(
        "FEATURE_KEY", "features/ingest_batch.jsonl"
    )
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    client = _s3_client(endpoint_url)
    rows = _read_csv(client, source_bucket, source_key)
    features = _engineer_features(rows)

    token = payload.get("uuid") or os.getenv("FEATURE_RUN_ID") or str(uuid.uuid4())
    rendered_key = feature_key.replace("${uuid}", token).replace("//", "/")
    body = "\n".join(json.dumps(row) for row in features).encode("utf-8")
    client.put_object(
        Bucket=feature_bucket,
        Key=rendered_key,
        Body=body,
        ContentType="application/json",
    )

    preview = features[:3]
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "source_bucket": source_bucket,
                "source_key": source_key,
                "feature_bucket": feature_bucket,
                "feature_key": rendered_key,
                "feature_count": len(features),
                "preview": preview,
            }
        ),
    }

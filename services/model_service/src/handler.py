"""AWS Lambda entrypoint for the model service."""

from __future__ import annotations

import json
import os
from typing import Any, Mapping

from train import run_training


def _get_value(event: Mapping[str, Any] | None, key: str, default: str) -> str:
    if event and key in event:
        value = event[key]
        if isinstance(value, str) and value:
            return value
    return os.getenv(key, default)


def lambda_handler(event: Mapping[str, Any] | None, _context: Any) -> dict[str, Any]:
    """Lambda handler that triggers the training job."""
    bucket_default = os.getenv("TRAINING_DATA_BUCKET") or "ml-data-demo"
    key_default = os.getenv("TRAINING_DATA_KEY") or "data/btc_candles_labeled_sample.csv"
    artifact_bucket_default = os.getenv("TRAINING_ARTIFACT_BUCKET") or "artifacts"
    artifact_key_default = os.getenv("TRAINING_ARTIFACT_KEY") or "models/training_pipeline.pkl"
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")
    event_payload = event or {}
    test_size = float(event_payload.get("test_size", os.getenv("TRAIN_TEST_SIZE", "0.2")))
    random_state = int(event_payload.get("random_state", os.getenv("TRAIN_RANDOM_STATE", "137")))

    bucket = _get_value(event_payload, "bucket", bucket_default)
    key = _get_value(event_payload, "key", key_default)
    artifact_bucket = _get_value(event_payload, "artifact_bucket", artifact_bucket_default)
    artifact_key = _get_value(event_payload, "artifact_key", artifact_key_default)

    result = run_training(
        bucket=bucket,
        key=key,
        endpoint_url=endpoint_url,
        artifact_bucket=artifact_bucket,
        artifact_key=artifact_key,
        test_size=test_size,
        random_state=random_state,
    )
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "metrics": result.metrics,
                "columns": list(result.columns),
                "preview_rows": result.preview_rows,
                "artifact_bucket": result.artifact_bucket,
                "artifact_key": result.artifact_key,
            }
        ),
    }

"""Inference Lambda: loads the model artifact and emits dummy predictions."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Mapping

import boto3
from botocore.exceptions import ClientError


def _s3_client(endpoint_url: str | None):
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def _load_artifact(client, bucket: str, key: str) -> Dict[str, Any]:
    try:
        response = client.get_object(Bucket=bucket, Key=key)
        payload = response["Body"].read().decode("utf-8")
        return json.loads(payload)
    except client.exceptions.NoSuchKey:
        pass
    except ClientError:
        pass
    return {"generated_at": None, "metrics": {"row_count": 1.0}}


def _score(record: Mapping[str, Any]) -> float:
    score = 0.0
    for value in record.values():
        if isinstance(value, (int, float)):
            score += float(value)
    return score


def _predict(records: Iterable[Mapping[str, Any]], boundary: float) -> List[Dict[str, Any]]:
    preds: List[Dict[str, Any]] = []
    for idx, record in enumerate(records):
        score = _score(record)
        label = "buy" if score >= boundary else "hold"
        confidence = 0.0 if boundary == 0 else min(1.0, abs(score / boundary))
        preds.append(
            {
                "id": record.get("sequence", idx),
                "prediction": label,
                "score": round(score, 4),
                "confidence": round(confidence, 4),
            }
        )
    return preds


def lambda_handler(event: Mapping[str, Any] | None, _context: Any) -> Dict[str, Any]:
    payload = event or {}
    artifact_bucket = payload.get("artifact_bucket") or os.getenv(
        "INFERENCE_ARTIFACT_BUCKET", "artifacts"
    )
    artifact_key = payload.get("artifact_key") or os.getenv(
        "INFERENCE_ARTIFACT_KEY", "models/training_pipeline.pkl"
    )
    decision_boundary = float(payload.get("decision_boundary") or 0)
    endpoint_url = os.getenv("AWS_ENDPOINT_URL")

    client = _s3_client(endpoint_url)
    artifact = _load_artifact(client, artifact_bucket, artifact_key)
    metrics = artifact.get("metrics") or {}
    if decision_boundary == 0:
        decision_boundary = float(metrics.get("row_count") or 1.0)
    inputs = payload.get("inputs") or payload.get("records") or []
    if not isinstance(inputs, list):
        inputs = []
    predictions = _predict(inputs, decision_boundary)
    body = {
        "model_version": artifact.get("generated_at"),
        "artifact_bucket": artifact_bucket,
        "artifact_key": artifact_key,
        "decision_boundary": decision_boundary,
        "prediction_count": len(predictions),
        "predictions": predictions,
    }
    return {"statusCode": 200, "body": json.dumps(body)}

"""Monitoring Lambda that computes toy accuracy/drift metrics."""

from __future__ import annotations

import json
import os
from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Sequence


def _normalize_label(value: Any) -> str:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned.lower() or "unknown"
    if isinstance(value, (int, float)):
        return f"{value:.4f}"
    return "unknown"


def _extract_prediction_labels(predictions: Iterable[Mapping[str, Any]]) -> List[str]:
    labels: List[str] = []
    for record in predictions:
        if not isinstance(record, Mapping):
            continue
        label = record.get("prediction")
        if label is None:
            label = record.get("label")
        labels.append(_normalize_label(label))
    return labels


def _total_variation(pred_counter: Counter[str], actual_counter: Counter[str]) -> float:
    pred_total = sum(pred_counter.values())
    actual_total = sum(actual_counter.values())
    if pred_total == 0 or actual_total == 0:
        return 0.0
    labels = set(pred_counter) | set(actual_counter)
    distance = 0.0
    for label in labels:
        distance += abs(
            pred_counter[label] / pred_total - actual_counter[label] / actual_total
        )
    return round(distance / 2, 6)


def _accuracy(predictions: Sequence[str], actuals: Sequence[str]) -> float | None:
    if not actuals or len(actuals) != len(predictions):
        return None
    matches = sum(1 for pred, act in zip(predictions, actuals) if pred == act)
    return round(matches / len(actuals), 4) if actuals else None


def lambda_handler(event: Mapping[str, Any] | None, _context: Any) -> Dict[str, Any]:
    payload = event or {}
    predictions = payload.get("predictions") or []
    actuals = payload.get("actuals") or []
    dataset_tag = payload.get("dataset_tag") or os.getenv("MONITOR_DATASET_TAG", "demo")

    if not isinstance(predictions, list):
        predictions = []
    if not isinstance(actuals, list):
        actuals = []

    pred_labels = _extract_prediction_labels(predictions)
    actual_labels = [_normalize_label(value) for value in actuals]

    pred_counter = Counter(pred_labels)
    actual_counter = Counter(actual_labels)

    accuracy = _accuracy(pred_labels, actual_labels)
    drift_score = _total_variation(pred_counter, actual_counter)

    summary = {
        "dataset_tag": dataset_tag,
        "prediction_count": len(pred_labels),
        "label_distribution": dict(pred_counter),
        "actual_distribution": dict(actual_counter),
        "accuracy": accuracy,
        "drift_score": drift_score,
    }

    print(json.dumps(summary))
    body = json.dumps(
        {
            **summary,
            "sample_predictions": predictions[:3],
            "sample_actuals": actuals[:3],
        },
        default=str,
    )
    return {"statusCode": 200, "body": body}

"""Training routine that mirrors the bitcoin ML cycle logistic classifier.

This version pulls the labeled candle dataset from an S3 bucket (LocalStack in
development) and trains a simple logistic regression model.
"""

from __future__ import annotations

import io
import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, Sequence

import boto3
import joblib
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

FEATURE_COLUMNS: Sequence[str] = (
    "open_price",
    "high_price",
    "low_price",
    "close_price",
    "volume_btc",
    "volume_usd",
    "trade_count",
    "taker_buy_volume_btc",
    "taker_buy_volume_usd",
    "close_price_gt_prev",
)
TARGET_COLUMN = "next_close_price_gt_curr"


@dataclass
class TrainingResult:
    """Container for the trained model and evaluation metadata."""

    model: Pipeline
    metrics: Dict[str, float]
    feature_names: Sequence[str]
    input_example: NDArray[np.float64]


def _load_dataframe_from_s3(*, bucket: str, key: str, endpoint_url: str | None) -> pd.DataFrame:
    """Return the labeled candle dataset stored as CSV in S3."""
    logger.info("Loading dataset from s3://%s/%s", bucket, key)
    session = boto3.session.Session()
    client = session.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )
    response = client.get_object(Bucket=bucket, Key=key)
    with io.BytesIO(response["Body"].read()) as buffer:
        df = pd.read_csv(buffer)
    logger.info("Loaded %s rows from S3", len(df))
    return df


def _prepare_arrays(df: pd.DataFrame) -> tuple[NDArray[np.float64], NDArray[np.int8]]:
    missing = [column for column in (*FEATURE_COLUMNS, TARGET_COLUMN) if column not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")
    clean_df = df.dropna(subset=[*FEATURE_COLUMNS, TARGET_COLUMN])
    if clean_df.empty:
        raise RuntimeError("No rows remain after dropping those with missing values")
    features = clean_df.loc[:, FEATURE_COLUMNS].to_numpy(dtype=np.float64)
    labels = clean_df.loc[:, TARGET_COLUMN].to_numpy(dtype=np.int8)
    return features, labels


def train_next_move_logistic_classifier(
    *,
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 137,
) -> TrainingResult:
    """Fit a basic classifier to predict if the next close price increases."""
    features, labels = _prepare_arrays(df)
    if len(labels) < 100:
        raise RuntimeError("Need at least 100 labeled rows to train the classifier")

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=test_size,
        random_state=random_state,
        stratify=labels if len(np.unique(labels)) > 1 else None,
    )

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=500,
                    random_state=random_state,
                ),
            ),
        ]
    )
    logger.info("Training logistic regression classifier on %s samples", X_train.shape[0])
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics: Dict[str, float] = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
    }
    if len(np.unique(y_test)) > 1:
        y_proba = model.predict_proba(X_test)[:, 1]
        metrics["roc_auc"] = float(roc_auc_score(y_test, y_proba))

    return TrainingResult(
        model=model,
        metrics=metrics,
        feature_names=FEATURE_COLUMNS,
        input_example=X_test[:5],
    )


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
    """Load training data from S3, fit the classifier, optionally persist artifacts."""
    df = _load_dataframe_from_s3(bucket=bucket, key=key, endpoint_url=endpoint_url)
    result = train_next_move_logistic_classifier(
        df=df,
        test_size=test_size,
        random_state=random_state,
    )
    logger.info("Training metrics: %s", json.dumps(result.metrics, indent=2))
    if artifact_bucket:
        _persist_artifact(
            training=result,
            bucket=artifact_bucket,
            key=artifact_key or "models/training_pipeline.pkl",
            endpoint_url=endpoint_url,
        )
    return result


def _persist_artifact(
    *,
    training: TrainingResult,
    bucket: str,
    key: str,
    endpoint_url: str | None,
    metadata: Dict[str, str] | None = None,
) -> None:
    """Serialize the trained pipeline and push it to S3 for later inference."""
    logger.info("Uploading trained artifacts to s3://%s/%s", bucket, key)
    buffer = io.BytesIO()
    joblib.dump(
        {
            "model": training.model,
            "metrics": training.metrics,
            "feature_names": list(training.feature_names),
        },
        buffer,
    )
    buffer.seek(0)
    session = boto3.session.Session()
    client = session.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )
    client.put_object(Bucket=bucket, Key=key, Body=buffer.read(), Metadata=metadata or {})

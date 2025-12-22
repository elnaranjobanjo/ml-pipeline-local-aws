import io
import json
import sys
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = SERVICE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

SERVICES_DIR = Path(__file__).resolve().parents[2]
LAYER_DIR = SERVICES_DIR / "model_service" / "layer" / "python"
if LAYER_DIR.exists() and str(LAYER_DIR) not in sys.path:
    sys.path.append(str(LAYER_DIR))

import handler  # noqa: E402


SAMPLE_CSV = """timestamp,symbol,sequence,price,volume,label
2023-01-01T00:00:00Z,BTC,0,100,10,up
2023-01-01T00:01:00Z,BTC,1,105,12,down
"""


def test_engineered_features_include_expected_columns():
    rows = [
        {"timestamp": "ts", "symbol": "X", "sequence": 0, "price": 10.0, "volume": 5.0, "label": "up"},
        {"timestamp": "ts2", "symbol": "X", "sequence": 1, "price": 12.0, "volume": 6.0, "label": "down"},
    ]
    features = handler._engineer_features(rows)
    assert len(features) == 2
    assert set(features[0]) >= {
        "timestamp",
        "symbol",
        "sequence",
        "label",
        "price_change",
        "price_change_pct_of_avg",
        "normalized_volume",
    }


def test_lambda_handler_transforms_and_uploads(monkeypatch):
    stored = {}

    class FakeClient:
        def get_object(self, *, Bucket, Key):
            return {"Body": io.BytesIO(SAMPLE_CSV.encode("utf-8"))}

        def put_object(self, *, Bucket, Key, Body, ContentType):
            stored.update({"Bucket": Bucket, "Key": Key, "Body": Body, "ContentType": ContentType})

    monkeypatch.setattr(handler, "_s3_client", lambda endpoint_url=None: FakeClient())
    response = handler.lambda_handler(
        {
            "source_bucket": "input-bucket",
            "source_key": "data/raw.csv",
            "feature_bucket": "feature-bucket",
            "feature_key": "features/${uuid}.jsonl",
            "uuid": "run-123",
        },
        None,
    )

    assert response["statusCode"] == 200
    payload = json.loads(response["body"])
    assert payload["feature_bucket"] == "feature-bucket"
    assert payload["feature_key"].endswith("run-123.jsonl")
    assert payload["feature_count"] == 2

    assert stored["Bucket"] == "feature-bucket"
    assert stored["Key"].endswith("run-123.jsonl")
    stored_rows = [json.loads(line) for line in stored["Body"].decode("utf-8").splitlines()]
    assert stored_rows[0]["price"] == 100.0
    assert "normalized_volume" in stored_rows[0]

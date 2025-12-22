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


def test_lambda_handler_returns_predictions(monkeypatch):
    artifact = {"generated_at": "now", "metrics": {"row_count": 3}}

    class FakeClient:
        pass

    monkeypatch.setattr(handler, "_s3_client", lambda endpoint_url=None: FakeClient())
    monkeypatch.setattr(handler, "_load_artifact", lambda *_: artifact)
    response = handler.lambda_handler(
        {
            "artifact_bucket": "artifacts",
            "artifact_key": "models/run.json",
            "inputs": [
                {"sequence": 1, "price": 2.0, "normalized_volume": 0.4},
                {"sequence": 2, "price": 0.5, "normalized_volume": 0.1},
            ],
        },
        None,
    )

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["artifact_bucket"] == "artifacts"
    assert body["prediction_count"] == 2
    assert all("prediction" in row for row in body["predictions"])


def test_lambda_handler_handles_non_list_inputs(monkeypatch):
    artifact = {"generated_at": None, "metrics": {"row_count": 1}}
    monkeypatch.setattr(handler, "_s3_client", lambda endpoint_url=None: object())
    monkeypatch.setattr(handler, "_load_artifact", lambda *_: artifact)
    response = handler.lambda_handler({"inputs": "invalid"}, None)
    body = json.loads(response["body"])
    assert body["prediction_count"] == 0

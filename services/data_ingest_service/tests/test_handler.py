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


def test_generate_rows_respects_batch_size():
    rows = handler._generate_rows(batch_size=4, symbol="UNIT")
    assert len(rows) == 4
    assert all(row["symbol"] == "UNIT" for row in rows)
    assert all("timestamp" in row for row in rows)


def test_lambda_handler_uploads_csv(monkeypatch):
    uploads = []

    class FakeClient:
        def put_object(self, *, Bucket, Key, Body, ContentType):
            uploads.append({"Bucket": Bucket, "Key": Key, "Body": Body, "ContentType": ContentType})

    class FakeUUID:
        def __str__(self) -> str:
            return "fixed-id"

    monkeypatch.setattr(handler, "_s3_client", lambda endpoint_url=None: FakeClient())
    monkeypatch.setattr(handler.uuid, "uuid4", lambda: FakeUUID())
    response = handler.lambda_handler(
        {"bucket": "demo", "key": "data/batch-${uuid}.csv", "batch_size": 2, "symbol": "BTC"}, None
    )

    assert response["statusCode"] == 200
    payload = json.loads(response["body"])
    assert payload["bucket"] == "demo"
    assert payload["records"] == 2

    assert len(uploads) == 1
    upload = uploads[0]
    assert upload["Bucket"] == "demo"
    assert upload["Key"] == "data/batch-fixed-id.csv"
    body_text = upload["Body"].decode("utf-8")
    header, *rows = body_text.strip().splitlines()
    assert header == "timestamp,symbol,sequence,price,volume,label"
    assert len(rows) == 2

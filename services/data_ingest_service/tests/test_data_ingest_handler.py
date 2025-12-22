import importlib.util
import json
import sys
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = SERVICE_DIR / "src"
LAYER_DIR = Path(__file__).resolve().parents[2] / "model_service" / "layer" / "python"
if LAYER_DIR.exists() and str(LAYER_DIR) not in sys.path:
    sys.path.append(str(LAYER_DIR))


def _load_handler():
    spec = importlib.util.spec_from_file_location(
        "data_ingest_service_handler", SRC_DIR / "handler.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


handler = _load_handler()


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

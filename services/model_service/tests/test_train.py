import io
import json
import sys
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = SERVICE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

LAYER_DIR = SERVICE_DIR / "layer" / "python"
if LAYER_DIR.exists() and str(LAYER_DIR) not in sys.path:
    sys.path.append(str(LAYER_DIR))

import train  # noqa: E402


def test_run_training_summarizes_and_uploads(monkeypatch):
    sample_csv = "a,b\n1,2\n3,4\n"
    saved_payload = {}

    class FakeClient:
        def get_object(self, *, Bucket, Key):
            assert Bucket == "input-bucket"
            assert Key == "sample.csv"
            return {"Body": io.BytesIO(sample_csv.encode("utf-8"))}

        def put_object(self, *, Bucket, Key, Body, ContentType):
            saved_payload.update({"Bucket": Bucket, "Key": Key, "Body": Body, "ContentType": ContentType})

    monkeypatch.setattr(train, "_s3_client", lambda endpoint_url=None: FakeClient())
    result = train.run_training(
        bucket="input-bucket",
        key="sample.csv",
        endpoint_url=None,
        artifact_bucket="artifacts",
        artifact_key="models/sample.json",
    )

    assert result.metrics["row_count"] == 2
    assert result.metrics["column_count"] == 2
    assert result.artifact_bucket == "artifacts"
    assert saved_payload["Bucket"] == "artifacts"
    assert saved_payload["Key"] == "models/sample.json"
    artifact = json.loads(saved_payload["Body"].decode("utf-8"))
    assert artifact["source"] == {"bucket": "input-bucket", "key": "sample.csv"}
    assert artifact["metrics"]["row_count"] == 2.0

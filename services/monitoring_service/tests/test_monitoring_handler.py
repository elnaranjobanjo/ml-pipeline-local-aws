import json
import sys
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = SERVICE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

import handler  # noqa: E402


def test_lambda_handler_reports_accuracy_and_drift():
    predictions = [
        {"prediction": "buy"},
        {"prediction": "hold"},
        {"prediction": "buy"},
    ]
    actuals = ["buy", "sell", "buy"]
    response = handler.lambda_handler(
        {"predictions": predictions, "actuals": actuals, "dataset_tag": "unit"}, None
    )

    assert response["statusCode"] == 200
    payload = json.loads(response["body"])
    assert payload["dataset_tag"] == "unit"
    assert payload["prediction_count"] == 3
    assert payload["accuracy"] == round(2 / 3, 4)
    assert payload["drift_score"] >= 0.0
    assert payload["label_distribution"]["buy"] == 2

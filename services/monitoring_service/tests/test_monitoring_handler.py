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
        "monitoring_service_handler", SRC_DIR / "handler.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


handler = _load_handler()


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

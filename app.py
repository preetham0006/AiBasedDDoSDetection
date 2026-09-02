from pathlib import Path
from datetime import datetime
import json
import joblib
import pandas as pd

from flask import Flask, jsonify, render_template, request


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "model"

app = Flask(__name__)


# ============================================================
# MODEL CONFIGURATION
# ============================================================

MODEL_PATHS = {
    "Random Forest": MODEL_DIR / "random_forest.pkl",
    "Logistic Regression": MODEL_DIR / "logistic_regression.pkl",
    "Neural Network": MODEL_DIR / "neural_network.pkl",
}

FEATURES_PATH = MODEL_DIR / "feature_names.json"
METRICS_PATH = MODEL_DIR / "metrics.json"


# ============================================================
# GLOBAL STATE
# ============================================================

models = {}
feature_names = []
metrics = {}

# Default model
active_model = "Random Forest"

events = []
blocked_ips = set()

stats = {
    "total": 0,
    "ddos": 0,
    "benign": 0,
    "last_confidence": 0.0
}


# ============================================================
# LOAD MODELS
# ============================================================

def load_models():

    global models
    global feature_names
    global metrics

    models = {}

    print("\nLoading models...")

    # Load all three models
    for model_name, model_path in MODEL_PATHS.items():

        if model_path.exists():

            try:
                models[model_name] = joblib.load(model_path)
                print(f"✓ {model_name} loaded")

            except Exception as exc:
                print(f"✗ Failed to load {model_name}: {exc}")

        else:
            print(f"✗ {model_name} not found:")
            print(f"  {model_path}")

    # Load feature names
    if FEATURES_PATH.exists():

        try:
            feature_names = json.loads(
                FEATURES_PATH.read_text(encoding="utf-8")
            )

            print(f"✓ Feature names loaded: {len(feature_names)}")

        except Exception as exc:
            print(f"✗ Failed to load feature names: {exc}")

    else:
        print("✗ feature_names.json not found")

    # Load metrics
    if METRICS_PATH.exists():

        try:
            metrics = json.loads(
                METRICS_PATH.read_text(encoding="utf-8")
            )

            print("✓ Model metrics loaded")

        except Exception as exc:
            print(f"✗ Failed to load metrics: {exc}")

    else:
        print("✗ metrics.json not found")

    print("\nAvailable models:")

    for model_name in models:
        print(f"  • {model_name}")

    print()


# Load models when Flask starts
load_models()


# ============================================================
# HOME PAGE
# ============================================================

@app.get("/")
def index():

    return render_template(
        "index.html",

        model_ready=len(models) > 0,

        feature_count=len(feature_names),

        active_model=active_model,

        available_models=list(models.keys()),

        metrics=metrics
    )


# ============================================================
# STATUS API
# ============================================================

@app.get("/api/status")
def status():

    return jsonify({

        "model_ready": len(models) > 0,

        "feature_count": len(feature_names),

        "available_models": list(models.keys()),

        "active_model": active_model,

        "metrics": metrics,

        "stats": stats,

        "blocked_ips": sorted(blocked_ips),

        "recent_events": events[-20:][::-1]
    })


# ============================================================
# CHANGE ACTIVE MODEL
# ============================================================

@app.post("/api/model")
def change_model():

    global active_model

    payload = request.get_json(silent=True) or {}

    requested_model = payload.get("model")

    if requested_model not in models:

        return jsonify({
            "error": "Model not available",
            "available_models": list(models.keys())
        }), 400

    active_model = requested_model

    print(f"Active model changed to: {active_model}")

    return jsonify({

        "ok": True,

        "active_model": active_model,

        "available_models": list(models.keys())
    })


# ============================================================
# PREDICTION API
# ============================================================

@app.post("/api/predict")
def predict():

    if not models:

        return jsonify({
            "error": "No models loaded. Run: python train_model.py"
        }), 503

    payload = request.get_json(silent=True) or {}

    features = payload.get("features", {})

    source_ip = str(
        payload.get(
            "source_ip",
            "127.0.0.1"
        )
    )

    # --------------------------------------------------------
    # Check requested model
    # --------------------------------------------------------

    model_name = payload.get(
        "model",
        active_model
    )

    if model_name not in models:

        return jsonify({
            "error": f"Model '{model_name}' is not available",
            "available_models": list(models.keys())
        }), 400

    model = models[model_name]

    # --------------------------------------------------------
    # Check features
    # --------------------------------------------------------

    missing = [
        feature
        for feature in feature_names
        if feature not in features
    ]

    if missing:

        return jsonify({

            "error": "Missing model features",

            "missing": missing[:20]

        }), 400

    # --------------------------------------------------------
    # Create DataFrame
    # --------------------------------------------------------

    try:

        row = pd.DataFrame(
            [
                [
                    features[feature]
                    for feature in feature_names
                ]
            ],
            columns=feature_names
        )

    except Exception as exc:

        return jsonify({
            "error": f"Failed to prepare features: {exc}"
        }), 400

    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    try:

        prediction = int(
            model.predict(row)[0]
        )

        probabilities = model.predict_proba(row)[0]

        confidence = float(
            max(probabilities)
        )

    except Exception as exc:

        return jsonify({
            "error": f"Prediction failed: {exc}"
        }), 400

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    if prediction == 1:

        label = "DDoS"

    else:

        label = "BENIGN"

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    stats["total"] += 1

    if prediction == 1:

        stats["ddos"] += 1

    else:

        stats["benign"] += 1

    stats["last_confidence"] = confidence

    # --------------------------------------------------------
    # Application-level mitigation
    # --------------------------------------------------------

    action = "MONITORED"

    if prediction == 1 and confidence >= 0.90:

        blocked_ips.add(source_ip)

        action = "BLOCKED"

    # --------------------------------------------------------
    # Event
    # --------------------------------------------------------

    event = {

        "time": datetime.now().strftime("%H:%M:%S"),

        "source_ip": source_ip,

        "model": model_name,

        "label": label,

        "confidence": round(
            confidence * 100,
            2
        ),

        "action": action
    }

    events.append(event)

    # Keep only latest 200 events
    if len(events) > 200:

        del events[:-200]

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return jsonify({

        "prediction": prediction,

        "label": label,

        "confidence": round(
            confidence,
            4
        ),

        "action": action,

        "source_ip": source_ip,

        "model": model_name
    })


# ============================================================
# UNBLOCK IP
# ============================================================

@app.post("/api/unblock")
def unblock():

    payload = request.get_json(silent=True) or {}

    ip = str(
        payload.get(
            "ip",
            ""
        )
    )

    blocked_ips.discard(ip)

    return jsonify({

        "ok": True,

        "blocked_ips": sorted(
            blocked_ips
        )
    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("DDoS SECURITY MONITOR")
    print("=" * 60)

    print(
        f"Active model: {active_model}"
    )

    print(
        f"Models loaded: {len(models)}"
    )

    print(
        f"Features: {len(feature_names)}"
    )

    print("=" * 60 + "\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
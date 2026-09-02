from pathlib import Path
import json
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score
)


# ============================================================
# 1. PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "data" / "DDos.csv"
MODEL_DIR = BASE_DIR / "model"

MODEL_DIR.mkdir(exist_ok=True)


# ============================================================
# 2. CHECK DATASET
# ============================================================

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"{DATA_PATH} not found.\n"
        "Copy DDos.csv into the project's data folder."
    )


# ============================================================
# 3. LOAD DATASET
# ============================================================

print("\nLoading dataset...")

df = pd.read_csv(DATA_PATH)

# Remove unnecessary whitespace from column names
df.columns = df.columns.str.strip()

print(f"Original dataset shape: {df.shape}")


# ============================================================
# 4. DATA PREPROCESSING
# ============================================================

data_f = df.dropna().copy()

if "Label" not in data_f.columns:
    raise ValueError(
        "Expected a 'Label' column in DDos.csv."
    )

# Convert labels into numerical values
#
# BENIGN = 0
# DDoS   = 1

data_f["Label"] = data_f["Label"].map({
    "BENIGN": 0,
    "DDoS": 1
})

# Remove rows where the label could not be mapped
data_f = data_f.dropna(subset=["Label"])

# Separate features and target
X = data_f.drop("Label", axis=1)
y = data_f["Label"]


# ============================================================
# 5. CHECK FEATURES
# ============================================================

non_numeric = X.select_dtypes(
    exclude="number"
).columns.tolist()

if non_numeric:

    raise ValueError(
        "The supplied notebook expects numeric model inputs.\n"
        f"Non-numeric columns found: {non_numeric}"
    )


print(f"Processed dataset shape: {X.shape}")
print(f"Number of features: {X.shape[1]}")
print(f"Number of samples: {X.shape[0]}")


# ============================================================
# 6. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.30,
    random_state=42
)

print("\nDataset split:")
print(f"Training samples: {len(X_train)}")
print(f"Testing samples : {len(X_test)}")


# ============================================================
# 7. DEFINE THREE MODELS
# ============================================================

models = {

    # --------------------------------------------------------
    # MODEL 1: RANDOM FOREST
    # --------------------------------------------------------

    "Random Forest": RandomForestClassifier(
        n_estimators=50,
        random_state=42
    ),


    # --------------------------------------------------------
    # MODEL 2: LOGISTIC REGRESSION
    # --------------------------------------------------------

    "Logistic Regression": LogisticRegression(
        random_state=42
    ),


    # --------------------------------------------------------
    # MODEL 3: NEURAL NETWORK
    # --------------------------------------------------------

    "Neural Network": MLPClassifier(
        hidden_layer_sizes=(10,),
        max_iter=10,
        random_state=42
    )
}


# ============================================================
# 8. TRAIN AND EVALUATE ALL THREE MODELS
# ============================================================

results = {}

print("\n" + "=" * 60)
print("TRAINING MODELS")
print("=" * 60)


for name, model in models.items():

    print(f"\nTraining {name}...")

    # Train
    model.fit(X_train, y_train)

    # Predict
    predictions = model.predict(X_test)

    # Calculate metrics
    accuracy = accuracy_score(
        y_test,
        predictions
    )

    f1 = f1_score(
        y_test,
        predictions
    )

    precision = precision_score(
        y_test,
        predictions
    )

    recall = recall_score(
        y_test,
        predictions
    )

    # Store results
    results[name] = {
        "accuracy": round(float(accuracy), 4),
        "f1": round(float(f1), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4)
    }

    print(f"Accuracy : {accuracy:.4f}")
    print(f"F1 Score : {f1:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")


# ============================================================
# 9. SAVE MODELS
# ============================================================

print("\n" + "=" * 60)
print("SAVING MODELS")
print("=" * 60)


# Random Forest
joblib.dump(
    models["Random Forest"],
    MODEL_DIR / "random_forest.pkl"
)

print("✓ Random Forest saved")


# Logistic Regression
joblib.dump(
    models["Logistic Regression"],
    MODEL_DIR / "logistic_regression.pkl"
)

print("✓ Logistic Regression saved")


# Neural Network
joblib.dump(
    models["Neural Network"],
    MODEL_DIR / "neural_network.pkl"
)

print("✓ Neural Network saved")


# ============================================================
# 10. SAVE FEATURE NAMES
# ============================================================

feature_names = list(X.columns)

(MODEL_DIR / "feature_names.json").write_text(
    json.dumps(feature_names, indent=2),
    encoding="utf-8"
)

print("✓ Feature names saved")


# ============================================================
# 11. SAVE MODEL METRICS
# ============================================================

metrics_data = {

    "models": results,

    "dataset": {
        "total_samples": int(len(X)),
        "training_samples": int(len(X_train)),
        "testing_samples": int(len(X_test)),
        "features": int(X.shape[1])
    },

    "training_configuration": {
        "test_size": 0.30,
        "random_state": 42
    }
}


(MODEL_DIR / "metrics.json").write_text(
    json.dumps(
        metrics_data,
        indent=4
    ),
    encoding="utf-8"
)

print("✓ Model metrics saved")


# ============================================================
# 12. DISPLAY FINAL COMPARISON
# ============================================================

print("\n")
print("=" * 70)
print("MODEL COMPARISON")
print("=" * 70)

print(
    f"{'Model':<25}"
    f"{'Accuracy':<12}"
    f"{'F1':<12}"
    f"{'Precision':<12}"
    f"{'Recall':<12}"
)

print("-" * 70)

for name, metrics in results.items():

    print(
        f"{name:<25}"
        f"{metrics['accuracy']:<12.4f}"
        f"{metrics['f1']:<12.4f}"
        f"{metrics['precision']:<12.4f}"
        f"{metrics['recall']:<12.4f}"
    )

print("=" * 70)


# ============================================================
# 13. FINISHED
# ============================================================

print("\nModels successfully trained and saved.")

print("\nModel directory:")

print(MODEL_DIR)

print("\nFiles created:")

print("  random_forest.pkl")
print("  logistic_regression.pkl")
print("  neural_network.pkl")
print("  feature_names.json")
print("  metrics.json")
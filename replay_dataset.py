"""
Safe local demonstration:
replays rows from your own DDos.csv to the Flask API.
It does not generate packets, scan hosts, or attack a network.
"""
from pathlib import Path
import time
import random
import requests
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "DDos.csv"

API_URL = "http://127.0.0.1:5000/api/predict"
DELAY_SECONDS = 1.0
ROWS = 50

df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.strip()
df = df.dropna().copy()
df["Label"] = df["Label"].map({"BENIGN": 0, "DDoS": 1})
df = df.dropna(subset=["Label"])

feature_names = [c for c in df.columns if c != "Label"]

# Mix rows so the dashboard demonstrates both classes when available.
benign = df[df["Label"] == 0]
ddos = df[df["Label"] == 1]

rows = []
if not benign.empty:
    rows.extend(benign.sample(min(ROWS // 2, len(benign)), random_state=42).to_dict("records"))
if not ddos.empty:
    rows.extend(ddos.sample(min(ROWS // 2, len(ddos)), random_state=7).to_dict("records"))

random.shuffle(rows)

for row in rows:
    features = {f: float(row[f]) for f in feature_names}
    source_ip = f"10.0.0.{random.randint(2, 254)}"

    response = requests.post(
        API_URL,
        json={"features": features, "source_ip": source_ip},
        timeout=5,
    )
    print(response.json())
    time.sleep(DELAY_SECONDS)

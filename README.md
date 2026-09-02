# AI-Powered DDoS Detection & Mitigation Dashboard

A defensive, local demonstration system built around the Random Forest model from the supplied `main_file.ipynb`.

## What is reused from the notebook?

The notebook trains three models, but this application uses the **Random Forest** model because it is a practical choice for deployment.

The training pipeline mirrors the supplied notebook:

1. Load `data/DDos.csv`
2. Strip whitespace from column names
3. Drop null rows
4. Convert `BENIGN -> 0` and `DDoS -> 1`
5. Split with `test_size=0.30, random_state=42`
6. Train `RandomForestClassifier(n_estimators=50, random_state=42)`
7. Save the trained model and exact feature order

## Project architecture

Dataset -> Feature vector -> Random Forest -> BENIGN/DDoS -> confidence
                                                    |
                                                    +-> dashboard
                                                    +-> local application-level block list
                                                    +-> event log in memory

The "blocking" in this demo is application-level only. It does not modify the Windows firewall.

## Setup

PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy the dataset from the reference repository into:

```text
data/DDos.csv
```

Train/export the model:

```powershell
python train_model.py
```

Start the dashboard:

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

In another terminal, replay local dataset rows:

```powershell
python replay_dataset.py
```

## Important

The supplied notebook does not save a deployment artifact. The model exists after the notebook's training cell runs. Therefore `train_model.py` reproduces that Random Forest training step and serializes it to `model/ddos_random_forest.pkl`.

The notebook also imports `StandardScaler` but does not actually apply it before training the Random Forest. This project therefore does not introduce a scaler, keeping inference consistent with the supplied notebook.

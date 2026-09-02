# AI-Powered DDoS Detection and Mitigation System

An ML-based system for detecting DDoS network traffic and demonstrating automated mitigation through a real-time monitoring dashboard.

## Features

* Classifies network traffic as **BENIGN** or **DDoS**
* Uses **78 network-traffic features** for classification
* Compares **Random Forest, Logistic Regression, and MLP Neural Network**
* Achieved **99.95% test accuracy** using Random Forest
* Flask backend for model inference and traffic monitoring
* Confidence-based application-level IP blocking
* Real-time dashboard for detection statistics and traffic history
* Dataset replay for end-to-end system testing

## Tech Stack

**Frontend:** HTML, CSS, JavaScript
**Backend:** Python, Flask
**Machine Learning:** Scikit-learn
**Libraries:** Pandas, NumPy, Joblib

## System Flow

```text
Network Traffic Dataset
        ↓
Data Preprocessing
        ↓
ML Models
(Random Forest / Logistic Regression / MLP)
        ↓
Flask Backend
        ↓
Traffic Classification
        ↓
BENIGN / DDoS
        ↓
Monitoring & Mitigation Dashboard
```

## Running the Project

```bash
pip install -r requirements.txt
python train_model.py
python app.py
```

To simulate incoming traffic for testing:

```bash
python replay_dataset.py
```

Then open the Flask application in your browser.

## Note

The current implementation uses **dataset replay to simulate incoming network traffic**. IP blocking is implemented at the application level; live packet capture and OS-level firewall mitigation can be added as future enhancements.

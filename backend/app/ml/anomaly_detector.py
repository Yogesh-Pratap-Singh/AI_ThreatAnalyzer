import os
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest.joblib")

class AnomalyDetector:
    def __init__(self):
        self.model = None
        self._load_or_train_model()

    def _load_or_train_model(self):
        # Ensure directory exists
        os.makedirs(MODEL_DIR, exist_ok=True)
        
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                return
            except Exception:
                pass
        
        # Train a default baseline model
        self.train_baseline_model()

    def train_baseline_model(self):
        # Generate synthetic normal baseline traffic:
        # Features: [hour_of_day, bytes_transferred, dest_port, is_internal_dest, protocol_encoded, events_from_ip_last_hour]
        np.random.seed(42)
        n_samples = 1000
        
        # Hours mostly centered around working hours (8 AM - 6 PM)
        probs = np.array([
            0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.03, 0.05,
            0.08, 0.09, 0.10, 0.09, 0.08, 0.08, 0.09, 0.09,
            0.08, 0.06, 0.04, 0.02, 0.02, 0.01, 0.01, 0.01
        ])
        probs = probs / probs.sum()
        hours = np.random.choice(range(24), size=n_samples, p=probs)
        
        # Small bytes transferred (e.g. 500 bytes to 10 KB)
        bytes_tx = np.random.exponential(scale=5000, size=n_samples) + 100
        
        # Mostly internal ports or 80/443
        ports = np.random.choice([80, 443, 8080, 22, 3000, 5432], size=n_samples, p=[
            0.1, 0.6, 0.1, 0.05, 0.1, 0.05
        ])
        
        # Mostly internal destination (0.8 probability)
        is_internal = np.random.choice([0, 1], size=n_samples, p=[0.2, 0.8])
        
        # Mostly TCP (0.7), UDP (0.25), ICMP (0.05)
        protocols = np.random.choice([1, 2, 3], size=n_samples, p=[0.7, 0.25, 0.05])
        
        # Low frequency per hour (mostly 1 to 10 events)
        frequency = np.random.poisson(lam=3, size=n_samples) + 1
        
        X_train = np.column_stack((hours, bytes_tx, ports, is_internal, protocols, frequency))
        
        # Train Isolation Forest
        self.model = IsolationForest(contamination=0.05, n_estimators=200, random_state=42)
        self.model.fit(X_train)
        
        # Save model
        joblib.dump(self.model, MODEL_PATH)

    def score_event(self, features: np.ndarray) -> float:
        """
        Scores a single event. Returns a float between 0.0 and 1.0.
        Higher scores indicate higher likelihood of being an anomaly.
        """
        if self.model is None:
            self._load_or_train_model()
            
        X = features.reshape(1, -1)
        # decision_function returns value in range [-0.5, 0.5]
        # where -0.5 is outlier and +0.5 is inlier.
        dec_score = float(self.model.decision_function(X)[0])
        
        # Normalize decision function output to 0.0 - 1.0 where 1.0 is anomalous
        anomaly_score = 0.5 - dec_score
        anomaly_score = max(0.0, min(1.0, anomaly_score))
        return round(anomaly_score, 4)

detector = AnomalyDetector()

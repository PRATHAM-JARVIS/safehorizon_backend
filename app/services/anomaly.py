import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Any, Optional, Tuple
import joblib
import os
from datetime import datetime, timedelta
from ..models.model_registry import save_model, load_model
from ..config import get_settings

settings = get_settings()


class AnomalyDetector:
    def __init__(self):
        self.isolation_forest: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_columns = [
            'speed', 'lat', 'lon', 'hour', 'day_of_week', 
            'distance_from_previous', 'time_since_previous'
        ]
        
    def _load_models(self):
        """Load trained models from disk"""
        try:
            self.isolation_forest = load_model("isolation_forest")
            self.scaler = load_model("anomaly_scaler")
        except FileNotFoundError:
            # Models not trained yet
            pass
    
    def _extract_features(self, locations_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Extract features from location data for anomaly detection"""
        if not locations_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(locations_data)
        
        # Convert timestamp to datetime if it's a string
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Sort by timestamp to calculate movement features
        df = df.sort_values('timestamp')
        
        # Calculate distance from previous location
        df['prev_lat'] = df['latitude'].shift(1)
        df['prev_lon'] = df['longitude'].shift(1)
        df['distance_from_previous'] = np.sqrt(
            (df['latitude'] - df['prev_lat'])**2 + 
            (df['longitude'] - df['prev_lon'])**2
        ) * 111000  # Convert to meters approximately
        
        # Calculate time since previous location
        df['prev_timestamp'] = df['timestamp'].shift(1)
        df['time_since_previous'] = (
            df['timestamp'] - df['prev_timestamp']
        ).dt.total_seconds()
        
        # Fill NaN values for first record
        df.fillna(0, inplace=True)
        
        # Rename columns to match feature_columns
        df.rename(columns={'latitude': 'lat', 'longitude': 'lon'}, inplace=True)
        
        # Select only the features we need
        return df[self.feature_columns]
    
    async def train(self, locations_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train the anomaly detection model"""
        if len(locations_data) < 50:
            return {"status": "insufficient_data", "message": "Need at least 50 location points"}
        
        # Extract features
        features_df = self._extract_features(locations_data)
        
        if features_df.empty:
            return {"status": "error", "message": "No features extracted"}
        
        # Scale features
        self.scaler = StandardScaler()
        features_scaled = self.scaler.fit_transform(features_df)
        
        # Train Isolation Forest
        self.isolation_forest = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42,
            n_estimators=100
        )
        self.isolation_forest.fit(features_scaled)
        
        # Save models
        save_model(self.isolation_forest, "isolation_forest")
        save_model(self.scaler, "anomaly_scaler")
        
        return {
            "status": "success", 
            "message": f"Model trained on {len(features_df)} samples",
            "contamination": 0.1
        }
    
    async def score_point(self, location_data: Dict[str, Any]) -> float:
        """Score a single location point for anomaly"""
        if not self.isolation_forest or not self.scaler:
            self._load_models()
        
        if not self.isolation_forest or not self.scaler:
            # No model trained yet, return neutral score
            return 0.0
        
        # For single point scoring, we need to provide some context
        # Use the single point multiple times to create a minimal sequence
        extended_data = [location_data.copy() for _ in range(3)]
        
        # Convert to features
        features_df = self._extract_features(extended_data)
        
        if features_df.empty:
            return 0.0
        
        # Use only the first row (original point) for scoring
        features_single = features_df.iloc[0:1]
        
        # Scale features
        features_scaled = self.scaler.transform(features_single)
        
        # Get anomaly score (negative values are more anomalous)
        score = self.isolation_forest.decision_function(features_scaled)[0]
        
        # Convert to 0-1 scale where higher values indicate more anomalous behavior
        # Isolation Forest returns values roughly between -0.5 and 0.5
        normalized_score = max(0, min(1, (0.5 - score)))
        
        return float(normalized_score)


# Global instance
anomaly_detector = AnomalyDetector()


async def score_point(features: Dict[str, Any]) -> float:
    """Score a single point for anomaly detection"""
    return await anomaly_detector.score_point(features)


async def train_anomaly_model(locations_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Train the anomaly detection model"""
    return await anomaly_detector.train(locations_data)

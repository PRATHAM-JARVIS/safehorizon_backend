from typing import Any, Dict, List, Optional
import asyncio
from .geofence import check_point
from .anomaly import score_point
from .sequence import score_sequence


class SafetyScorer:
    def __init__(self):
        # Weights for different scoring components
        self.weights = {
            "geofence": 0.4,      # 40% weight for geofence violations
            "anomaly": 0.3,       # 30% weight for anomaly detection
            "sequence": 0.2,      # 20% weight for sequence analysis
            "manual": 0.1         # 10% weight for manual adjustments
        }
        
        # Risk level mappings
        self.geofence_scores = {
            "safe": 0.0,
            "risky": 0.6,
            "restricted": 1.0
        }
    
    async def compute_safety_score(self, context: Dict[str, Any]) -> int:
        """
        Compute comprehensive safety score (0-100, where 100 is safest)
        
        Args:
            context: Dictionary containing:
                - lat, lon: Current location
                - location_history: List of recent locations for sequence analysis
                - current_location_data: Current location data for anomaly detection
                - manual_adjustment: Optional manual score adjustment (-20 to +20)
        """
        lat = context.get("lat")
        lon = context.get("lon")
        location_history = context.get("location_history", [])
        current_location_data = context.get("current_location_data", {})
        manual_adjustment = context.get("manual_adjustment", 0)
        
        if not lat or not lon:
            return 50  # Neutral score if no location
        
        scores = {}
        
        # 1. Geofence Score
        try:
            geofence_result = await check_point(lat, lon)
            risk_level = geofence_result.get("risk_level", "safe")
            geofence_risk = self.geofence_scores.get(risk_level, 0.0)
            scores["geofence"] = geofence_risk
        except Exception:
            scores["geofence"] = 0.0  # Default to safe if error
        
        # 2. Anomaly Score
        try:
            if current_location_data:
                anomaly_score = await score_point(current_location_data)
                scores["anomaly"] = min(1.0, anomaly_score)
            else:
                scores["anomaly"] = 0.0
        except Exception:
            scores["anomaly"] = 0.0
        
        # 3. Sequence Score
        try:
            if len(location_history) >= 5:  # Need minimum points for sequence
                sequence_score = await score_sequence(location_history)
                scores["sequence"] = min(1.0, sequence_score)
            else:
                scores["sequence"] = 0.0
        except Exception:
            scores["sequence"] = 0.0
        
        # 4. Manual Adjustment (normalized to 0-1 scale)
        # Manual adjustment should be between -20 and +20 points, convert to risk adjustment
        manual_risk_adjustment = max(-0.2, min(0.2, manual_adjustment / 100))  # -20 to +20 -> -0.2 to +0.2
        scores["manual"] = manual_risk_adjustment
        
        # Calculate weighted risk score (0-1, where 1 is highest risk)
        weighted_risk = sum(
            scores[component] * self.weights[component] 
            for component in self.weights.keys()
        )
        
        # Convert to safety score (0-100, where 100 is safest)
        safety_score = max(0, min(100, int((1 - weighted_risk) * 100)))
        
        return safety_score
    
    async def compute_batch_scores(self, contexts: List[Dict[str, Any]]) -> List[int]:
        """Compute safety scores for multiple contexts"""
        tasks = [self.compute_safety_score(context) for context in contexts]
        return await asyncio.gather(*tasks)
    
    def get_risk_level(self, safety_score: int) -> str:
        """Convert safety score to risk level string"""
        if safety_score >= 80:
            return "low"
        elif safety_score >= 60:
            return "medium"
        elif safety_score >= 40:
            return "high"
        else:
            return "critical"
    
    def should_trigger_alert(self, safety_score: int, threshold: int = 70) -> bool:
        """Determine if an alert should be triggered based on safety score"""
        return safety_score < threshold


# Global instance
safety_scorer = SafetyScorer()


async def compute_safety_score(context: Dict[str, Any]) -> int:
    """Compute comprehensive safety score"""
    return await safety_scorer.compute_safety_score(context)


async def compute_batch_safety_scores(contexts: List[Dict[str, Any]]) -> List[int]:
    """Compute safety scores for multiple contexts"""
    return await safety_scorer.compute_batch_scores(contexts)


def get_risk_level(safety_score: int) -> str:
    """Convert safety score to risk level"""
    return safety_scorer.get_risk_level(safety_score)


def should_trigger_alert(safety_score: int, threshold: int = 70) -> bool:
    """Check if alert should be triggered"""
    return safety_scorer.should_trigger_alert(safety_score, threshold)

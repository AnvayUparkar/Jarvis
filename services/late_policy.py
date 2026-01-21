
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class LatePolicy:
    """
    Deterministic Late Submission Policy.
    Calculates penalties based on distinct rules.
    """
    
    # Constants
    HARD_DEADLINE_BUFFER = timedelta(minutes=15) # Grace period
    PENALTY_PER_DAY = 10 # 10% per day
    MAX_PENALTY = 50 # Cap at 50% deduction
    
    @staticmethod
    def calculate_penalty(due_date_str: str, submission_date_str: str) -> dict:
        """
        Calculate late penalty.
        Returns: { 'is_late': bool, 'penalty_points': int, 'reason': str }
        """
        if not due_date_str or not submission_date_str:
            return {'is_late': False, 'penalty_points': 0, 'reason': "No dates available"}
            
        try:
            # ISO 8601 format usually returned by Graph API: 2023-10-27T23:59:00Z
            # Clean 'Z' for simple parsing if needed, or use dateutil
            due_dt = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
            sub_dt = datetime.fromisoformat(submission_date_str.replace("Z", "+00:00"))
            
            # Apply grace period
            if sub_dt <= due_dt + LatePolicy.HARD_DEADLINE_BUFFER:
                return {'is_late': False, 'penalty_points': 0, 'reason': "On time"}
            
            # Calculate Lateness
            delta = sub_dt - due_dt
            days_late = delta.days + (1 if delta.seconds > 0 else 0)
            
            penalty = min(days_late * LatePolicy.PENALTY_PER_DAY, LatePolicy.MAX_PENALTY)
            
            return {
                'is_late': True,
                'penalty_points': penalty,
                'reason': f"Late by {days_late} day(s). -{penalty}% penalty applied."
            }
            
        except Exception as e:
            logger.error(f"Error calculating late penalty: {e}")
            return {'is_late': False, 'penalty_points': 0, 'reason': "Error checking dates"}

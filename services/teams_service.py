
import logging
import requests
from typing import List, Dict, Optional
from services.teams_auth import get_auth_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URL for Microsoft Graph API
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

class TeamsService:
    """
    Wrapper for Microsoft Graph API Education endpoints.
    Handles data fetching for Classes, Assignments, and Submissions.
    """
    def __init__(self):
        self.auth = get_auth_client()

    def _get_headers(self):
        """Get Authorization headers from Auth client."""
        return self.auth.get_headers()

    def get_classes(self) -> List[Dict]:
        """
        Fetch all classes for the authenticated faculty member.
        GET /education/classes
        """
        logger.info("Fetching classes...")
        url = f"{GRAPH_API_URL}/education/classes"
        response = requests.get(url, headers=self._get_headers())
        
        if response.status_code == 200:
            data = response.json()
            classes = []
            for item in data.get("value", []):
                classes.append({
                    "id": item.get("id"),
                    "displayName": item.get("displayName"),
                    "description": item.get("description", ""),
                    "section": item.get("classCode", "") # Using classCode as proxy for section if available
                })
            logger.info(f"Found {len(classes)} classes.")
            return classes
        else:
            logger.error(f"Failed to fetch classes: {response.text}")
            raise Exception(f"Graph API Error: {response.status_code} - {response.text}")

    def get_assignments(self, class_id: str) -> List[Dict]:
        """
        Fetch published assignments for a specific class.
        GET /education/classes/{id}/assignments
        """
        logger.info(f"Fetching assignments for class {class_id}...")
        url = f"{GRAPH_API_URL}/education/classes/{class_id}/assignments"
        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            data = response.json()
            assignments = []
            for item in data.get("value", []):
                # Filter for published assignments if needed, though API usually returns all visible
                if item.get("status") == "draft": 
                    continue
                
                # Extract max points from rubric or grading setup if available
                # Note: 'grading' property structure depends on assignment type
                max_points = 100 # Default fallback
                if 'grading' in item and item['grading']:
                    # Simplified extraction - actual structure varies
                    pass 
                
                assignments.append({
                    "id": item.get("id"),
                    "displayName": item.get("displayName"),
                    "dueDateTime": item.get("dueDateTime"),
                    "maxPoints": max_points, # Placeholder, needs deep inspection of grading property
                    "rubricUrl": item.get("rubric", {}).get("rubricUrl")
                })
            logger.info(f"Found {len(assignments)} assignments.")
            return assignments
        else:
            logger.error(f"Failed to fetch assignments: {response.text}")
            raise Exception(f"Graph API Error: {response.status_code} - {response.text}")

    def get_submissions(self, class_id: str, assignment_id: str) -> List[Dict]:
        """
        Fetch submissions for a specific assignment.
        GET /education/classes/{id}/assignments/{id}/submissions
        """
        logger.info(f"Fetching submissions for assignment {assignment_id}...")
        url = f"{GRAPH_API_URL}/education/classes/{class_id}/assignments/{assignment_id}/submissions"
        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            data = response.json()
            submissions = data.get("value", [])
            logger.info(f"Found {len(submissions)} submissions.")
            return submissions
        else:
            logger.error(f"Failed to fetch submissions: {response.text}")
            raise Exception(f"Graph API Error: {response.status_code} - {response.text}")
    
    def patch_submission(self, class_id: str, assignment_id: str, submission_id: str, grade: float, feedback_text: str):
        """
        Update a submission with grade and feedback.
        PATCH /education/classes/{id}/assignments/{id}/submissions/{id}
        """
        logger.info(f"Patching submission {submission_id} with grade {grade}...")
        
        # Note: 'outcomes' endpoint might be preferred for grading resources, 
        # but pure patch on submission is often used for simple feedback.
        # Graph API for grading is complex; standard patching of 'return' logic might be needed.
        # For now, we assume simple property update if supported, or outcome resource.
        
        # Simplified payload for concept
        payload = {
            "feedback": {
                "text": {
                    "content": feedback_text,
                    "contentType": "text"
                }
            }
            # "grade" might need to be set via outcomes endpoint depending on API version
        }
        
        url = f"{GRAPH_API_URL}/education/classes/{class_id}/assignments/{assignment_id}/submissions/{submission_id}/return" 
        # Actually /return is an action. PATCH is for properties.
        # Correct flow: PATCH feedback -> POST return
        
        # 1. Update Feedback
        patch_url = f"{GRAPH_API_URL}/education/classes/{class_id}/assignments/{assignment_id}/submissions/{submission_id}"
        resp_patch = requests.patch(patch_url, json=payload, headers=self._get_headers())
        
        if resp_patch.status_code not in [200, 204]:
             logger.error(f"Failed to patch feedback: {resp_patch.text}")
             return False
             
        # 2. Return submission (publishes Grade) - if auto-return is desired
        # If we just want to save draft, stop here.
        
        return True

# Singleton
_teams_service = None

def get_teams_service():
    global _teams_service
    if _teams_service is None:
        _teams_service = TeamsService()
    return _teams_service


import logging
import json
from services.late_policy import LatePolicy
# import google.generativeai as google_ai # Assumed configured in main.py or globally

logger = logging.getLogger(__name__)

class GradingEngine:
    """
    AI Grading Engine with Strict Mode.
    Analyze submission content -> Check against Rubric -> Apply Late Policy -> Calc Final Grade.
    """
    
    def __init__(self, google_ai_client=None):
        self.ai = google_ai_client # Pass configured client
        
    def grade_submission(self, submission: dict, assignment: dict) -> dict:
        """
        Main grading pipeline.
        
        Args:
            submission: Graph API submission object (contains resources/files)
            assignment: Graph API assignment object (contains max points, instructions/rubric)
            
        Returns:
            dict: { 'grade': float, 'feedback': str, 'breakdown': dict }
        """
        
        # 1. Extract Details
        student_id = submission.get("recipient", {}).get("userId") # or display name
        submission_date = submission.get("submittedDateTime")
        due_date = assignment.get("dueDateTime")
        max_points = assignment.get("maxPoints", 100)
        
        # 2. Check Lateness (Deterministic)
        late_result = LatePolicy.calculate_penalty(due_date, submission_date)
        
        # 3. Extract Content (Text/Files)
        # TODO: Implement file download/text extraction from submission resources
        # For prototype, assume we extract a text summary
        submission_content = "Student submission content placeholder."
        
        # 4. AI Grading (Strict Mode)
        rubric = assignment.get("rubricUrl", "Standard Rubric: Clarity, Correctness, Depth.")
        
        raw_feedback = self._query_llm_grading(submission_content, rubric, max_points)
        
        # 5. Calculate Final Score
        # raw_score comes from LLM
        raw_score = raw_feedback.get("score", 0)
        
        # Apply Caps and Penalties
        final_score = min(raw_score, max_points)
        if late_result['is_late']:
            deduction = (final_score * late_result['penalty_points']) / 100
            final_score -= deduction
            
        # Format Feedback
        feedback_text = f"""
**Grade**: {final_score}/{max_points}
**Status**: {late_result['reason']}

**AI Analysis**:
{raw_feedback.get('comments')}

**Improvement Areas**:
{raw_feedback.get('improvements')}
        """
        
        return {
            "grade": final_score,
            "feedback": feedback_text.strip(),
            "status": "published" # or draft
        }

    def _query_llm_grading(self, content, rubric, max_points) -> dict:
        """
        Query Gemini to grade the submission.
        """
        import google.generativeai as genai
        
        prompt = f"""
        Act as a strict but fair academic grader.
        
        **Assignment Rubric**:
        {rubric}
        
        **Max Points**: {max_points}
        
        **Student Submission**:
        {content}
        
        **Task**:
        1. Grade the submission against the rubric.
        2. Provide constructive feedback.
        3. List specific areas for improvement.
        4. Return ONLY a JSON object:
        {{
            "score": <float>,
            "comments": "<string>",
            "improvements": "<string>"
        }}
        """
        
        try:
            model = genai.GenerativeModel("gemini-2.5-flash") # or config default
            response = model.generate_content(prompt)
            
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
            
        except Exception as e:
            logger.error(f"LLM Grading Error: {e}")
            return {
                "score": 0,
                "comments": "Error during AI analysis.",
                "improvements": "System error."
            }

# Singleton
_grading_engine = None

def get_grading_engine():
    global _grading_engine
    if _grading_engine is None:
        _grading_engine = GradingEngine()
    return _grading_engine

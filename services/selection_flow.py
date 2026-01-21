
import eel
import time
import queue
import logging
from typing import List, Optional
from services.teams_service import get_teams_service

logger = logging.getLogger(__name__)

# Events / Queues to handle Async UI responses
selection_queue = queue.Queue()

class SelectionFlow:
    """
    Manages the interactive selection flow for Teams integration.
    Pauses backend execution while waiting for frontend UI.
    """
    def __init__(self):
        self.teams_service = get_teams_service()

    def select_class(self) -> Optional[str]:
        """
        Trigger UI to select a class.
        Blocking call until user selects or cancels.
        """
        # Fetch classes
        try:
            classes = self.teams_service.get_classes()
            if not classes:
                logger.info("No classes found.")
                return None
        except Exception as e:
            logger.error(f"Error fetching classes: {e}")
            return None

        # Show UI
        logger.info("Requesting Class Selection on UI...")
        try:
            eel.showClassesSelection(classes)
        except Exception as e:
            # Fallback if UI not ready (e.g. headless test)
            logger.warning(f"UI Call failed: {e}")
            return classes[0]['id'] if classes else None

        # Wait for response
        logger.info("Waiting for user selection...")
        selection = self._wait_for_selection()
        
        if selection:
            logger.info(f"User selected class: {selection}")
            return selection
        else:
            logger.info("Selection cancelled.")
            return None

    def select_assignments(self, class_id: str) -> List[str]:
        """
        Trigger UI to select assignments.
        Blocking call.
        """
        # Fetch assignments
        try:
            assignments = self.teams_service.get_assignments(class_id)
            if not assignments:
                logger.info("No assignments found.")
                return []
        except Exception as e:
            logger.error(f"Error fetching assignments: {e}")
            return []

        # Show UI
        logger.info("Requesting Assignment Selection on UI...")
        eel.showAssignmentsSelection(assignments)

        # Wait for response
        logger.info("Waiting for user selection...")
        selection = self._wait_for_selection()
        
        if selection:
             logger.info(f"User selected {len(selection)} assignments.")
             return selection
        else:
             logger.info("Selection cancelled.")
             return []

    def _wait_for_selection(self):
        """Block until frontend responds via Eel exposed methods."""
        # Clear queue first
        with selection_queue.mutex:
            selection_queue.queue.clear()
            
        try:
            # Wait up to 5 minutes just in case
            result = selection_queue.get(timeout=300)
            return result
        except queue.Empty:
            logger.error("Selection timed out.")
            return None

# Singleton
_selection_flow = None

def get_selection_flow():
    global _selection_flow
    if _selection_flow is None:
        _selection_flow = SelectionFlow()
    return _selection_flow

# === EEL EXPOSED HANDLERS ===
@eel.expose
def handle_class_selected(class_id):
    """Callback from Frontend."""
    logger.info(f"Frontend returned Class ID: {class_id}")
    selection_queue.put(class_id)

@eel.expose
def handle_assignments_selected(assignment_ids):
    """Callback from Frontend."""
    logger.info(f"Frontend returned Assignment IDs: {assignment_ids}")
    selection_queue.put(assignment_ids)

@eel.expose
def handle_selection_cancelled():
    """Callback from Frontend."""
    logger.info("Frontend cancelled selection.")
    selection_queue.put(None)

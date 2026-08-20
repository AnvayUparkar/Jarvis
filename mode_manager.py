# mode_manager.py
import logging
import uuid
import time
from enum import Enum, auto

class JarvisMode(Enum):
    TASK_MODE = auto()
    CONVERSATION_MODE = auto()

# Setup structured logger for ModeManager
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s")
logger = logging.getLogger("JarvisModeManager")

# Configurable settings
CONVERSATION_MAX_HISTORY = 10          # Maximum message history turns (1 turn = user + model)
CONVERSATION_TIMEOUT = 60              # Inactivity timeout in seconds
CONVERSATION_MAX_RESPONSE_TOKENS = 150  # Maximum output tokens for LLM generation
CONVERSATION_BARGE_IN = True            # Enable user barge-in during speech synthesis

# VAD settings
VAD_SILENCE_DURATION = 0.8             # Duration of silence to detect end of speech (in seconds)
VAD_MIN_SPEECH_DURATION = 0.3          # Minimum duration of speech to confirm voice activity (in seconds)
VAD_MAX_SPEECH_DURATION = 15.0         # Maximum duration of a single utterance (in seconds)

class ConversationSession:
    def __init__(self):
        self.active = True
        self.conversation_id = str(uuid.uuid4())
        self.message_history = []
        self.start_time = time.time()
        self.last_interaction_time = time.time()

    def touch(self):
        """Update the last interaction time when user speaks or system responds."""
        self.last_interaction_time = time.time()

class ModeManager:
    def __init__(self):
        self._current_mode = JarvisMode.TASK_MODE
        self._session = None
        self._is_loop_running = False

    def get_current_mode(self):
        return self._current_mode

    def is_conversation_mode(self):
        return self._current_mode == JarvisMode.CONVERSATION_MODE

    def is_loop_running(self):
        return self._is_loop_running

    def set_loop_running(self, state: bool):
        self._is_loop_running = state

    def get_session(self):
        return self._session

    def enter_conversation_mode(self):
        if self._current_mode != JarvisMode.CONVERSATION_MODE:
            self._current_mode = JarvisMode.CONVERSATION_MODE
            self._session = ConversationSession()
            logger.info(f"Mode changed: Entered CONVERSATION_MODE (Session ID: {self._session.conversation_id})")
            logger.info("Conversation start")
            return True
        return False

    def exit_conversation_mode(self):
        if self._current_mode != JarvisMode.TASK_MODE:
            self._current_mode = JarvisMode.TASK_MODE
            if self._session:
                self._session.active = False
            self._session = None
            logger.info("Mode changed: Returned to TASK_MODE")
            logger.info("Conversation end")
            return True
        return False

    def add_message(self, role: str, content: str):
        if self._session:
            self._session.message_history.append({"role": role, "parts": [content]})
            
            # Restrict history size (turns * 2 since 1 turn has user and model parts)
            limit = CONVERSATION_MAX_HISTORY * 2
            if len(self._session.message_history) > limit:
                self._session.message_history = self._session.message_history[-limit:]
                
            self._session.touch()
            
            if role == "user":
                logger.info(f"Speech detected / Transcription: {content}")
            elif role == "model":
                logger.info(f"LLM response: {content}")

    def get_history(self):
        if self._session:
            return self._session.message_history
        return []

    def log_error(self, message: str):
        logger.error(message)

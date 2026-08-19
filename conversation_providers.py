# conversation_providers.py
import os
import re
import logging
from openai import OpenAI
import google.generativeai as google_ai

class ConversationProvider:
    def generate_response(self, history) -> str:
        raise NotImplementedError

class GeminiProvider(ConversationProvider):
    def generate_response(self, history) -> str:
        from mode_manager import CONVERSATION_MAX_RESPONSE_TOKENS
        model = google_ai.GenerativeModel(
            'gemini-2.5-flash-lite',
            system_instruction="You are a female virtual assistant named Jarvis. Respond naturally. Always use female gender terms, pronouns, and verb inflections for yourself (e.g., in Marathi use 'करू शकते' instead of 'करू शकतो', and in Hindi use 'कर सकती हूँ' instead of 'कर सकता हूँ'). Keep responses concise for simple questions, but provide details if explicitly requested. Keep the dialogue brief as your response will be read aloud."
        )
        gen_config = {
            "max_output_tokens": CONVERSATION_MAX_RESPONSE_TOKENS,
        }
        response = model.generate_content(history, generation_config=gen_config)
        return response.text

# NVIDIA Conversation Provider
# Currently disabled.
# Google Gemini is the active provider.
# NVIDIA can be enabled in a future phase.
#
# class NvidiaProvider(ConversationProvider):
#     def __init__(self):
#         self.api_key = os.environ.get("NVIDIA_API_KEY")
#         self.base_url = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
#         self.model = os.environ.get("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct")
#         
#         self.client = None
#         if not self.api_key and not ("localhost" in self.base_url or "127.0.0.1" in self.base_url):
#             print("[NVIDIA] API key not configured - NVIDIA provider unavailable")
#             logging.info("[NVIDIA] API key not configured - NVIDIA provider unavailable")
#
#         # Initialize client if API key is present or we are pointing to a local model
#         if self.api_key or "localhost" in self.base_url or "127.0.0.1" in self.base_url:
#             self.client = OpenAI(api_key=self.api_key or "no-key", base_url=self.base_url)
#
#     def generate_response(self, history) -> str:
#         if not self.client:
#             raise ValueError("NVIDIA_API_KEY not configured and NVIDIA_BASE_URL does not point to localhost.")
#             
#         messages = [
#             {
#                 "role": "system",
#                 "content": (
#                     "You are a virtual assistant named Jarvis. Respond naturally. Keep responses concise. "
#                     "You can run actions on the user's system by outputting '[TOOL_CALL: <command>]' where <command> "
#                     "is a natural language command Jarvis supports (e.g., 'open chrome', 'send email to Anvay', 'whats the weather'). "
#                     "Keep the dialogue brief as your response will be read aloud."
#                 )
#             }
#         ]
#         
#         for h in history:
#             role = h["role"]
#             content = h["parts"][0] if h.get("parts") else ""
#             messages.append({
#                 "role": "user" if role == "user" else "assistant",
#                 "content": content
#             })
#             
#         print(f"[AI] model={self.model}")
#         logging.info(f"[AI] model={self.model}")
#         print("[AI] NVIDIA request started")
#         logging.info("[AI] NVIDIA request started")
#         
#         from mode_manager import CONVERSATION_MAX_RESPONSE_TOKENS
#         response = self.client.chat.completions.create(
#             model=self.model,
#             messages=messages,
#             max_tokens=CONVERSATION_MAX_RESPONSE_TOKENS
#         )
#         
#         return response.choices[0].message.content

def get_conversation_provider():
    # NVIDIA Conversation Provider
    # Currently disabled.
    # Google Gemini is the active provider.
    # NVIDIA can be enabled in a future phase.
    print("[AI] provider=existing")
    logging.info("[AI] provider=existing")
    return GeminiProvider()

def parse_and_execute_tool_call(response_text, executor, process_cmd_func):
    """
    Parses response text for [TOOL_CALL: command] tags, validates them for safety,
    executes them asynchronously via the existing Jarvis command parser, and returns
    the cleaned response text.
    """
    match = re.search(r'\[TOOL_CALL:\s*(.*?)\]', response_text, re.IGNORECASE)
    if not match:
        match = re.search(r'\[TOOL:\s*(.*?)\]', response_text, re.IGNORECASE)
        
    if match:
        tool_cmd = match.group(1).strip()
        print(f"[AI] tool_call detected: {tool_cmd}")
        logging.info(f"[AI] tool_call detected: {tool_cmd}")
        
        # Security validation: check for dangerous commands (rm, del, powershell, cmd, system modifications)
        dangerous_patterns = [r'\brm\b', r'\bdel\b', r'\bformat\b', r'\bpowershell\b', r'\bcmd\b', r'\bsh\b', r'\bbash\b', r'>', r'\|', r'&']
        if any(re.search(pat, tool_cmd.lower()) for pat in dangerous_patterns):
            print(f"[⚠️ SECURITY] Ignored dangerous tool call: {tool_cmd}")
            logging.warning(f"[⚠️ SECURITY] Ignored dangerous tool call: {tool_cmd}")
            # Remove tag but speak warning
            clean_text = re.sub(r'\[TOOL_CALL:\s*.*?\]', '', response_text, flags=re.IGNORECASE)
            clean_text = re.sub(r'\[TOOL:\s*.*?\]', '', clean_text, flags=re.IGNORECASE).strip()
            return f"I cannot execute that command due to security restrictions. {clean_text}"
            
        try:
            # Execute tool asynchronously using the existing executor and command parser
            executor.submit(process_cmd_func, tool_cmd)
        except Exception as e:
            print(f"Error executing tool call: {e}")
            logging.error(f"Error executing tool call: {e}")
            
        # Strip tool tags from final response text
        clean_text = re.sub(r'\[TOOL_CALL:\s*.*?\]', '', response_text, flags=re.IGNORECASE)
        clean_text = re.sub(r'\[TOOL:\s*.*?\]', '', clean_text, flags=re.IGNORECASE).strip()
        return clean_text
        
    return response_text

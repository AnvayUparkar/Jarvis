import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError, RetryError, NotFound
import time
import os

# Save the original generate_content method
_original_generate_content = genai.GenerativeModel.generate_content

# The preferred sequence of models to try
'''
FALLBACK_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemini-3-pro-preview",
    "gemini-3.1-flash-lite"
    
]'''


FALLBACK_MODELS = [
    "gemini-3.7-flash",           # Latest stable model; optimal balance of speed and intelligence
    "gemini-3.5-flash-lite",      # Ultra-fast, high-volume model for quick tasks
    "gemini-3.1-pro-preview",     # Advanced model for complex reasoning and deep content generation
    "gemini-3.1-flash-lite",      # Legacy highly efficient fallback
    "gemini-3-pro-preview",       # Legacy advanced fallback
    "gemini-2.5-flash",           # Legacy flash fallback
    "gemini-2.5-flash-lite",      # Legacy fast fallback
    "gemini-2.5-pro",             # Legacy pro fallback
    "gemini-flash-latest",        # Dynamic pointer to the latest flash model
    "gemini-pro-latest"           # Dynamic pointer to the latest pro model
]


def _generate_content_with_fallback(self, *args, **kwargs):
    """
    Wrapper around GenerativeModel.generate_content that catches rate limits
    and automatically retries with alternative models.
    """
    original_model_name = self.model_name
    if original_model_name.startswith('models/'):
        original_model_name = original_model_name[7:]
    
    # We will try the originally requested model first, then fallbacks
    models_to_try = [original_model_name]
    for model in FALLBACK_MODELS:
        if model != original_model_name and model not in models_to_try:
            models_to_try.append(model)
            
    last_exception = None
    
    for model_name in models_to_try:
        try:
            if model_name != original_model_name:
                print(f"[🔄 GEMINI FALLBACK] Rate limit hit. Trying alternative model: {model_name}")
                # Create a temporary model instance for the fallback
                # Note: We don't change `self` because we don't want to mutate the object globally,
                # we just use a temp model for this specific generation.
                temp_model = genai.GenerativeModel(
                    model_name,
                    generation_config=self._generation_config,
                    safety_settings=self._safety_settings,
                    system_instruction=self._system_instruction
                )
                return _original_generate_content(temp_model, *args, **kwargs)
            else:
                return _original_generate_content(self, *args, **kwargs)
                
        except (ResourceExhausted, RetryError, NotFound) as e:
            print(f"[⚠️ API ERROR] Model '{model_name}' unavailable or rate limited.")
            last_exception = e
        except InternalServerError as e:
            print(f"[⚠️ API ERROR] Internal server error with '{model_name}'.")
            last_exception = e
            time.sleep(1) # Brief pause before retry
        except Exception as e:
            # Sometimes rate limits or missing model errors throw a generic Exception
            if "429" in str(e) or "404" in str(e) or "not found" in str(e).lower() or "quota" in str(e).lower() or "exhausted" in str(e).lower():
                print(f"[⚠️ API ERROR] Model '{model_name}' issue (429/404/Quota).")
                last_exception = e
            else:
                print(f"[❌ GEMINI] Unexpected error with '{model_name}': {e}")
                raise e # Reraise if it's not a rate limit (e.g. invalid prompt)
    
    # If we exhaust all models
    print("[❌ GEMINI FATAL] All models in the fallback sequence failed!")
    if last_exception is not None:
        raise last_exception
    raise RuntimeError("All models in the fallback sequence failed!")


def enable_gemini_fallback():
    """
    Applies the monkey-patch to google.generativeai.GenerativeModel globally.
    Call this ONCE at the start of your application.
    """
    if genai.GenerativeModel.generate_content is not _generate_content_with_fallback:
        genai.GenerativeModel.generate_content = _generate_content_with_fallback
        print("[✅ GEMINI] Global Model Fallback ENABLED.")

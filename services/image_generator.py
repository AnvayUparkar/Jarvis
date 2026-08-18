import os
from datetime import datetime
from PIL import Image
from huggingface_hub import InferenceClient
import google.generativeai as google_ai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini for prompt enhancement
try:
    from apikey import GEN_AI_API_KEY
    if GEN_AI_API_KEY:
        google_ai.configure(api_key=GEN_AI_API_KEY)
except Exception as e:
    print(f"[IMAGE_GEN] Warning loading apikey.py: {e}. Trying env fallback.")
    gemini_key = os.getenv("GEN_AI_API_KEY") or os.getenv("api_data")
    if gemini_key:
        google_ai.configure(api_key=gemini_key)


def enhance_image_prompt(user_prompt: str) -> str:
    """
    Enhances a simple user prompt into a visually descriptive prompt for image models.
    Leverages the existing Gemini LLM configuration in the project.
    """
    print(f"[IMAGE_GEN] Enhancing user prompt: '{user_prompt}'")
    try:
        model = google_ai.GenerativeModel("gemini-2.5-flash-lite")
        system_instruction = (
            "You are an expert prompt engineer for text-to-image AI generators. "
            "Your task is to take a simple image description from the user and expand it into a detailed, "
            "photorealistic, or styled prompt for FLUX.1-schnell.\n\n"
            "Specifically describe:\n"
            "- Subject: Details, materials, colors.\n"
            "- Composition: Camera perspective (e.g. low-angle, wide shot), layout.\n"
            "- Lighting: Source, color, time of day (e.g. golden hour, soft cinematic lighting).\n"
            "- Atmosphere & Realism: Realistic reflections, physical accuracy.\n\n"
            "IMAGE QUALITY SAFEGUARDS (CRITICAL):\n"
            "If the subject contains human, vehicle (e.g. cars), or objects with structural panels, ensure you instruct "
            "for structural accuracy: e.g. accurate proportions, correct wheel alignment, panels matching seamlessly, "
            "headlights/doors correctly structured, natural fingers/limbs, non-warped geometry.\n\n"
            "Do NOT add unrelated subjects or alter the core user request. "
            "Return ONLY the enhanced prompt string. No conversational text, quotes, or markdown formatting."
        )
        response = model.generate_content(
            f"System Instruction: {system_instruction}\nUser Prompt: {user_prompt}"
        )
        if response and response.text:
            enhanced = response.text.strip()
            print(f"[IMAGE_GEN] Enhanced Prompt: {enhanced}")
            return enhanced
    except Exception as e:
        print(f"[IMAGE_GEN] Prompt enhancement failed: {e}. Using fallback.")
    
    # Simple rule-based fallback if LLM is unavailable
    return f"A highly detailed, photorealistic depiction of {user_prompt}, cinematic lighting, correct proportions, sharp focus, octane render."


class ImageGenerator:
    """
    Modular Image Generation Service utilizing Hugging Face InferenceClient
    with the black-forest-labs/FLUX.1-schnell model.
    """
    def __init__(self, model_name=None, output_dir=None):
        self.hf_token = os.getenv("HF_TOKEN")
        self.model_name = model_name or os.getenv("IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
        self.output_dir = output_dir or os.getenv("IMAGE_OUTPUT_DIR", "www/generated_images")

    def generate(self, prompt: str) -> str:
        """
        Sends the enhanced prompt to FLUX.1-schnell, saves the resulting PIL image,
        and returns the local file path.
        """
        if not self.hf_token:
            raise ValueError(
                "Hugging Face token is not configured.\n"
                "Please add HF_TOKEN to your .env file."
            )

        # Ensure target directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        try:
            print(f"[IMAGE_GEN] Initializing Hugging Face InferenceClient...")
            client = InferenceClient(api_key=self.hf_token, provider="auto")

            print(f"[IMAGE_GEN] Querying model '{self.model_name}'...")
            start_time = datetime.now()

            # Call API to generate PIL image
            image = client.text_to_image(prompt, model=self.model_name)

            duration = (datetime.now() - start_time).total_seconds()
            print(f"[IMAGE_GEN] Generation succeeded in {duration:.2f} seconds.")

            if not isinstance(image, Image.Image):
                raise TypeError(f"Expected PIL Image, got {type(image)}")

            # Save the image locally
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jarvis_image_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)

            image.save(filepath)
            print(f"[IMAGE_GEN] Image successfully saved to: {filepath}")

            # Return the file path relative to 'www' or absolute path depending on Jarvis server scope
            return filepath

        except Exception as e:
            print(f"[IMAGE_GEN] Error: {e}")
            raise e

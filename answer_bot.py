import json
import google.generativeai as google_ai
import os
import sys
import re

# Attempt to import API key from apikey.py
try:
    # Add the parent directory to sys.path to allow importing apikey.py
    # if it's in the root of the project and answer_bot.py is in a subdirectory.
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from apikey import api_data as GEN_AI_API_KEY
except ImportError:
    print("Error: apikey.py not found or api_data not defined. Using placeholder for API key.")
    GEN_AI_API_KEY = "AIzaSyB_H-_FNNVw-Oo10NyPJoOeTpXoXOPRRmY" # Placeholder, replace with actual key

# Configure Gemini AI
gemini_configured_successfully = False
try:
    google_ai.configure(api_key=GEN_AI_API_KEY)
    gemini_configured_successfully = True
except Exception as e:
    print(f"❌ Error configuring Gemini API: {e}. Please check your GEN_AI_API_KEY.")

def answer_mcq_question(question: str, options: list[str]) -> str:
    """
    Answers a multiple-choice question using the Google Gemini API.

    Args:
        question (str): The multiple-choice question.
        options (list[str]): A list of options for the question.

    Returns:
        str: The chosen option.
    """
    if not options:
        return "No options provided."

    # Format the prompt for the Gemini LLM.
    prompt = f"Question: {question}\nOptions:"
    for i, option in enumerate(options):
        prompt += f"\n{chr(65 + i)}. {option}"
    
    # --- IMPROVED PROMPT INSTRUCTION ---
    prompt += "\n\nYour answer must be a single uppercase letter corresponding to the best option (e.g., A, B, C, D)."
    prompt += " Do NOT include any other text, explanations, or punctuation. For example, if the answer is option B, simply respond with 'B'."

    print(f"Sending request to Gemini with prompt:\n{prompt}\n")

    try:
        # Call the Gemini API
        model = google_ai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        # Extract the text response and clean it
        llm_response_text = response.text.strip()
        print(f"Gemini response raw: '{llm_response_text}'\n")

        # Attempt to extract a single letter (A, B, C, etc.)
        # This regex looks for a single uppercase letter at the beginning or end of the string,
        # or a single uppercase letter surrounded by non-word characters.
        match = re.search(r'\b[A-Z]\b', llm_response_text.upper())
        if match:
            chosen_letter = match.group(0)
        else:
            # Fallback if regex doesn't find a clear single letter, take the first char if it's a letter
            if llm_response_text and llm_response_text[0].isalpha():
                chosen_letter = llm_response_text[0].upper()
            else:
                chosen_letter = "A" # Default to 'A' if no clear letter is found

        print(f"Parsed LLM response letter: {chosen_letter}\n")

        # Map the letter back to the actual option.
        try:
            chosen_index = ord(chosen_letter) - 65
            if 0 <= chosen_index < len(options):
                return options[chosen_index]
            else:
                return "Could not determine a valid option from the LLM response."
        except (TypeError, ValueError):
            return "Invalid LLM response format."

    except Exception as e:
        print(f"❌ Error calling Gemini API: {e}")
        return "Sorry, I couldn't get an answer from the AI at this moment."

# Example Usage (optional, for testing the function)
if __name__ == "__main__":
    test_question = "What is the capital of France?"
    test_options = ["Berlin", "Madrid", "Paris", "Rome"]
    
    # Temporarily set a dummy API key if not found, for local testing without a real key
    if GEN_AI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("Using dummy API key for example. Please replace 'YOUR_GEMINI_API_KEY_HERE' with your actual key for real functionality.")
        # To run this example with a real API key, ensure apikey.py exists or set GEN_AI_API_KEY directly.
        # For actual API calls, you'd need a valid key.
        # This example will likely fail if the dummy key is used for google_ai.configure()

    # This part will now only work if Gemini was configured successfully
    if gemini_configured_successfully:
        print(f"Answering: '{test_question}' with options: {test_options}")
        answer = answer_mcq_question(test_question, test_options)
        print(f"Answer: {answer}")
    else:
        print("Skipping example usage: Gemini API key not configured or configuration failed.")

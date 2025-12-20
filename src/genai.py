import google.generativeai as genai
import os
import sys
from config import GEMINI_API_KEY

def get_latest_flash_model():
    """
    Retrieves the latest available 'flash' model from the Gemini API.
    Prioritizes models with higher version numbers.
    """
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Filter for flash models
        flash_models = [m for m in models if 'flash' in m.lower()]
        
        if not flash_models:
            print("Warning: No 'flash' models found. Falling back to default.")
            return 'models/gemini-1.5-flash' # Fallback
            
        # Sort to find the "latest". 
        # Attempt to sort by version number if strictly formatted, otherwise simple string sort
        # String sort actually works decently for 1.5 vs 2.0 vs 3.0
        # We want to reverse sort to get the highest number first
        flash_models.sort(reverse=True)
        
        latest = flash_models[0]
        print(f"Selected Model: {latest}")
        return latest
        
    except Exception as e:
        print(f"Error listing models: {e}")
        return 'models/gemini-1.5-flash' # Fallback

def generate_reply(email_body, system_prompt):
    """
    Generates an email reply using Gemini.
    
    Args:
        email_body (str): The content of the email to reply to.
        system_prompt (str): The persona/instructions for the AI.
        
    Returns:
        str: The generated reply text.
    """
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        return None

    try:
        model_name = get_latest_flash_model()
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(model_name)
        
        full_prompt = f"{system_prompt}\n\nEmail Thread:\n{email_body}\n\nResponse:"
        
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating reply with Gemini: {e}")
        return None

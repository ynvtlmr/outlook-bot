from google import genai
import os
import sys
from config import GEMINI_API_KEY

def get_latest_flash_model():
    """
    Returns the 'gemini-2.5-flash' model.
    """
    model = 'gemini-2.5-flash'
    print(f"Selected Model: {model}")
    return model

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
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        full_prompt = f"{system_prompt}\n\nEmail Thread:\n{email_body}\n\nResponse:"
        
        response = client.models.generate_content(
            model=model_name,
            contents=full_prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error generating reply with Gemini: {e}")
        return None

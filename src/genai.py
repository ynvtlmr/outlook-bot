from google import genai
import json
import os
import sys
from config import GEMINI_API_KEY


# Priority list of models to cycle through
AVAILABLE_MODELS = [
    "gemini-3-flash",
    "gemini-2.5-flash", 
    "gemini-2.5-flash-lite"
]

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

    client = genai.Client(api_key=GEMINI_API_KEY)
    full_prompt = f"{system_prompt}\n\nEmail Thread:\n{email_body}\n\nResponse:"

    for model_name in AVAILABLE_MODELS:
        try:
            print(f"Attempting to generate reply with model: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"Warning: Failed to generate reply with {model_name}. Error: {e}")
            continue

    print("Error: All models failed to generate reply.")
    return None

def generate_batch_replies(email_batch, system_prompt):
    """
    Generates replies for a batch of emails using Gemini.
    
    Args:
        email_batch (list): List of dicts with 'id', 'subject', and 'content' keys.
        system_prompt (str): The persona/instructions for the AI.
        
    Returns:
        dict: A dictionary mapping message_id to the generated reply text.
    """
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        return {}
    
    if not email_batch:
        return {}

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # transform the batch into a cleaner input format for the LLM
    # We start by telling it what we want
    prompt_intro = (
        f"{system_prompt}\n\n"
        "TASK: You are processing a batch of emails. For each email provided in the JSON list below, generate a reply based on the persona.\n"
        "OUTPUT FORMAT: You MUST return a raw JSON list of objects. Each object must have exactly two fields:\n"
        "  - \"id\": The exact id from the input.\n"
        "  - \"reply_text\": Your generated response.\n\n"
        "Do not output markdown formatting (like ```json), just the raw JSON.\n\n"
        "INPUT DATA:\n"
    )
    
    # Create a simplified version of the batch for the prompt to save tokens/confusion
    # (We don't need to send everything, just what's needed for the reply)
    prompt_batch = [
        {"id": item['id'], "subject": item['subject'], "content": item['content']}
        for item in email_batch
    ]
    
    full_prompt = prompt_intro + json.dumps(prompt_batch, indent=2)
    
    for model_name in AVAILABLE_MODELS:
        try:
            print(f"Attempting to generate batch replies with model: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config={
                    'response_mime_type': 'application/json'
                }
            )
            
            raw_text = response.text.strip()
            
            # Cleanup potential markdown fences if the model adds them despite instructions
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            parsed_data = json.loads(raw_text.strip())
            
            # Convert List -> Dict for O(1) lookups
            results = {}
            if isinstance(parsed_data, list):
                for item in parsed_data:
                    if 'id' in item and 'reply_text' in item:
                        results[item['id']] = item['reply_text']
                        
            return results

        except Exception as e:
            print(f"Warning: Failed to generate batch replies with {model_name}. Error: {e}")
            continue

    print("Error: All models failed to generate batch replies.")
    return {}

import sys
import os
import certifi
import pkg_resources

print("="*60)
print("DIAGNOSTIC REPORT")
print("="*60)

# 1. Python Interpreter
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")

# 2. Certifi
print(f"Certifi Path: {certifi.where()}")
try:
    print(f"Certifi Version: {pkg_resources.get_distribution('certifi').version}")
except:
    print("Certifi Version: Unknown")

# 3. Code Verification
print("\nChecking src/genai.py content on disk:")
try:
    with open("src/genai.py", "r") as f:
        content = f.read()
        if "client_args={'verify': certifi.where()}" in content:
            print("SUCCESS: src/genai.py contains the SSL fix.")
        else:
            print("FAILURE: src/genai.py DOES NOT contain the SSL fix.")
except Exception as e:
     print(f"Error reading src/genai.py: {e}")

# 4. Connection Test
print("\nRunning Google GenAI Connection Test (using venv logic)...")
try:
    from google import genai
    from google.genai import types
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    print(f"API Key found: {'Yes' if api_key else 'No'}")
    
    if api_key:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                client_args={'verify': certifi.where()}
            )
        )
        print("Attempting generate_content...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Diagnostics Test Message"
        )
        print("SUCCESS: Connection worked!")
        print(f"Response: {response.text}")
    else:
        print("SKIPPING: No API Key found.")
        
except Exception as e:
    print(f"FAILURE: Connection failed with error:")
    print(e)

print("="*60)

import os
from dotenv import load_dotenv

load_dotenv()

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DAYS_THRESHOLD = 5
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
APPLESCRIPTS_DIR = os.path.join(BASE_DIR, 'src', 'apple_scripts')

# AI Models
AVAILABLE_MODELS = [
    "gemini-3-flash",
    "gemini-2.5-flash", 
    "gemini-2.5-flash-lite"
]

# Parsing Delimiters
MSG_DELIMITER = "\n///END_OF_MESSAGE///\n"
BODY_START = "---BODY_START---"
BODY_END = "---BODY_END---"


import os
from dotenv import load_dotenv

load_dotenv()

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DAYS_THRESHOLD = 5
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
USERS_FILE = os.path.join(BASE_DIR, 'config', 'users.csv')
APPLESCRIPTS_DIR = os.path.join(BASE_DIR, 'src', 'apple_scripts')

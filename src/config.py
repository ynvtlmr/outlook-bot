import os
import yaml
from dotenv import load_dotenv

load_dotenv()

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load YAML Configuration
_config_path = os.path.join(BASE_DIR, 'config.yaml')
try:
    with open(_config_path, 'r') as f:
        _config_data = yaml.safe_load(f) or {}
except Exception as e:
    print(f"Warning: Error loading config.yaml: {e}")
    _config_data = {}

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Default to 5 if not in yaml
DAYS_THRESHOLD = _config_data.get('days_threshold', 5)
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
APPLESCRIPTS_DIR = os.path.join(BASE_DIR, 'src', 'apple_scripts')

# Fallback Content
DEFAULT_REPLY = _config_data.get('default_reply', "Thank you for your email. I will review it and get back to you shortly.")

# AI Models
AVAILABLE_MODELS = _config_data.get('available_models', [
    "gemini-3-flash",
    "gemini-2.5-flash", 
    "gemini-2.5-flash-lite"
])

# Parsing Delimiters
MSG_DELIMITER = "\n///END_OF_MESSAGE///\n"
BODY_START = "---BODY_START---"
BODY_END = "---BODY_END---"


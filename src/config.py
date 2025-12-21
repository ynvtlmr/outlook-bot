import os
import sys
import yaml
from dotenv import load_dotenv

load_dotenv()

# Path Determination
if getattr(sys, 'frozen', False):
    # Running as compiled application
    # sys._MEIPASS is the temp folder where PyInstaller extracts bundled files
    RESOURCE_DIR = sys._MEIPASS
    
    # For User Data (Config, Logs), use the User's Documents folder
    # This ensures we have write permission and don't pollute the app bundle
    USER_DATA_DIR = os.path.join(os.path.expanduser("~"), "Documents", "OutlookBot")
else:
    # Running from source
    RESOURCE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    USER_DATA_DIR = RESOURCE_DIR

# Ensure User Data Directory exists
os.makedirs(USER_DATA_DIR, exist_ok=True)

# Define Paths
CONFIG_PATH = os.path.join(USER_DATA_DIR, 'config.yaml')
ENV_PATH = os.path.join(USER_DATA_DIR, '.env')
SYSTEM_PROMPT_PATH = os.path.join(USER_DATA_DIR, 'system_prompt.txt')
OUTPUT_DIR = os.path.join(USER_DATA_DIR, 'output')

# Resources (Bundled or Source)
APPLESCRIPTS_DIR = os.path.join(RESOURCE_DIR, 'src', 'apple_scripts')

# Load .env (Override with user data path)
load_dotenv(ENV_PATH)

# Load YAML Configuration
try:
    with open(CONFIG_PATH, 'r') as f:
        _config_data = yaml.safe_load(f) or {}
except FileNotFoundError:
    # Use defaults if config doesn't exist yet (will be created by GUI or manual copy)
    _config_data = {}
except Exception as e:
    print(f"Warning: Error loading config.yaml: {e}")
    _config_data = {}

# Configuration Values
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DAYS_THRESHOLD = _config_data.get('days_threshold', 5)
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


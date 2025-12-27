import os
import sys
from typing import Optional

import yaml
from dotenv import load_dotenv

# Path Determination
if getattr(sys, "frozen", False):
    # Running as compiled application
    # sys._MEIPASS is the temp folder where PyInstaller extracts bundled files
    RESOURCE_DIR = getattr(sys, "_MEIPASS", os.path.abspath("."))

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
CONFIG_PATH = os.path.join(USER_DATA_DIR, "config.yaml")
ENV_PATH = os.path.join(USER_DATA_DIR, ".env")
SYSTEM_PROMPT_PATH = os.path.join(USER_DATA_DIR, "system_prompt.txt")
OUTPUT_DIR = os.path.join(USER_DATA_DIR, "output")

# Resources (Bundled or Source)
APPLESCRIPTS_DIR = os.path.join(RESOURCE_DIR, "src", "apple_scripts")

# Load .env (Override with user data path)
load_dotenv(ENV_PATH)

# Load YAML Configuration
try:
    with open(CONFIG_PATH, "r") as f:
        _config_data = yaml.safe_load(f) or {}
except FileNotFoundError:
    # Use defaults if config doesn't exist yet (will be created by GUI or manual copy)
    _config_data = {}
except Exception as e:
    print(f"Warning: Error loading config.yaml: {e}")
    _config_data = {}

# --- Centralized Credentials Management ---

ENV_GEMINI_API_KEY = "GEMINI_API_KEY"
ENV_OPENAI_API_KEY = "OPENAI_API_KEY"
ENV_OPENROUTER_API_KEY = "OPENROUTER_API_KEY"


class CredentialManager:
    """Central accessor for API keys to ensure consistency."""

    @staticmethod
    def get_gemini_key() -> Optional[str]:
        return os.getenv(ENV_GEMINI_API_KEY)

    @staticmethod
    def get_openai_key() -> Optional[str]:
        return os.getenv(ENV_OPENAI_API_KEY)

    @staticmethod
    def get_openrouter_key() -> Optional[str]:
        return os.getenv(ENV_OPENROUTER_API_KEY)


# Configuration Values
GEMINI_API_KEY: Optional[str] = CredentialManager.get_gemini_key()
OPENAI_API_KEY: Optional[str] = CredentialManager.get_openai_key()
OPENROUTER_API_KEY: Optional[str] = CredentialManager.get_openrouter_key()
DAYS_THRESHOLD: int = _config_data.get("days_threshold", 5)
DEFAULT_REPLY: str = _config_data.get(
    "default_reply", "Thank you for your email. I will review it and get back to you shortly."
)

# Preferred model for LLM generation (None means use first available)
PREFERRED_MODEL: Optional[str] = _config_data.get("preferred_model", None)

# Parsing Delimiters
MSG_DELIMITER: str = "\n///END_OF_MESSAGE///\n"
BODY_START: str = "---BODY_START---"
BODY_END: str = "---BODY_END---"

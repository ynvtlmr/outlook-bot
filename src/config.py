import os

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configuration
DAYS_THRESHOLD = 7
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
USERS_FILE = os.path.join(BASE_DIR, 'config', 'users.csv')
APPLESCRIPTS_DIR = os.path.join(BASE_DIR, 'src', 'apple_scripts')

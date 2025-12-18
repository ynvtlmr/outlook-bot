import subprocess
import os
from config import APPLESCRIPTS_DIR

def get_outlook_version():
    """
    Retrieves the version of the currently installed/running Microsoft Outlook.
    Returns the version string or None if it fails.
    """
    script_path = os.path.join(APPLESCRIPTS_DIR, 'get_version.scpt')
    
    if not os.path.exists(script_path):
        print(f"Error: Script not found at {script_path}")
        return None
        
    cmd = ['osascript', script_path]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error detecting Outlook version: {e.stderr}")
        return None

if __name__ == "__main__":
    version = get_outlook_version()
    if version:
        print(f"Detected Microsoft Outlook Version: {version}")
    else:
        print("Failed to detect Outlook version.")

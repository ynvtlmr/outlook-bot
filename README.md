# Outlook Bot

A local automation tool for macOS that bridges Microsoft Outlook with Google's Gemini models. It uses AppleScript for local data access and Python for logic and AI interaction.

## Core Features

### 1. Flagged Email Responder (`main.py`)
Automatically drafts replies for emails you have flagged in Outlook.
- **Workflow**: 
    1. Scans Outlook for threads containing messages with an **"Active"** flag.
    2. Extracts the full conversation context (not just the tagged email).
    3. Checks if a reply is actually needed (filters out threads where you replied recently).
    4. Uses **Gemini** or **OpenAI** to generate a draft reply based on your `system_prompt.txt`.
    5. Creates the draft in Outlook for your review.

---

## Setup Guide

### 1. Prerequisites
- **macOS**: Required for AppleScript support.
- **Microsoft Outlook for Mac**: Must be running.
    - *Note: "Legacy Outlook" mode is recommended for best AppleScript compatibility.*
- **Python**: 3.10+.
- **Google Cloud API Key**: For Gemini access.

### 2. Installation

 Clone the repository and set up a virtual environment:
```bash
git clone <repository_url>
cd outlook-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration

#### API Key
1. Get an API key from [Google AI Studio](https://aistudio.google.com/).
2. Create a `.env` file in the project root:
   ```bash
   touch .env
   ```
3. Add your key to the file:
   ```env
   GEMINI_API_KEY=your_key_here
   ```

#### Customization
- **Persona**: Edit `system_prompt.txt` to change how the AI writes (e.g., tone, style, signature).
- **Settings**: Edit `config.yaml` to change the `days_threshold` or the list of `available_models`.

---

## Usage

You can run the bot using either the Graphical User Interface (GUI) or the Command Line Interface (CLI).

### Graphical User Interface (GUI)
The GUI is the recommended way to manage settings and run the bot.

**Launch the GUI:**
```bash
python src/gui.py
```

**Features:**
- **Control Panel**: Start/Stop the bot and "Save All Settings" with a single click.
    - *Note: "Stop" will wait for the current ongoing task to finish.*
- **Configuration Tab**:
    - **Gemini API Key**: Manage your key securely (toggles visibility).
    - **Days Threshold**: Set the lookback period for email threads.
    - **Default Reply**: Edit the fallback message.
    - **Available Models**: Update the list of Gemini models.
- **System Prompt Tab**: Edit the `system_prompt.txt` file to adjust the bot's persona and instructions.
- **Console Output**: View real-time logs directly in the application window.

### Command Line Interface (CLI)
Alternatively, you can run the automation script directly from the terminal. This uses the current settings in `config.yaml` and `.env`.

```bash
python src/main.py
```

---

## Building for macOS

If you prefer to run the tool as a standalone application (`.app`) without needing to touch the terminal, you can build it yourself or download a release.

### 1. Build Locally
You can package the Python scripts into a macOS application using PyInstaller:

```bash
pip install pyinstaller
pyinstaller outlook_bot.spec
```
The application will be created in the `dist/` folder as `OutlookBot.app`.

### 2. GitHub Actions (CI/CD)
This project includes a specific GitHub workflow (`.github/workflows/build_app.yml`) that automatically builds and creates releases for both **Intel** and **Apple Silicon (M1/M2/M3)** Macs whenever a new tag (e.g., `v1.0`) is pushed.

---

## Standalone App Data
If you run the packaged `OutlookBot.app`:
- **Configuration & Logs**: All data is stored in `~/Documents/OutlookBot/`.
    - This keeps your application bundle clean and allows updates without losing settings.
- **First Run**: The app will automatically create this directory. use the GUI to configure your API key and settings, and they will be saved here.

## Project Structure

- **`src/gui.py`**: The Graphical User Interface (GUI) entry point.
- **`src/main.py`**: The primary logic script (CLI entry point).
- **`src/genai.py`**: Handles interactions with the Google GenAI SDK.
- **`src/scraper.py`**: logic for parsing raw Outlook text data into Python dictionaries.
- **`src/outlook_client.py`**: Wrapper for executing AppleScripts.
- **`src/date_utils.py`**: Utilities for parsing various date formats.
- **`src/apple_scripts/`**: Raw AppleScript files used to query the Outlook application.
- **`output/`**: Directory where scraped thread logs are saved for debugging.

## Troubleshooting

- **Permissions**: The first time you run this, macOS will ask for permission for Terminal (or your IDE) to control "Microsoft Outlook". You must allow this.
- **"New Outlook"**: If the scripts hang or return no data, ensure you are using "Legacy Outlook" (Help > Revert to Legacy Outlook) as the new version has limited AppleScript support.

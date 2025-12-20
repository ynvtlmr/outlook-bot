# Outlook Bot

A local automation tool for macOS that bridges Microsoft Outlook with Google's Gemini models. It uses AppleScript for local data access and Python for logic and AI interaction.

## Core Features

### 1. Flagged Email Responder (`main.py`)
Automatically drafts replies for emails you have flagged in Outlook.
- **Workflow**: 
    1. Scans Outlook for threads containing messages with an **"Active"** flag.
    2. Extracts the full conversation context (not just the tagged email).
    3. Checks if a reply is actually needed (filters out threads where you replied recently).
    4. Uses **Gemini** (e.g., `gemini-3-flash`) to generate a draft reply based on your `system_prompt.txt`.
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
- **Settings**: Edit `src/config.py` to change the `DAYS_THRESHOLD` or the list of `AVAILABLE_MODELS`.

---

## Usage

### To Generate Replies for Flagged Emails
Run the main script. This will scrape flagged threads and create drafts for any that need attention.
```bash
python src/main.py
```

---

## Project Structure

- **`src/main.py`**: The primary entry point for the flagged email workflow.
- **`src/genai.py`**: Handles interactions with the Google GenAI SDK.
- **`src/scraper.py`**: logic for parsing raw Outlook text data into Python dictionaries.
- **`src/outlook_client.py`**: Wrapper for executing AppleScripts.
- **`src/date_utils.py`**: Utilities for parsing various date formats.
- **`src/apple_scripts/`**: Raw AppleScript files used to query the Outlook application.
- **`output/`**: Directory where scraped thread logs are saved for debugging.

## Troubleshooting

- **Permissions**: The first time you run this, macOS will ask for permission for Terminal (or your IDE) to control "Microsoft Outlook". You must allow this.
- **"New Outlook"**: If the scripts hang or return no data, ensure you are using "Legacy Outlook" (Help > Revert to Legacy Outlook) as the new version has limited AppleScript support.

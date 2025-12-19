# Outlook Bot

A powerful macOS automation tool for Microsoft Outlook, designed to streamline email management, automate follow-ups, and maintain relationships. This bot leverages macOS AppleScript (via `osascript`) bridged with Python to interact directly with the Outlook desktop application.

## 🚀 Features

### 1. Smart Thread Scraping
*   **Recent Threads**: Scrapes and exports the last 50 email threads from your Inbox to text files for easy reading/analysis.
*   **Flagged Threads**: Deep scanning for "Active" flags. When a flagged message is found, the bot intelligently hunts down the *entire conversation* (searching Inbox, Sent, Archive, and Deleted Items) to give you the full context of the thread, not just the single flagged email.

### 2. Auto-Drafting for Flagged Items
*   Automatically processes threads with "Active" flags.
*   Identifies the latest message in the conversation (regardless of which specific email was flagged).
*   Creates a draft reply attached to that latest message, simulating a "Reply All" action while ensuring you (the sender) are not included in the recipients list.
*   **Safety**: It *only* creates drafts. It typically opens them for your review and never sends emails automatically without your confirmation.

### 3. Relationship Manager (`responder.py`)
*   Monitors communication with specific people defined in `config/users.csv`.
*   Checks the last time you exchanged emails with them.
*   If no contact has been made for 7 days (configurable), it automatically drafts a "Catching up" email to keep the relationship warm.

## 🛠 Prerequisites

*   **Operating System**: macOS (Required for AppleScript support).
*   **Application**: Microsoft Outlook for Mac (Classic/Legacy behavior often provides better AppleScript support).
*   **Python**: Python 3.6+.

## 📂 Project Structure

```
outlook-bot/
├── config/
│   └── users.csv          # List of contacts to monitor (name, email)
├── src/
│   ├── main.py            # Primary entry point (Scraping + Flagged Auto-Response)
│   ├── responder.py       # Relationship Manager entry point
│   ├── scraper.py         # Logic for parsing and saving email threads
│   ├── outlook_client.py  # Python wrapper for AppleScript execution
│   └── apple_scripts/     # .scpt files for direct Outlook interaction
│       ├── create_draft.scpt
│       ├── get_emails.scpt
│       ├── get_flagged_threads.scpt
│       ├── get_recent_threads.scpt
│       ├── get_version.scpt
│       └── reply_to_message.scpt
├── output/                # Generated text dumps of email threads
└── requirements.txt       # Python dependencies
```

## 📦 Setup & Usage

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd outlook-bot
    ```

2.  **Dependencies**:
    Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration**:
    *   **Responder**: Create `config/users.csv` with headers `name,email`.
    *   **Thresholds**: Edit `src/config.py` to adjust `DAYS_THRESHOLD` (default: 7).

4.  **Running the Bot**:

    **To Scrape & Process Flagged Items:**
    ```bash
    python3 src/main.py
    ```
    *   Running this will detect your Outlook version, scrape flagged threads, save them to `output/`, and open draft replies for any active flags.

    **To Check Relationships:**
    ```bash
    python3 src/responder.py
    ```
    *   Checks `users.csv` and drafts "Catching up" emails if needed.

## ⚙️ Architecture & Execution Logic

The bot operates on a **Bridge Pattern** between Python (logic) and AppleScript (interaction):

### 1. Scraping & Flagged Response Flow (`main.py`)
This is the main workflow for daily usage.
1.  **Initialization**:
    *   `main.py` starts and detects the Outlook client version using `get_version.scpt`.
2.  **Scraping**:
    *   Calls `scraper.run_scraper(mode='flagged')`.
    *   Executes `get_flagged_threads.scpt` to fetch full conversation threads for any flagged items.
    *   **Parsing**: Raw text from AppleScript is parsed in `scraper.py`, extracting headers and body content, and grouped into threads by Conversation ID or Subject.
    *   Threads are saved to the `output/` directory for inspection.
3.  **Auto-Drafting**:
    *   `main.py` identifies threads with "Active" flags.
    *   It sorts the thread to find the **latest message** (not necessarily the flagged one).
    *   Calls `client.reply_to_message(...)` which executes `reply_to_message.scpt` to safely create a draft reply (no auto-send).

### 2. Relationship Management Flow (`responder.py`)
This workflow ensures you keep in touch with key contacts.
1.  **Configuration**: Reads contacts from `config/users.csv`.
2.  **Scanning**:
    *   For each contact, executes `get_emails.scpt` to fetch recent communications.
3.  **Decision**:
    *   Calculates the days since the last email exchange.
    *   If the gap exceeds `config.DAYS_THRESHOLD` (default: 7), it creates a "Catching up" draft using `create_draft.scpt`.

### Technical Implementation
*   **OutlookClient** (`src/outlook_client.py`): A Python wrapper that constructs and executes `osascript` commands.
*   **AppleScript Bridge**: Since Outlook for Mac lacks a local Python API, AppleScript is used to interact with the UI and local database directly.

## ⚠️ Known Limitations

*   **Speed**: AppleScript can be slow when scanning large mailboxes. The bot uses optimized queries (search limits, specific folders) to mitigate this.
*   **Outlook Mode**: "New Outlook" for Mac has reduced AppleScript support compared to the "Legacy" version. If you encounter issues, try switching to Legacy mode.

---
*Created for personal productivity and automation.*

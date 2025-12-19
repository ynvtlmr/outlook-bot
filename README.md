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
│   ├── users.csv          # List of contacts to monitor for the Responder module
│   └── ...
├── src/
│   ├── main.py            # Primary entry point (Scraping + Flagged Auto-Response)
│   ├── responder.py       # Relationship Manager entry point
│   ├── scraper.py         # Logic for parsing and saving email threads
│   ├── outlook_client.py  # Python wrapper for AppleScript execution
│   └── apple_scripts/     # .scpt files for direct Outlook interaction
└── output/                # Generated text dumps of email threads
```

## 📦 Setup & Usage

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd outlook-bot
    ```

2.  **Dependencies**:
    The project uses standard libraries, but `python-dateutil` is recommended for robust date parsing.
    ```bash
    pip install python-dateutil
    ```

3.  **Configuration**:
    *   **Responder**: Add contacts to `config/users.csv` (headers: `name,email`).
    *   **Thresholds**: Edit `src/config.py` to change `DAYS_THRESHOLD` (default: 7).

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

## ⚙️ How It Works

The bot uses a "Bridge" pattern:
1.  **Python** acts as the brain. It makes decisions, parses text, and attempts to group threads logically.
2.  **AppleScript** acts as the hands. It performs the actual "heavy lifting" inside Outlook—fetching messages, reading flags, and creating windows/drafts.

### Why AppleScript?
Microsoft Outlook for Mac does not have a comprehensive local API outside of AppleScript/JXA. This approach allows the bot to run locally on your machine without needing Exchange web credentials or API keys.

## ⚠️ Known Limitations

*   **Speed**: AppleScript can be slow when scanning large mailboxes. The bot uses optimized queries (search limits, specific folders) to mitigate this.
*   **Outlook Mode**: "New Outlook" for Mac has reduced AppleScript support compared to the "Legacy" version. If you encounter issues, try switching to Legacy mode.

---
*Created for personal productivity and automation.*

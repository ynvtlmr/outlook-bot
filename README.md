# Outlook Bot

A Python-based automation tool for Microsoft Outlook on macOS. It leverages AppleScript to interact directly with the local Outlook client for scraping emails, monitoring threads, and drafting responses.

## Overview

This project bridges Python and Microsoft Outlook using the Open Scripting Architecture (OSA).
- **Python Layer**: Handles logic, parsing, scheduling, and file I/O.
- **AppleScript Layer**: Handles direct communication with the Outlook application (reading mailboxes, fetching messages, creating drafts).

## Directory Structure

```
├── config/             # Configuration files (users.csv)
├── output/             # Scraped data output directory
├── src/
│   ├── apple_scripts/  # AppleScript source files (.scpt)
│   ├── main.py         # Entry point for scraping
│   ├── responder.py    # Logic for checking engagement and drafting replies
│   ├── scraper.py      # Core scraping logic
│   └── ...
└── tests/              # Unit tests
```

## AppleScript Modules

The core interaction with Outlook is performed by specific AppleScripts located in `src/apple_scripts/`. Here is a detailed breakdown of each script:

### 1. `create_draft.scpt`
**Purpose**: Creates a new email draft and opens it for review.
- **Inputs**: `Recipient Address`, `Subject`, `Content`.
- **Mechanism**: Tells Outlook to make a new "outgoing message" with the provided properties. It does *not* send the email automatically; it calls `open` on the message object so the user can review and hit send.

### 2. `get_emails.scpt`
**Purpose**: Searches for recent emails from a specific sender.
- **Inputs**: `Target Email Address`.
- **Mechanism**:
    - Scans the "Inbox" folder.
    - Limits scan to the most recent 500 messages for performance.
    - Filters messages where the sender's address contains the target email.
    - **Output**: Returns a delimited string containing sender, subject, date, and body for all matching messages. Separation logic uses `|||` for fields and `///END_OF_EMAIL///` for messages.

### 3. `get_flagged_emails.scpt`
**Purpose**: Retrieval of all flagged ("todo") items across all mail folders.
- **Mechanism**:
    - Iterates through *every* top-level mail folder.
    - Filters for messages where `todo flag` is `marked`.
    - **Output**: Returns a formatted string with `ID`, `From`, `Date`, `Subject`, and body content wrapped in `---BODY_START---` / `---BODY_END---` blocks.

### 4. `get_recent_threads.scpt`
**Purpose**: specialized scraper for the most recent inbox activity.
- **Mechanism**:
    - Focuses on "Inbox" only.
    - Retrieves the last 50 messages strictly.
    - **Output**: Similar formatting to `get_flagged_emails.scpt`, ensuring conversation IDs are captured for threading.

### 5. `get_version.scpt`
**Purpose**: Health check / Diagnostics.
- **Mechanism**: Simply queries the `version` property of the Outlook application object.

### 6. `list_mailboxes.scpt`
**Purpose**: Exploratory tool to visualize folder structure.
- **Mechanism**: Lists all top-level folders and their unread counts. It also attempts to identify container names to map the hierarchy.

## Python Integration

The Python scripts wrap these AppleScripts using `subprocess` to execute `osascript` commands.

### `outlook_client.py`
Connects the two worlds. It contains the `OutlookClient` class which:
- Locates the `.scpt` files.
- Executes them via `subprocess.run`.
- Handles basic error catching for the shell command execution.

### `scraper.py`
Handles the business logic of "reading" emails.
- **Parsing**: It takes the raw, delimited string output from the AppleScripts and converts them into Python dictionaries.
- **Threading**: Groups messages by Conversation ID or Subject.
- **Output**: Saves threads as human-readable text files in the `output/` directory.
- **Modes**: Supports `recent` (last 50 inbox items) and `flagged` (all flagged items) modes.

### `responder.py`
A proactive engagement tool.
- **Input**: Reads a list of users from `config/users.csv`.
- **Logic**:
    1. specific user history using `get_emails.scpt`.
    2. Parses dates to find the last interaction.
    3. If the last interaction was > 7 days ago (configurable via `DAYS_THRESHOLD`), it uses `create_draft.scpt` to draft a "Catching up" email.

## Setup & Usage

1. **Prerequisites**:
   - macOS (required for AppleScript).
   - Microsoft Outlook installed and configured.
   - Python 3.

2. **Configuration**:
   - Add target contacts to `config/users.csv` (format: `name,email`).

3. **Running the Scraper**:
   ```bash
   python src/main.py
   ```
   This will run both "recent" and "flagged" scrapers and populate the `output/` folder.

4. **Running the Responder**:
   ```bash
   python src/responder.py
   ```
   This will check your history with users in the CSV and open draft windows in Outlook for any who need a follow-up.

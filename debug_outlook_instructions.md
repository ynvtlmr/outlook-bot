# How to Diagnose Outlook Draft Issues

If you are noticing that the bot creates drafts but leaves them empty (or missing text), run this diagnostic script to pinpoint the cause.

## Step 1: Run Diagnostics
1. Open Outlook (Classic/Legacy mode is recommended).
2. Open your terminal.
3. Run:
   ```bash
   uv run python tests/outlook_diagnostics.py
   ```

## Step 2: Interpret Results

The script runs 5 tests:
1. **Basic Write/Read**: If this fails, the bot has no permission to write to Outlook at all.
2. **Special Characters**: If this fails, emojis or foreign language characters are breaking the script.
3. **Large Payload**: If this fails (or hangs), there's a limit on how much text can be sent at once.
4. **HTML/Tag Injection**: If this fails, the way we try to format lines (using `<br>`) is being rejected.
5. **Rapid Read-Back**: If this fails, it's a "race condition"—Outlook is too slow to save the text before we try to close/read it.

## Step 3: Send Us the Output
Copy the text output from the terminal and send it to us so we can apply the correct fix.

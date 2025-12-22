# How to Fix SSL Errors in Outlook Bot

If you are seeing errors like `[SSL: CERTIFICATE_VERIFY_FAILED]`, it means your computer (specifically Python) doesn't trust the secure connection to Google. This is common on macOS.

## Step 1: Run Diagnostics
We have created a diagnostic script to confirm the issue.

1. Open your terminal.
2. Navigate to the bot folder.
3. Run the following command:
   ```bash
   uv run python tests/ssl_diagnostics.py
   ```

**What to look for:**
- **TEST 2:** Does it say "WARNING: Default cafile does not exist"? -> This is the problem.
- **TEST 4:** Does it fail? -> This confirms the bot cannot connect.
- **TEST 5:** Does it success? -> This confirms that installing certificates will fix it.

## Step 2: The Fix

### Option A: The "Official" Python Fix (Recommended)
If you installed Python from python.org, there is a script included to fix this.

1. Open Finder.
2. Go to **Applications** -> **Python 3.x** (e.g., Python 3.12).
3. Double-click on `Install Certificates.command`.
   - This opens a terminal window and installs the missing certificates.
4. Restart the bot.

### Option B: The "Certifi" Fix
If you don't have that file or it doesn't work:

1. Ensure the `certifi` package is installed:
   ```bash
   pip install certifi
   ```
2. You may need to tell Python to use it by setting an environment variable before running the bot:
   ```bash
   export SSL_CERT_FILE=$(python3 -m certifi)
   ```
   Then run the bot in the same terminal window.

### Option C: Reinstall Python via Homebrew
If you are using a system python or a messy install:
1. `brew install python`
2. Re-create your virtual environment.

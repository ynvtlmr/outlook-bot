# Outlook Bot

A macOS automation tool that bridges Microsoft Outlook with LLM providers (Gemini, OpenAI, OpenRouter) to automatically generate email reply drafts. Uses AppleScript for local Outlook access and Python for logic and AI integration.

## How It Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           OUTLOOK BOT WORKFLOW                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   1. SCAN           2. FILTER          3. GENERATE       4. CREATE     │
│   ┌─────────┐       ┌─────────┐        ┌─────────┐      ┌─────────┐   │
│   │ Outlook │──────▶│  Age &  │───────▶│   LLM   │─────▶│  Draft  │   │
│   │ Flagged │       │  Flag   │        │  Reply  │      │ in      │   │
│   │ Emails  │       │  Check  │        │         │      │ Outlook │   │
│   └─────────┘       └─────────┘        └─────────┘      └─────────┘   │
│                                                                         │
│   AppleScript       Python Logic       Gemini/OpenAI    AppleScript    │
│                                        /OpenRouter                      │
└─────────────────────────────────────────────────────────────────────────┘
```

1. **Scans Outlook** for email threads with an **"Active"** flag
2. **Filters threads** that haven't had activity for X days (configurable)
3. **Generates replies** using your configured LLM with a customizable persona
4. **Creates drafts** in Outlook for your review before sending

## Features

- **Multi-Provider LLM Support**: Gemini, OpenAI, and OpenRouter with automatic model discovery
- **Batch Processing**: Generates multiple replies in a single API call
- **GUI Configuration**: No code editing required for day-to-day use
- **Customizable Persona**: Define your writing style via `system_prompt.txt`
- **Smart Filtering**: Only processes stale threads, ignoring recent conversations
- **Corporate SSL Support**: Handles Zscaler and other corporate proxy certificates

---

## Requirements

| Requirement | Details |
|-------------|---------|
| **OS** | macOS (AppleScript required) |
| **Outlook** | Microsoft Outlook for Mac (Legacy mode recommended) |
| **Python** | 3.13+ (managed by `uv`) |
| **API Key** | At least one: Gemini, OpenAI, or OpenRouter |

> **Note**: The "New Outlook" has limited AppleScript support. For best results, use **Help → Revert to Legacy Outlook**.

---

## Quick Start

### 1. Clone & Install

```bash
git clone <repository_url>
cd outlook-bot

# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync
```

### 2. Configure API Key

Get an API key from one of:
- [Google AI Studio](https://aistudio.google.com/) (Gemini)
- [OpenAI Platform](https://platform.openai.com/) (OpenAI)
- [OpenRouter](https://openrouter.ai/) (OpenRouter)

Create a `.env` file:

```bash
echo "GEMINI_API_KEY=your_key_here" > .env
# Or for OpenAI:
# echo "OPENAI_API_KEY=your_key_here" > .env
# Or for OpenRouter:
# echo "OPENROUTER_API_KEY=your_key_here" > .env
```

### 3. Customize Persona

Edit `system_prompt.txt` to define how the AI writes emails:

```text
You are [Your Name], a [your role].
Your emails are short, professional, and friendly.
Sign off with "[Your Name]".
```

### 4. Run the Bot

**GUI Mode (Recommended):**
```bash
uv run python src/gui.py
```

**CLI Mode:**
```bash
uv run python src/main.py
```

---

## Configuration

### `config.yaml`

| Setting | Default | Description |
|---------|---------|-------------|
| `days_threshold` | `5` | Minimum days since last activity before a reply is generated |
| `default_reply` | `"Thank you..."` | Fallback message if all LLM providers fail |
| `preferred_model` | `null` | Specific model to try first (e.g., `gemini-1.5-flash`) |

### `.env`

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |

---

## GUI Features

| Tab | Features |
|-----|----------|
| **Configuration** | API keys, days threshold, default reply, model selection |
| **System Prompt** | Edit persona and writing style |
| **Console Output** | Real-time logs and status |

**Controls:**
- **START BOT**: Runs the email processing pipeline
- **STOP**: Waits for current task to complete, then stops
- **Save All Settings**: Persists all configuration changes
- **Test Buttons**: Verify API connectivity for each provider

---

## Development

### Commands

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src tests/

# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type check
uv run ty check .
```

### Diagnostic Scripts

Located in `tests/diagnostics/`, these scripts help debug specific issues:

| Script | Purpose |
|--------|---------|
| `diagnose_environment.py` | Check Python environment and dependencies |
| `diagnose_llm_health.py` | Test LLM provider connectivity |
| `diagnose_ingestion.py` | Debug email parsing issues |
| `diagnose_batch_replies.py` | Test batch reply generation |
| `ssl_diagnostics.py` | Debug SSL certificate issues |
| `outlook_diagnostics.py` | Test Outlook/AppleScript integration |

Run with: `uv run python tests/diagnostics/<script>.py`

### Project Structure

```
outlook-bot/
├── src/
│   ├── main.py           # CLI entry point & orchestration
│   ├── gui.py            # CustomTkinter GUI
│   ├── llm.py            # LLM providers (Gemini, OpenAI, OpenRouter)
│   ├── scraper.py        # AppleScript output parser
│   ├── outlook_client.py # AppleScript execution wrapper
│   ├── date_utils.py     # Date parsing utilities
│   ├── ssl_utils.py      # SSL/Zscaler certificate handling
│   ├── config.py         # Configuration loading
│   └── apple_scripts/    # AppleScript files for Outlook
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── diagnostics/      # Debugging & diagnostic scripts
├── config.yaml           # User configuration
├── system_prompt.txt     # LLM persona definition
└── .env                  # API keys (gitignored)
```

---

## Building for macOS

### Local Build

```bash
uv run pyinstaller outlook_bot.spec
```

The app will be created at `dist/OutlookBot.app`.

### Standalone App Data

When running as a packaged `.app`:
- Configuration stored in `~/Documents/OutlookBot/`
- First run creates this directory automatically
- Updates won't affect saved settings

---

## Troubleshooting

### "Outlook not responding" or empty data

1. Ensure Outlook is running
2. Switch to Legacy Outlook: **Help → Revert to Legacy Outlook**
3. Grant Terminal/IDE permission to control Outlook when prompted

### SSL Certificate Errors

The app includes automatic Zscaler/corporate proxy certificate handling:
1. SSL verification is **disabled by default** in `llm.py` for corporate environments
2. When enabled, it auto-discovers and merges Zscaler certificates with the system bundle
3. See `ssl_utils.py` for certificate bundle locations and customization

### No models detected

1. Check your API key is valid
2. Use the **Test** buttons in GUI to verify connectivity
3. Check console output for error messages

### Drafts created with empty content

This is a known limitation of Outlook's AppleScript API. The app uses UI automation (keystrokes) as a workaround. If this fails:
1. Ensure Outlook has focus when the script runs
2. Increase delays in `reply_to_message.scpt` if timing issues occur

---

## License

MIT

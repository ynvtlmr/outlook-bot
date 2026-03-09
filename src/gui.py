import os
import signal
import subprocess
import sys
import threading
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk
import dotenv
import yaml

import llm

# Import main script logic
import main
from cold_outreach import STRATEGIES
from config import (
    COLD_OUTREACH_DAILY_LIMIT,
    COLD_OUTREACH_ENABLED,
    COLD_OUTREACH_PROMPT_PATH,
    COLD_OUTREACH_STRATEGY,
    CONFIG_PATH,
    DAYS_THRESHOLD,

    ENV_GEMINI_API_KEY,
    ENV_OPENAI_API_KEY,
    ENV_OPENROUTER_API_KEY,
    ENV_PATH,
    FOLLOW_UP_DAILY_LIMIT,
    SALESFORCE_BCC,
    SYSTEM_PROMPT_PATH,
    CredentialManager,
)
from date_utils import get_current_date_context

# --- Configuration & Constants ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class StdoutRedirector:
    """Redirects stdout/stderr to a Tkinter widget in a thread-safe way."""

    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        # Schedule the update on the main thread
        self.text_widget.after(0, self._append_text, string)

    def flush(self):
        pass

    def _append_text(self, string):
        try:
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", string)
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
        except Exception:
            pass  # Widget might be destroyed


class OutlookBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Outlook Bot Manager")
        self.geometry("950x700")
        self.grid_columnconfigure(0, weight=1)
        # Row 0: Control Panel
        # Row 1: Tab View
        # Row 2: "Console Output" Label
        # Row 3: Log Box (needs to expand)
        self.grid_rowconfigure(3, weight=1)

        self.is_running = False
        self.bot_process: subprocess.Popen | None = None

        # --- Top Control Panel ---
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        self.btn_follow_up = ctk.CTkButton(
            self.control_frame,
            text="Follow Up",
            command=lambda: self.start_bot(main.run_follow_up),
            fg_color="green",
            hover_color="darkgreen",
        )
        self.btn_follow_up.pack(side="left", padx=10, pady=10)

        self.btn_cold_outreach = ctk.CTkButton(
            self.control_frame,
            text="Cold Outreach",
            command=lambda: self.start_bot(main.run_cold_outreach),
            fg_color="#1f538d",
            hover_color="#163d6a",
        )
        self.btn_cold_outreach.pack(side="left", padx=10, pady=10)

        self.btn_test_prompt = ctk.CTkButton(
            self.control_frame,
            text="Test Prompt",
            command=self.start_test_prompt,
            fg_color="#b8860b",
            hover_color="#8b6508",
        )
        self.btn_test_prompt.pack(side="left", padx=10, pady=10)

        self.btn_run_all = ctk.CTkButton(
            self.control_frame,
            text="Run All",
            command=lambda: self.start_bot(main.main),
            fg_color="green",
            hover_color="darkgreen",
        )
        self.btn_run_all.pack(side="left", padx=10, pady=10)

        self.btn_stop = ctk.CTkButton(
            self.control_frame,
            text="STOP",
            command=self.stop_bot,
            fg_color="darkred",
            hover_color="#800000",
            state="disabled",
        )
        self.btn_stop.pack(side="left", padx=10, pady=10)

        self.btn_save = ctk.CTkButton(
            self.control_frame, text="Save All Settings", command=self.save_config, fg_color="#1f538d"
        )  # Blueish
        self.btn_save.pack(side="right", padx=10, pady=10)

        # --- Tabs for Configuration ---
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.tab_view.add("Configuration")
        self.tab_view.add("System Prompt")
        self.tab_view.add("Cold Outreach")

        # -- Tab: Configuration --
        self.setup_config_tab()

        # -- Tab: System Prompt --
        self.setup_prompt_tab()

        # -- Tab: Cold Outreach --
        self.setup_cold_outreach_tab()

        # --- Log Output ---
        self.log_lbl = ctk.CTkLabel(self, text="Console Output:", font=("Arial", 12, "bold"))
        self.log_lbl.grid(row=2, column=0, sticky="nw", padx=20, pady=(10, 0))

        self.log_box = ctk.CTkTextbox(self, font=("Consolas", 12))
        self.log_box.grid(row=3, column=0, padx=20, pady=(5, 20), sticky="nsew")
        self.log_box.configure(state="disabled")

        # Load initial config
        self.load_all_configs()

        # Handle cleanup on close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_config_tab(self):
        tab = self.tab_view.tab("Configuration")
        tab.grid_columnconfigure(1, weight=1)

        # Gemini API Key
        lbl_key = ctk.CTkLabel(tab, text="Gemini API Key:")
        lbl_key.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_api_key = ctk.CTkEntry(tab, width=400, show="*")  # Masked by default
        self.entry_api_key.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Toggle visibility (Gemini)
        self.chk_show_key = ctk.CTkCheckBox(tab, text="Show", command=self.toggle_key_visibility, width=60)
        self.chk_show_key.grid(row=0, column=2, padx=10, pady=10)

        # Test Button (Gemini)
        self.btn_test_gemini = ctk.CTkButton(tab, text="Test", command=self.test_gemini, width=60, fg_color="#333333")
        self.btn_test_gemini.grid(row=0, column=3, padx=10, pady=10)

        # OpenAI API Key
        lbl_openai = ctk.CTkLabel(tab, text="OpenAI API Key:")
        lbl_openai.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_openai_key = ctk.CTkEntry(tab, width=400, show="*")
        self.entry_openai_key.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        # Toggle visibility (OpenAI)
        self.chk_show_openai = ctk.CTkCheckBox(tab, text="Show", command=self.toggle_openai_visibility, width=60)
        self.chk_show_openai.grid(row=1, column=2, padx=10, pady=10)

        # Test Button (OpenAI)
        self.btn_test_openai = ctk.CTkButton(tab, text="Test", command=self.test_openai, width=60, fg_color="#333333")
        self.btn_test_openai.grid(row=1, column=3, padx=10, pady=10)

        # OpenRouter API Key
        lbl_or = ctk.CTkLabel(tab, text="OpenRouter Key:")
        lbl_or.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_or_key = ctk.CTkEntry(tab, width=400, show="*")
        self.entry_or_key.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # Toggle visibility (OpenRouter)
        self.chk_show_or = ctk.CTkCheckBox(tab, text="Show", command=self.toggle_or_visibility, width=60)
        self.chk_show_or.grid(row=2, column=2, padx=10, pady=10)

        # Test Button (OpenRouter)
        self.btn_test_or = ctk.CTkButton(tab, text="Test", command=self.test_or, width=60, fg_color="#333333")
        self.btn_test_or.grid(row=2, column=3, padx=10, pady=10)

        # Days Threshold
        lbl_days = ctk.CTkLabel(tab, text="Days Threshold:")
        lbl_days.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.entry_days = ctk.CTkEntry(tab, width=100)
        self.entry_days.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # Follow-Up Daily Limit
        lbl_fu_limit = ctk.CTkLabel(tab, text="Follow-Up Daily Limit:")
        lbl_fu_limit.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.entry_follow_up_limit = ctk.CTkEntry(tab, width=100)
        self.entry_follow_up_limit.grid(row=4, column=1, padx=10, pady=10, sticky="w")

        # Salesforce BCC
        lbl_bcc = ctk.CTkLabel(tab, text="Salesforce BCC:")
        lbl_bcc.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.entry_bcc = ctk.CTkEntry(tab, width=400)
        self.entry_bcc.grid(row=5, column=1, padx=10, pady=10, sticky="ew")

        # Model Provider Selection
        lbl_provider = ctk.CTkLabel(tab, text="Model Provider:")
        lbl_provider.grid(row=6, column=0, padx=10, pady=10, sticky="nw")
        self.combo_provider = ctk.CTkComboBox(tab, state="readonly", command=self.on_provider_change)
        self.combo_provider.grid(row=6, column=1, padx=10, pady=10, sticky="ew")
        self.combo_provider.set("All")
        self.combo_provider.configure(values=["All", "Gemini", "OpenAI", "OpenRouter"])

        # Search Entry
        self.entry_search = ctk.CTkEntry(tab, placeholder_text="Search models...")
        self.entry_search.grid(row=6, column=2, padx=10, pady=10, sticky="ew")
        self.entry_search.bind("<KeyRelease>", self.on_search_change)

        # Model Selection
        lbl_model = ctk.CTkLabel(tab, text="Preferred Model:")
        lbl_model.grid(row=7, column=0, padx=10, pady=10, sticky="nw")
        self.combo_model = ctk.CTkComboBox(tab, state="readonly", command=self.on_model_selected)
        self.combo_model.grid(row=7, column=1, padx=10, pady=10, sticky="ew")

        # Refresh Models Button
        self.btn_refresh_models = ctk.CTkButton(tab, text="Refresh Models", command=self.refresh_models_list)
        self.btn_refresh_models.grid(row=7, column=2, padx=10, pady=10, sticky="nw")

        # Store available models list for dropdown (list of dicts from llm service: {'id':..., 'provider':...})
        self.available_models_data = []

    def setup_prompt_tab(self):
        tab = self.tab_view.tab("System Prompt")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Immutable Date Context
        date_str = get_current_date_context()
        self.lbl_date_context = ctk.CTkEntry(tab, fg_color="transparent", border_width=0)
        self.lbl_date_context.insert(0, date_str)
        self.lbl_date_context.configure(state="readonly")
        self.lbl_date_context.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        self.txt_prompt = ctk.CTkTextbox(tab, wrap="word")
        self.txt_prompt.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    def setup_cold_outreach_tab(self):
        tab = self.tab_view.tab("Cold Outreach")
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(5, weight=1)

        # Enable/Disable Toggle
        lbl_enable = ctk.CTkLabel(tab, text="Enable:")
        lbl_enable.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.switch_cold_outreach = ctk.CTkSwitch(tab, text="Cold Outreach Enabled")
        self.switch_cold_outreach.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # CSV File Path
        lbl_csv = ctk.CTkLabel(tab, text="CSV File:")
        lbl_csv.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        csv_frame = ctk.CTkFrame(tab, fg_color="transparent")
        csv_frame.grid(row=1, column=1, padx=10, pady=10, sticky="ew", columnspan=2)
        csv_frame.grid_columnconfigure(0, weight=1)

        self.entry_csv_path = ctk.CTkEntry(csv_frame, width=400)
        self.entry_csv_path.grid(row=0, column=0, sticky="ew")

        self.btn_browse_csv = ctk.CTkButton(
            csv_frame, text="Browse", command=self.browse_csv, width=80, fg_color="#333333"
        )
        self.btn_browse_csv.grid(row=0, column=1, padx=(10, 0))

        # Daily Limit
        lbl_limit = ctk.CTkLabel(tab, text="Daily Limit:")
        lbl_limit.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_daily_limit = ctk.CTkEntry(tab, width=100)
        self.entry_daily_limit.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # Lead Strategy
        strategy_labels = {"default": "Default (CSV Order)", "round_robin": "Round-Robin", "product_fit": "Product-Fit Scoring"}
        self._strategy_label_to_key = {v: k for k, v in strategy_labels.items()}
        self._strategy_key_to_label = strategy_labels

        lbl_strategy = ctk.CTkLabel(tab, text="Lead Strategy:")
        lbl_strategy.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.combo_strategy = ctk.CTkComboBox(
            tab,
            state="readonly",
            values=list(strategy_labels.values()),
        )
        self.combo_strategy.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        self.combo_strategy.set(strategy_labels["default"])

        # Cold Outreach Prompt
        lbl_prompt = ctk.CTkLabel(tab, text="Outreach Prompt:")
        lbl_prompt.grid(row=4, column=0, padx=10, pady=(10, 0), sticky="nw")
        self.txt_cold_prompt = ctk.CTkTextbox(tab, wrap="word")
        self.txt_cold_prompt.grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    def browse_csv(self):
        path = filedialog.askopenfilename(
            title="Select Salesforce CSV Export",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.entry_csv_path.delete(0, "end")
            self.entry_csv_path.insert(0, path)

    def _toggle_visibility(self, checkbox: ctk.CTkCheckBox, entry: ctk.CTkEntry) -> None:
        """Toggle password visibility for an entry field based on checkbox state."""
        entry.configure(show="" if checkbox.get() else "*")

    def toggle_key_visibility(self) -> None:
        self._toggle_visibility(self.chk_show_key, self.entry_api_key)

    def toggle_openai_visibility(self) -> None:
        self._toggle_visibility(self.chk_show_openai, self.entry_openai_key)

    def toggle_or_visibility(self) -> None:
        self._toggle_visibility(self.chk_show_or, self.entry_or_key)

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def load_all_configs(self):
        self.log("[Info] Loading configurations...\n")

        # 1. Load Config YAML
        data = {}
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    data = yaml.safe_load(f) or {}
        except (yaml.YAMLError, OSError) as e:
            self.log(f"[Error] Failed to load config.yaml: {e}\n")

        # Days
        self.entry_days.delete(0, "end")
        self.entry_days.insert(0, str(data.get("days_threshold", DAYS_THRESHOLD)))

        # Follow-Up Daily Limit
        self.entry_follow_up_limit.delete(0, "end")
        self.entry_follow_up_limit.insert(0, str(data.get("follow_up_daily_limit", FOLLOW_UP_DAILY_LIMIT)))

        # Salesforce BCC
        self.entry_bcc.delete(0, "end")
        self.entry_bcc.insert(0, str(data.get("salesforce_bcc", SALESFORCE_BCC)))

        # Note: Models are loaded dynamically by refresh_models_list()

        # 2. Load .env
        try:
            if os.path.exists(ENV_PATH):
                dotenv.load_dotenv(ENV_PATH, override=True)
                api_key = CredentialManager.get_gemini_key() or ""
                self.entry_api_key.delete(0, "end")
                self.entry_api_key.insert(0, api_key)

                openai_key = CredentialManager.get_openai_key() or ""
                self.entry_openai_key.delete(0, "end")
                self.entry_openai_key.insert(0, openai_key)

                or_key = CredentialManager.get_openrouter_key() or ""
                self.entry_or_key.delete(0, "end")
                self.entry_or_key.insert(0, or_key)
        except OSError as e:
            self.log(f"[Error] Failed to load .env: {e}\n")

        # 3. Load Preferred Model
        preferred_model = data.get("preferred_model", "")
        # We'll set this 'preferred_model' as a temporary attribute so refresh_models_list can pick it up
        self._initial_preferred_model = preferred_model

        # 4. Detect Models (Use the service)
        # We delay this slightly or run it now if we have keys
        self.refresh_models_list(use_initial_pref=True)

        # 5. Load System Prompt
        try:
            if os.path.exists(SYSTEM_PROMPT_PATH):
                with open(SYSTEM_PROMPT_PATH, "r") as f:
                    content = f.read()
                self.txt_prompt.delete("0.0", "end")
                self.txt_prompt.insert("0.0", content)
        except OSError as e:
            self.log(f"[Error] Failed to load system_prompt.txt: {e}\n")

        # 5b. Load Cold Outreach settings
        if data.get("cold_outreach_enabled", COLD_OUTREACH_ENABLED):
            self.switch_cold_outreach.select()
        else:
            self.switch_cold_outreach.deselect()

        self.entry_csv_path.delete(0, "end")
        self.entry_csv_path.insert(0, str(data.get("cold_outreach_csv_path", "")))

        self.entry_daily_limit.delete(0, "end")
        self.entry_daily_limit.insert(0, str(data.get("cold_outreach_daily_limit", COLD_OUTREACH_DAILY_LIMIT)))

        # Lead Strategy
        strategy_key = data.get("cold_outreach_strategy", COLD_OUTREACH_STRATEGY)
        strategy_label = self._strategy_key_to_label.get(strategy_key, self._strategy_key_to_label["default"])
        self.combo_strategy.set(strategy_label)

        # Load Cold Outreach Prompt
        try:
            if os.path.exists(COLD_OUTREACH_PROMPT_PATH):
                with open(COLD_OUTREACH_PROMPT_PATH, "r") as f:
                    cold_content = f.read()
                self.txt_cold_prompt.delete("0.0", "end")
                self.txt_cold_prompt.insert("0.0", cold_content)
        except OSError as e:
            self.log(f"[Error] Failed to load cold_outreach_prompt.txt: {e}\n")

        # 6. Auto-Test Connections if keys exist
        if self.entry_api_key.get().strip():
            self.test_gemini()
        if self.entry_openai_key.get().strip():
            self.test_openai()
        if self.entry_or_key.get().strip():
            self.test_or()

    def save_config(self):
        success = True

        # 1. Save YAML
        try:
            # Read existing config to preserve any fields we don't manage
            existing_data = {}
            if os.path.exists(CONFIG_PATH):
                try:
                    with open(CONFIG_PATH, "r") as f:
                        existing_data = yaml.safe_load(f) or {}
                except Exception:
                    pass  # If read fails, start fresh

            try:
                days = int(self.entry_days.get().strip())
            except ValueError:
                self.log("[Error] Invalid Days Threshold. Must be an integer.\n")
                success = False
                return success

            try:
                follow_up_daily_limit = int(self.entry_follow_up_limit.get().strip())
            except ValueError:
                self.log("[Warning] Invalid follow-up daily limit. Using default.\n")
                follow_up_daily_limit = FOLLOW_UP_DAILY_LIMIT

            salesforce_bcc = self.entry_bcc.get().strip()
            preferred_model = self.combo_model.get()
            cold_outreach_enabled = bool(self.switch_cold_outreach.get())
            cold_outreach_csv_path = self.entry_csv_path.get().strip()
            cold_outreach_strategy = self._strategy_label_to_key.get(self.combo_strategy.get(), "default")
            try:
                cold_outreach_daily_limit = int(self.entry_daily_limit.get().strip())
            except ValueError:
                self.log("[Warning] Invalid daily limit. Using default.\n")
                cold_outreach_daily_limit = COLD_OUTREACH_DAILY_LIMIT

            # Update only the fields we manage, preserve others
            data = existing_data.copy()
            data.update(
                {
                    "days_threshold": days,
                    "follow_up_daily_limit": follow_up_daily_limit,
                    "salesforce_bcc": salesforce_bcc,
                    "preferred_model": preferred_model,
                    "cold_outreach_enabled": cold_outreach_enabled,
                    "cold_outreach_csv_path": cold_outreach_csv_path,
                    "cold_outreach_daily_limit": cold_outreach_daily_limit,
                    "cold_outreach_strategy": cold_outreach_strategy,
                }
            )

            with open(CONFIG_PATH, "w") as f:
                yaml.dump(data, f)
        except (yaml.YAMLError, OSError) as e:
            self.log(f"[Error] Failed to save config.yaml: {e}\n")
            success = False

        # 2. Save .env
        try:
            new_key = self.entry_api_key.get().strip()

            # Use dotenv.set_key to preserve other vars if any
            dotenv.set_key(ENV_PATH, ENV_GEMINI_API_KEY, new_key)
            os.environ[ENV_GEMINI_API_KEY] = new_key

            new_openai_key = self.entry_openai_key.get().strip()
            dotenv.set_key(ENV_PATH, ENV_OPENAI_API_KEY, new_openai_key)
            os.environ[ENV_OPENAI_API_KEY] = new_openai_key

            new_or_key = self.entry_or_key.get().strip()
            dotenv.set_key(ENV_PATH, ENV_OPENROUTER_API_KEY, new_or_key)
            os.environ[ENV_OPENROUTER_API_KEY] = new_or_key
        except OSError as e:
            self.log(f"[Error] Failed to save .env: {e}\n")
            success = False

        # 3. Save System Prompt
        try:
            prompt_content = self.txt_prompt.get("0.0", "end").strip()
            with open(SYSTEM_PROMPT_PATH, "w") as f:
                f.write(prompt_content)
        except OSError as e:
            self.log(f"[Error] Failed to save system_prompt.txt: {e}\n")
            success = False

        # 4. Save Cold Outreach Prompt
        try:
            cold_prompt_content = self.txt_cold_prompt.get("0.0", "end").strip()
            with open(COLD_OUTREACH_PROMPT_PATH, "w") as f:
                f.write(cold_prompt_content)
        except OSError as e:
            self.log(f"[Error] Failed to save cold_outreach_prompt.txt: {e}\n")
            success = False

        if success:
            self.log("[Info] All settings saved successfully.\n")
        return success

    def start_test_prompt(self):
        """Open a file picker for a .txt email, then run test prompt."""
        if self.is_running:
            return

        email_file = filedialog.askopenfilename(
            title="Select Email .txt File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not email_file:
            return

        # Save settings first
        if not self.save_config():
            return

        self.is_running = True
        self.btn_follow_up.configure(state="disabled")
        self.btn_cold_outreach.configure(state="disabled")
        self.btn_test_prompt.configure(state="disabled")
        self.btn_run_all.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.log("\n" + "=" * 30 + "\nStarting Test Prompt...\n" + "=" * 30 + "\n")

        threading.Thread(target=self.run_process_raw, args=(["--test-prompt", email_file],), daemon=True).start()

    def start_bot(self, target_fn: Callable = None):
        if self.is_running:
            return

        if target_fn is None:
            target_fn = main.main

        # Save before run
        if not self.save_config():
            return

        # Map function to CLI entry point
        fn_to_cmd = {
            main.run_follow_up: "follow_up",
            main.run_cold_outreach: "cold_outreach",
            main.main: "run_all",
        }
        cmd_arg = fn_to_cmd.get(target_fn, "run_all")

        self.is_running = True
        self.btn_follow_up.configure(state="disabled")
        self.btn_cold_outreach.configure(state="disabled")
        self.btn_test_prompt.configure(state="disabled")
        self.btn_run_all.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.log("\n" + "=" * 30 + "\nStarting Outlook Bot...\n" + "=" * 30 + "\n")

        # Run as a subprocess so STOP can kill entire process tree
        threading.Thread(target=self.run_process, args=(cmd_arg,), daemon=True).start()

    def run_process_raw(self, extra_args: list[str]):
        """Run main.py with arbitrary CLI args."""
        python = sys.executable
        script = os.path.join(os.path.dirname(__file__), "main.py")

        try:
            self.bot_process = subprocess.Popen(
                [python, "-u", script] + extra_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

            for line in self.bot_process.stdout:
                text = line.decode("utf-8", errors="replace")
                self.log_box.after(0, self._append_log, text)

            self.bot_process.wait()

        except Exception as e:
            self.log_box.after(0, self._append_log, f"\n[Error: {e}]\n")
        finally:
            self.bot_process = None
            self.after(0, self.process_finished)

    def run_process(self, cmd_arg: str):
        python = sys.executable
        script = os.path.join(os.path.dirname(__file__), "main.py")

        try:
            self.bot_process = subprocess.Popen(
                [python, "-u", script, f"--{cmd_arg.replace('_', '-')}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

            # Stream output line by line to the GUI
            for line in self.bot_process.stdout:
                text = line.decode("utf-8", errors="replace")
                self.log_box.after(0, self._append_log, text)

            self.bot_process.wait()

        except Exception as e:
            self.log_box.after(0, self._append_log, f"\n[Error: {e}]\n")
        finally:
            self.bot_process = None
            self.after(0, self.process_finished)

    def _append_log(self, text: str):
        try:
            self.log_box.configure(state="normal")
            self.log_box.insert("end", text)
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        except Exception:
            pass

    def process_finished(self):
        self.is_running = False
        self.btn_follow_up.configure(state="normal")
        self.btn_cold_outreach.configure(state="normal")
        self.btn_test_prompt.configure(state="normal")
        self.btn_run_all.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.log("\n[Process finished]\n")

    def _kill_bot_process(self):
        """Kill the bot subprocess and all its children (AppleScripts)."""
        proc = self.bot_process
        if proc and proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                try:
                    proc.kill()
                except (ProcessLookupError, PermissionError, OSError):
                    pass
        self.bot_process = None

    def stop_bot(self):
        self._kill_bot_process()
        if self.is_running:
            self.log("\n[Stopped]\n")
            self.process_finished()

    def refresh_models_list(self, use_initial_pref=False):
        self.log("[Info] Detecting available models...\n")
        try:
            # Explicitly set ENV from UI before detecting.
            os.environ[ENV_GEMINI_API_KEY] = self.entry_api_key.get().strip()
            os.environ[ENV_OPENAI_API_KEY] = self.entry_openai_key.get().strip()
            os.environ[ENV_OPENROUTER_API_KEY] = self.entry_or_key.get().strip()

            service = llm.LLMService()
            # ACCESS RAW DATA instead of list strings, so we know provider
            models_data = service.available_models  # list of {'id':..., 'provider':...}

            # Store full model data
            self.available_models_data = models_data  # store list of dicts

            if not models_data:
                self.log("[Warning] No models detected. Please check API keys.\n")
                self.combo_model.configure(values=["No models available"])
                self.combo_model.set("No models available")
                return

            self.log(f"[Info] Found {len(models_data)} models total.\n")

            # Decide on preferred model
            pref = None
            if use_initial_pref and hasattr(self, "_initial_preferred_model"):
                pref = self._initial_preferred_model

            # Determine which provider contains this preferred model to set correct filter
            if pref:
                # Find provider for this model
                found_model = next((m for m in models_data if m["id"] == pref), None)
                if found_model:
                    found_prov = found_model.get("provider", "").lower()

                    # Map internal provider id to Dropdown display string
                    provider_map = {"gemini": "Gemini", "openai": "OpenAI", "openrouter": "OpenRouter"}

                    display_prov = provider_map.get(found_prov, "All")
                    self.combo_provider.set(display_prov)

            # Update dropdown based on current provider/preferred selection
            self.update_model_dropdown(preferred_model=pref)

        except Exception as e:
            self.log(f"[Error] Failed to detect models: {e}\n")
            import traceback

            traceback.print_exc()
            self.combo_model.configure(values=["Error loading models"])
            self.combo_model.set("Error loading models")

    def on_provider_change(self, choice):
        """Called when user selects a provider filter."""
        self.log(f"[Info] Provider filter changed to: {choice}\n")
        self.update_model_dropdown()

    def on_search_change(self, event=None):
        """Called when user types in search box."""
        self.update_model_dropdown()

    def update_model_dropdown(self, preferred_model=None):
        """Filters available_models_data based on combo_provider AND search text, then updates combo_model."""
        provider_filter = self.combo_provider.get()  # "All", "Gemini", "OpenAI"
        search_text = self.entry_search.get().lower().strip()

        filtered_ids = []
        for m in self.available_models_data:
            p = m.get("provider", "").lower()
            mid = m.get("id", "")

            # Filter by Provider
            if provider_filter != "All":
                if provider_filter == "Gemini" and p != "gemini":
                    continue
                if provider_filter == "OpenAI" and p != "openai":
                    continue
                if provider_filter == "OpenRouter" and p != "openrouter":
                    continue

            # Filter by Search Text
            if search_text and search_text not in mid.lower():
                continue

            filtered_ids.append(mid)

        if not filtered_ids:
            self.combo_model.configure(values=["No matching models"])
            self.combo_model.set("No matching models")
            return

        self.combo_model.configure(values=filtered_ids)

        # Try to keep current selection if valid
        current = self.combo_model.get()

        # If specific preferred_model requested (e.g. from load), try that
        if preferred_model and preferred_model in filtered_ids:
            self.combo_model.set(preferred_model)
        elif current in filtered_ids:
            # Keep current
            self.combo_model.set(current)
        else:
            # Default to first
            self.combo_model.set(filtered_ids[0])

        # self.log(f"[Debug] Showing {len(filtered_ids)} models for {provider_filter}\n")

    def on_model_selected(self, choice):
        """Called when user selects a model from the dropdown."""
        self.log(f"[Info] Model selection changed to: {choice}\n")

    def on_close(self):
        self._kill_bot_process()
        self.destroy()

    def _test_connection(self, provider: str, key: str, button: ctk.CTkButton, test_fn: Callable) -> None:
        """Generic connection test handler for any provider."""
        self.log(f"[Info] Testing {provider} connection...\n")
        button.configure(text="...", state="disabled")

        def _target():
            success, msg = test_fn(key)
            self.after(0, lambda: self._handle_test_result(button, success, msg))

        threading.Thread(target=_target, daemon=True).start()

    def test_gemini(self) -> None:
        """Test Gemini API connectivity using the entered API key."""
        self._test_connection(
            "Gemini", self.entry_api_key.get().strip(), self.btn_test_gemini, llm.LLMService.test_gemini_connection
        )

    def test_openai(self) -> None:
        """Test OpenAI API connectivity using the entered API key."""
        self._test_connection(
            "OpenAI", self.entry_openai_key.get().strip(), self.btn_test_openai, llm.LLMService.test_openai_connection
        )

    def test_or(self) -> None:
        """Test OpenRouter API connectivity using the entered API key."""
        self._test_connection(
            "OpenRouter", self.entry_or_key.get().strip(), self.btn_test_or, llm.LLMService.test_openrouter_connection
        )

    def _handle_test_result(self, button: ctk.CTkButton, success: bool, message: str) -> None:
        button.configure(text="Test", state="normal")
        if success:
            button.configure(fg_color="green", hover_color="darkgreen")
            self.log(f"[Success] {message}\n")
        else:
            button.configure(fg_color="darkred", hover_color="#800000")
            self.log(f"[Error] {message}\n")


if __name__ == "__main__":
    app = OutlookBotGUI()
    app.mainloop()

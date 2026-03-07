"""CustomTkinter GUI for Outlook Bot configuration and real-time monitoring."""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys
import threading
from tkinter import filedialog
from typing import TYPE_CHECKING, Any

import customtkinter as ctk
import dotenv
import yaml

from outlook_bot.core.config import (
    ENV_GEMINI_API_KEY,
    ENV_OPENAI_API_KEY,
    ENV_OPENROUTER_API_KEY,
    Config,
    CredentialManager,
    Paths,
)
from outlook_bot.providers.registry import ProviderRegistry
from outlook_bot.utils.dates import get_current_date_context

if TYPE_CHECKING:
    from collections.abc import Callable

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class OutlookBotGUI(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.paths = Paths()

        self.title("Outlook Bot Manager")
        self.geometry("800x700")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.is_running = False
        self.bot_process: subprocess.Popen | None = None

        self._setup_control_panel()
        self._setup_tabs()
        self._setup_log_output()

        self.load_all_configs()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_control_panel(self) -> None:
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        self.btn_follow_up = ctk.CTkButton(
            self.control_frame,
            text="Follow Up",
            command=lambda: self.start_bot("follow-up"),
            fg_color="green",
            hover_color="darkgreen",
        )
        self.btn_follow_up.pack(side="left", padx=10, pady=10)

        self.btn_cold_outreach = ctk.CTkButton(
            self.control_frame,
            text="Cold Outreach",
            command=lambda: self.start_bot("cold-outreach"),
            fg_color="#1f538d",
            hover_color="#163d6a",
        )
        self.btn_cold_outreach.pack(side="left", padx=10, pady=10)

        self.btn_run_all = ctk.CTkButton(
            self.control_frame,
            text="Run All",
            command=lambda: self.start_bot("run-all"),
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
            self.control_frame,
            text="Save All Settings",
            command=self.save_config,
            fg_color="#1f538d",
        )
        self.btn_save.pack(side="right", padx=10, pady=10)

    def _setup_tabs(self) -> None:
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.tab_view.add("Configuration")
        self.tab_view.add("System Prompt")
        self.tab_view.add("Cold Outreach")

        self._setup_config_tab()
        self._setup_prompt_tab()
        self._setup_cold_outreach_tab()

    def _setup_config_tab(self) -> None:
        tab = self.tab_view.tab("Configuration")
        tab.grid_columnconfigure(1, weight=1)

        # API Key entries
        self.entry_api_key = self._add_api_key_row(tab, "Gemini API Key:", 0, self.test_gemini)
        self.entry_openai_key = self._add_api_key_row(tab, "OpenAI API Key:", 1, self.test_openai)
        self.entry_or_key = self._add_api_key_row(tab, "OpenRouter Key:", 2, self.test_or)

        # Store test buttons for state management
        self.btn_test_gemini = tab.grid_slaves(row=0, column=3)[0]
        self.btn_test_openai = tab.grid_slaves(row=1, column=3)[0]
        self.btn_test_or = tab.grid_slaves(row=2, column=3)[0]

        # Days Threshold
        ctk.CTkLabel(tab, text="Days Threshold:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.entry_days = ctk.CTkEntry(tab, width=100)
        self.entry_days.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # Default Reply
        ctk.CTkLabel(tab, text="Default Reply:").grid(row=4, column=0, padx=10, pady=10, sticky="nw")
        self.txt_default_reply = ctk.CTkTextbox(tab, height=60)
        self.txt_default_reply.grid(row=4, column=1, padx=10, pady=10, sticky="ew", columnspan=2)

        # Salesforce BCC
        ctk.CTkLabel(tab, text="Salesforce BCC:").grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.entry_bcc = ctk.CTkEntry(tab, width=400)
        self.entry_bcc.grid(row=5, column=1, padx=10, pady=10, sticky="ew")

        # Provider filter + search
        ctk.CTkLabel(tab, text="Model Provider:").grid(row=6, column=0, padx=10, pady=10, sticky="nw")
        self.combo_provider = ctk.CTkComboBox(tab, state="readonly", command=self._on_provider_change)
        self.combo_provider.grid(row=6, column=1, padx=10, pady=10, sticky="ew")
        self.combo_provider.set("All")
        self.combo_provider.configure(values=["All", "Gemini", "OpenAI", "OpenRouter"])

        self.entry_search = ctk.CTkEntry(tab, placeholder_text="Search models...")
        self.entry_search.grid(row=6, column=2, padx=10, pady=10, sticky="ew")
        self.entry_search.bind("<KeyRelease>", self._on_search_change)

        # Model selection
        ctk.CTkLabel(tab, text="Preferred Model:").grid(row=7, column=0, padx=10, pady=10, sticky="nw")
        self.combo_model = ctk.CTkComboBox(tab, state="readonly")
        self.combo_model.grid(row=7, column=1, padx=10, pady=10, sticky="ew")

        self.btn_refresh_models = ctk.CTkButton(tab, text="Refresh Models", command=self.refresh_models_list)
        self.btn_refresh_models.grid(row=7, column=2, padx=10, pady=10, sticky="nw")

        self.available_models_data: list[dict[str, str]] = []

    def _add_api_key_row(self, tab, label: str, row: int, test_fn: Callable) -> ctk.CTkEntry:
        ctk.CTkLabel(tab, text=label).grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry = ctk.CTkEntry(tab, width=400, show="*")
        entry.grid(row=row, column=1, padx=10, pady=10, sticky="ew")

        chk = ctk.CTkCheckBox(tab, text="Show", width=60, command=lambda e=entry, c=None: None)  # placeholder
        chk.grid(row=row, column=2, padx=10, pady=10)
        chk.configure(command=lambda e=entry, cb=chk: e.configure(show="" if cb.get() else "*"))

        btn = ctk.CTkButton(tab, text="Test", command=test_fn, width=60, fg_color="#333333")
        btn.grid(row=row, column=3, padx=10, pady=10)

        return entry

    def _setup_prompt_tab(self) -> None:
        tab = self.tab_view.tab("System Prompt")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        date_entry = ctk.CTkEntry(tab, fg_color="transparent", border_width=0)
        date_entry.insert(0, get_current_date_context())
        date_entry.configure(state="readonly")
        date_entry.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        self.txt_prompt = ctk.CTkTextbox(tab, wrap="word")
        self.txt_prompt.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    def _setup_cold_outreach_tab(self) -> None:
        tab = self.tab_view.tab("Cold Outreach")
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(tab, text="Enable:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.switch_cold_outreach = ctk.CTkSwitch(tab, text="Cold Outreach Enabled")
        self.switch_cold_outreach.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(tab, text="CSV File:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        csv_frame = ctk.CTkFrame(tab, fg_color="transparent")
        csv_frame.grid(row=1, column=1, padx=10, pady=10, sticky="ew", columnspan=2)
        csv_frame.grid_columnconfigure(0, weight=1)
        self.entry_csv_path = ctk.CTkEntry(csv_frame, width=400)
        self.entry_csv_path.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(csv_frame, text="Browse", command=self._browse_csv, width=80, fg_color="#333333").grid(
            row=0, column=1, padx=(10, 0)
        )

        ctk.CTkLabel(tab, text="Daily Limit:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_daily_limit = ctk.CTkEntry(tab, width=100)
        self.entry_daily_limit.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(tab, text="Outreach Prompt:").grid(row=3, column=0, padx=10, pady=(10, 0), sticky="nw")
        self.txt_cold_prompt = ctk.CTkTextbox(tab, wrap="word")
        self.txt_cold_prompt.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    def _setup_log_output(self) -> None:
        ctk.CTkLabel(self, text="Console Output:", font=("Arial", 12, "bold")).grid(
            row=2, column=0, sticky="nw", padx=20, pady=(10, 0)
        )
        self.log_box = ctk.CTkTextbox(self, font=("Consolas", 12))
        self.log_box.grid(row=3, column=0, padx=20, pady=(5, 20), sticky="nsew")
        self.log_box.configure(state="disabled")

    def log(self, message: str) -> None:
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _append_log(self, text: str) -> None:
        with contextlib.suppress(Exception):
            self.log(text)

    def _browse_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Salesforce CSV Export",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.entry_csv_path.delete(0, "end")
            self.entry_csv_path.insert(0, path)

    def load_all_configs(self) -> None:
        self.log("[Info] Loading configurations...\n")

        config = Config.load(self.paths)

        self.entry_days.delete(0, "end")
        self.entry_days.insert(0, str(config.days_threshold))

        self.txt_default_reply.delete("0.0", "end")
        self.txt_default_reply.insert("0.0", config.default_reply)

        self.entry_bcc.delete(0, "end")
        self.entry_bcc.insert(0, config.salesforce_bcc)

        # Load API keys
        try:
            if self.paths.env_path.exists():
                dotenv.load_dotenv(self.paths.env_path, override=True)
            for entry, getter in [
                (self.entry_api_key, CredentialManager.get_gemini_key),
                (self.entry_openai_key, CredentialManager.get_openai_key),
                (self.entry_or_key, CredentialManager.get_openrouter_key),
            ]:
                entry.delete(0, "end")
                entry.insert(0, getter() or "")
        except OSError as e:
            self.log(f"[Error] Failed to load .env: {e}\n")

        self._initial_preferred_model = config.preferred_model
        self.refresh_models_list(use_initial_pref=True)

        # System prompt
        try:
            if self.paths.system_prompt_path.exists():
                self.txt_prompt.delete("0.0", "end")
                self.txt_prompt.insert("0.0", self.paths.system_prompt_path.read_text())
        except OSError as e:
            self.log(f"[Error] Failed to load system_prompt.txt: {e}\n")

        # Cold outreach
        if config.cold_outreach_enabled:
            self.switch_cold_outreach.select()
        else:
            self.switch_cold_outreach.deselect()

        self.entry_csv_path.delete(0, "end")
        self.entry_csv_path.insert(0, config.cold_outreach_csv_path)

        self.entry_daily_limit.delete(0, "end")
        self.entry_daily_limit.insert(0, str(config.cold_outreach_daily_limit))

        try:
            if self.paths.cold_outreach_prompt_path.exists():
                self.txt_cold_prompt.delete("0.0", "end")
                self.txt_cold_prompt.insert("0.0", self.paths.cold_outreach_prompt_path.read_text())
        except OSError as e:
            self.log(f"[Error] Failed to load cold_outreach_prompt.txt: {e}\n")

        if self.entry_api_key.get().strip():
            self.test_gemini()
        if self.entry_openai_key.get().strip():
            self.test_openai()
        if self.entry_or_key.get().strip():
            self.test_or()

    def save_config(self) -> bool:
        success = True

        try:
            days = int(self.entry_days.get().strip())
        except ValueError:
            self.log("[Error] Invalid Days Threshold. Must be an integer.\n")
            return False

        config = Config(
            days_threshold=days,
            default_reply=self.txt_default_reply.get("0.0", "end").strip(),
            preferred_model=self.combo_model.get(),
            salesforce_bcc=self.entry_bcc.get().strip(),
            cold_outreach_enabled=bool(self.switch_cold_outreach.get()),
            cold_outreach_csv_path=self.entry_csv_path.get().strip(),
            cold_outreach_daily_limit=int(self.entry_daily_limit.get().strip() or "10"),
        )

        try:
            config.save(self.paths)
        except (yaml.YAMLError, OSError) as e:
            self.log(f"[Error] Failed to save config.yaml: {e}\n")
            success = False

        try:
            env_path = str(self.paths.env_path)
            for env_var, entry in [
                (ENV_GEMINI_API_KEY, self.entry_api_key),
                (ENV_OPENAI_API_KEY, self.entry_openai_key),
                (ENV_OPENROUTER_API_KEY, self.entry_or_key),
            ]:
                val = entry.get().strip()
                dotenv.set_key(env_path, env_var, val)
                os.environ[env_var] = val
        except OSError as e:
            self.log(f"[Error] Failed to save .env: {e}\n")
            success = False

        try:
            self.paths.system_prompt_path.write_text(self.txt_prompt.get("0.0", "end").strip())
        except OSError as e:
            self.log(f"[Error] Failed to save system_prompt.txt: {e}\n")
            success = False

        try:
            self.paths.cold_outreach_prompt_path.write_text(self.txt_cold_prompt.get("0.0", "end").strip())
        except OSError as e:
            self.log(f"[Error] Failed to save cold_outreach_prompt.txt: {e}\n")
            success = False

        if success:
            self.log("[Info] All settings saved successfully.\n")
        return success

    def start_bot(self, cmd_arg: str) -> None:
        if self.is_running:
            return
        if not self.save_config():
            return

        self.is_running = True
        for btn in (self.btn_follow_up, self.btn_cold_outreach, self.btn_run_all):
            btn.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.log("\n" + "=" * 30 + "\nStarting Outlook Bot...\n" + "=" * 30 + "\n")

        threading.Thread(target=self._run_process, args=(cmd_arg,), daemon=True).start()

    def _run_process(self, cmd_arg: str) -> None:
        python = sys.executable
        try:
            self.bot_process = subprocess.Popen(
                [python, "-u", "-m", "outlook_bot.cli", f"--{cmd_arg}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )

            for line in self.bot_process.stdout:  # type: ignore[union-attr]
                text = line
                self.log_box.after(0, self._append_log, text)

            self.bot_process.wait()
        except Exception as e:
            self.log_box.after(0, self._append_log, f"\n[Error: {e}]\n")
        finally:
            self.bot_process = None
            self.after(0, self._process_finished)

    def _process_finished(self) -> None:
        self.is_running = False
        for btn in (self.btn_follow_up, self.btn_cold_outreach, self.btn_run_all):
            btn.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.log("\n[Process finished]\n")

    def _kill_bot_process(self) -> None:
        proc = self.bot_process
        if proc and proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
                    proc.kill()
        self.bot_process = None

    def stop_bot(self) -> None:
        self._kill_bot_process()
        if self.is_running:
            self.log("\n[Stopped]\n")
            self._process_finished()

    def refresh_models_list(self, use_initial_pref: bool = False) -> None:
        self.log("[Info] Detecting available models...\n")
        try:
            os.environ[ENV_GEMINI_API_KEY] = self.entry_api_key.get().strip()
            os.environ[ENV_OPENAI_API_KEY] = self.entry_openai_key.get().strip()
            os.environ[ENV_OPENROUTER_API_KEY] = self.entry_or_key.get().strip()

            registry = ProviderRegistry()
            models_data = [{"id": m.id, "provider": m.provider} for m in registry.available_models]
            self.available_models_data = models_data

            if not models_data:
                self.log("[Warning] No models detected.\n")
                self.combo_model.configure(values=["No models available"])
                self.combo_model.set("No models available")
                return

            self.log(f"[Info] Found {len(models_data)} models total.\n")

            pref = None
            if use_initial_pref and hasattr(self, "_initial_preferred_model"):
                pref = self._initial_preferred_model

            if pref:
                found = next((m for m in models_data if m["id"] == pref), None)
                if found:
                    provider_map = {"gemini": "Gemini", "openai": "OpenAI", "openrouter": "OpenRouter"}
                    self.combo_provider.set(provider_map.get(found["provider"], "All"))

            self._update_model_dropdown(preferred_model=pref)

        except Exception as e:
            self.log(f"[Error] Failed to detect models: {e}\n")

    def _on_provider_change(self, choice: str) -> None:
        self._update_model_dropdown()

    def _on_search_change(self, event=None) -> None:
        self._update_model_dropdown()

    def _update_model_dropdown(self, preferred_model: str | None = None) -> None:
        provider_filter = self.combo_provider.get()
        search_text = self.entry_search.get().lower().strip()

        filtered = []
        for m in self.available_models_data:
            p = m.get("provider", "").lower()
            mid = m.get("id", "")

            if provider_filter != "All" and provider_filter.lower() != p:
                continue
            if search_text and search_text not in mid.lower():
                continue
            filtered.append(mid)

        if not filtered:
            self.combo_model.configure(values=["No matching models"])
            self.combo_model.set("No matching models")
            return

        self.combo_model.configure(values=filtered)
        current = self.combo_model.get()

        if preferred_model and preferred_model in filtered:
            self.combo_model.set(preferred_model)
        elif current in filtered:
            self.combo_model.set(current)
        else:
            self.combo_model.set(filtered[0])

    def _test_connection(self, provider: str, key: str, button: ctk.CTkButton | Any) -> None:
        self.log(f"[Info] Testing {provider} connection...\n")
        button.configure(text="...", state="disabled")

        def _target() -> None:
            registry = ProviderRegistry.__new__(ProviderRegistry)
            registry.ssl_mode = "disabled"
            registry.providers = {}
            registry.available_models = []

            success, msg = registry.test_connection(provider.lower(), key)
            self.after(0, lambda: self._handle_test_result(button, success, msg))

        threading.Thread(target=_target, daemon=True).start()

    def test_gemini(self) -> None:
        self._test_connection("Gemini", self.entry_api_key.get().strip(), self.btn_test_gemini)

    def test_openai(self) -> None:
        self._test_connection("OpenAI", self.entry_openai_key.get().strip(), self.btn_test_openai)

    def test_or(self) -> None:
        self._test_connection("OpenRouter", self.entry_or_key.get().strip(), self.btn_test_or)

    def _handle_test_result(self, button: ctk.CTkButton, success: bool, message: str) -> None:
        button.configure(text="Test", state="normal")
        if success:
            button.configure(fg_color="green", hover_color="darkgreen")
            self.log(f"[Success] {message}\n")
        else:
            button.configure(fg_color="darkred", hover_color="#800000")
            self.log(f"[Error] {message}\n")

    def on_close(self) -> None:
        self._kill_bot_process()
        self.destroy()


def main() -> None:
    app = OutlookBotGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

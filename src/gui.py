import os
import sys
import threading

import customtkinter as ctk
from tkinter import filedialog
import dotenv
import yaml

import llm

# Import main script logic
import main
from config import CONFIG_PATH, DAYS_THRESHOLD, DEFAULT_REPLY, ENV_PATH, SYSTEM_PROMPT_PATH
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
        self.geometry("800x700")
        self.grid_columnconfigure(0, weight=1)
        # Row 0: Control Panel
        # Row 1: Tab View
        # Row 2: "Console Output" Label
        # Row 3: Log Box (needs to expand)
        self.grid_rowconfigure(3, weight=1)

        self.is_running = False

        # --- Top Control Panel ---
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        self.btn_start = ctk.CTkButton(
            self.control_frame, text="START BOT", command=self.start_bot, fg_color="green", hover_color="darkgreen"
        )
        self.btn_start.pack(side="left", padx=10, pady=10)

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

        # -- Tab: Configuration --
        self.setup_config_tab()

        # -- Tab: System Prompt --
        self.setup_prompt_tab()

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





        # Default Reply
        lbl_reply = ctk.CTkLabel(tab, text="Default Reply:")
        lbl_reply.grid(row=4, column=0, padx=10, pady=10, sticky="nw")
        self.txt_default_reply = ctk.CTkTextbox(tab, height=60)
        self.txt_default_reply.grid(row=4, column=1, padx=10, pady=10, sticky="ew", columnspan=2)

        # Model Provider Selection
        lbl_provider = ctk.CTkLabel(tab, text="Model Provider:")
        lbl_provider.grid(row=5, column=0, padx=10, pady=10, sticky="nw")
        self.combo_provider = ctk.CTkComboBox(tab, state="readonly", command=self.on_provider_change)
        self.combo_provider.grid(row=5, column=1, padx=10, pady=10, sticky="ew")
        self.combo_provider.set("All")
        self.combo_provider.configure(values=["All", "Gemini", "OpenAI", "OpenRouter"])
        
        # Search Entry
        self.entry_search = ctk.CTkEntry(tab, placeholder_text="Search models...")
        self.entry_search.grid(row=5, column=2, padx=10, pady=10, sticky="ew")
        self.entry_search.bind("<KeyRelease>", self.on_search_change)

        # Model Selection
        lbl_model = ctk.CTkLabel(tab, text="Preferred Model:")
        lbl_model.grid(row=6, column=0, padx=10, pady=10, sticky="nw")
        self.combo_model = ctk.CTkComboBox(tab, state="readonly", command=self.on_model_selected)
        self.combo_model.grid(row=6, column=1, padx=10, pady=10, sticky="ew")

        # Refresh Models Button
        self.btn_refresh_models = ctk.CTkButton(tab, text="Refresh Models", command=self.refresh_models_list)
        self.btn_refresh_models.grid(row=6, column=2, padx=10, pady=10, sticky="nw")
        
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

    def toggle_key_visibility(self):
        if self.chk_show_key.get():
            self.entry_api_key.configure(show="")
        else:
            self.entry_api_key.configure(show="*")

    def toggle_openai_visibility(self):
        if self.chk_show_openai.get():
            self.entry_openai_key.configure(show="")
        else:
            self.entry_openai_key.configure(show="*")

    def toggle_or_visibility(self):
        if self.chk_show_or.get():
            self.entry_or_key.configure(show="")
        else:
            self.entry_or_key.configure(show="*")

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





        # Default Reply
        self.txt_default_reply.delete("0.0", "end")
        self.txt_default_reply.insert("0.0", data.get("default_reply", DEFAULT_REPLY))

        # Models (Handled by refresh_models_list)
        # We don't load 'available_models' from yaml anymore as it's dynamic
        pass

        # 2. Load .env
        try:
            if os.path.exists(ENV_PATH):
                dotenv.load_dotenv(ENV_PATH, override=True)
                api_key = os.getenv("GEMINI_API_KEY", "")
                self.entry_api_key.delete(0, "end")
                self.entry_api_key.insert(0, api_key)

                openai_key = os.getenv("OPENAI_API_KEY", "")
                self.entry_openai_key.delete(0, "end")
                self.entry_openai_key.insert(0, openai_key)

                or_key = os.getenv("OPENROUTER_API_KEY", "")
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
            
            days = int(self.entry_days.get())
            default_reply = self.txt_default_reply.get("0.0", "end").strip()
            preferred_model = self.combo_model.get()
            
            # Update only the fields we manage, preserve others
            data = existing_data.copy()
            data.update({
                "days_threshold": days,
                "default_reply": default_reply,
                "preferred_model": preferred_model
            })
            # Note: disable_ssl_verify is now hardcoded in llm.py and not stored in config.yaml
            
            with open(CONFIG_PATH, "w") as f:
                yaml.dump(data, f)
        except ValueError:
            self.log("[Error] Invalid Days Threshold. Must be an integer.\n")
            success = False
        except (yaml.YAMLError, OSError) as e:
            self.log(f"[Error] Failed to save config.yaml: {e}\n")
            success = False

        # 2. Save .env
        try:
            new_key = self.entry_api_key.get().strip()

            # Use dotenv.set_key to preserve other vars if any
            dotenv.set_key(ENV_PATH, "GEMINI_API_KEY", new_key)
            os.environ["GEMINI_API_KEY"] = new_key

            new_openai_key = self.entry_openai_key.get().strip()
            dotenv.set_key(ENV_PATH, "OPENAI_API_KEY", new_openai_key)
            os.environ["OPENAI_API_KEY"] = new_openai_key

            new_or_key = self.entry_or_key.get().strip()
            dotenv.set_key(ENV_PATH, "OPENROUTER_API_KEY", new_or_key)
            os.environ["OPENROUTER_API_KEY"] = new_or_key
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

        if success:
            self.log("[Info] All settings saved successfully.\n")
        return success

    def start_bot(self):
        if self.is_running:
            return

        # Save before run
        # Wait, if we save, we might need to ensure the files exist for main.py to read?
        # main.py reads from config.py paths, which we also write to here.
        if not self.save_config():
            return

        self.is_running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.log("\n" + "=" * 30 + "\nStarting Outlook Bot...\n" + "=" * 30 + "\n")

        # Run in a separate thread to keep GUI responsive
        threading.Thread(target=self.run_process, daemon=True).start()

    def run_process(self):
        # Redirect stdout/stderr
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        sys.stdout = StdoutRedirector(self.log_box)
        sys.stderr = StdoutRedirector(self.log_box)

        try:
            # Execute the main script logic
            # main.main() does its work and returns.
            main.main()

        except Exception as e:
            print(f"\n[Error during execution: {e}]")
            import traceback

            traceback.print_exc()
        finally:
            # Restore stdout/stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr

            # Notify GUI of completion
            self.after(0, self.process_finished)

    def process_finished(self):
        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.log("\n[Process finished]\n")

    def stop_bot(self):
        # Since we are running in a thread, we can't easily "kill" it unless main.py checks a flag.
        # For now, we'll just log that we can't force stop safely without refactoring main.py logic to be interruptible.
        # But for packaging purposes, we can at least update the UI.
        if self.is_running:
            self.log("\n[Stop requested... waiting for current task to finish]\n")
            # In a real app we'd set a flag that main.py checks.
            # config.should_stop = True (if we implemented that)
            pass

    def refresh_models_list(self, use_initial_pref=False):
        self.log("[Info] Detecting available models...\n")
        try:
            # Explicitly set ENV from UI before detecting.
            os.environ["GEMINI_API_KEY"] = self.entry_api_key.get().strip()
            os.environ["OPENAI_API_KEY"] = self.entry_openai_key.get().strip()
            os.environ["OPENROUTER_API_KEY"] = self.entry_or_key.get().strip()

            service = llm.LLMService()
            # ACCESS RAW DATA instead of list strings, so we know provider
            models_data = service.available_models # list of {'id':..., 'provider':...}
            
            # Store full model data
            self.available_models_data = models_data # store list of dicts

            if not models_data:
                 self.log(f"[Warning] No models detected. Please check API keys.\n")
                 self.combo_model.configure(values=["No models available"])
                 self.combo_model.set("No models available")
                 return

            self.log(f"[Info] Found {len(models_data)} models total.\n")
            
            # Decide on preferred model
            pref = None
            if use_initial_pref and hasattr(self, '_initial_preferred_model'):
                pref = self._initial_preferred_model
            
            # Determine which provider contains this preferred model to set correct filter
            if pref:
                 # Find provider for this model
                 found_model = next((m for m in models_data if m["id"] == pref), None)
                 if found_model:
                     found_prov = found_model.get("provider", "").lower()
                     
                     # Map internal provider id to Dropdown display string
                     provider_map = {
                         "gemini": "Gemini", 
                         "openai": "OpenAI", 
                         "openrouter": "OpenRouter"
                     }
                     
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
        provider_filter = self.combo_provider.get() # "All", "Gemini", "OpenAI"
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
        if self.is_running:
            self.stop_bot()
        self.destroy()

    def test_gemini(self):
        key = self.entry_api_key.get().strip()
        self.log("[Info] Testing Gemini connection...\n")
        self.btn_test_gemini.configure(text="...", state="disabled")

        def _target():
            success, msg = llm.LLMService.test_gemini_connection(key)
            # Update UI on main thread
            self.after(0, lambda: self._handle_test_result(self.btn_test_gemini, success, msg))

        threading.Thread(target=_target, daemon=True).start()

    def test_openai(self):
        key = self.entry_openai_key.get().strip()
        self.log("[Info] Testing OpenAI connection...\n")
        self.btn_test_openai.configure(text="...", state="disabled")

        def _target():
            success, msg = llm.LLMService.test_openai_connection(key)
            # Update UI on main thread
            self.after(0, lambda: self._handle_test_result(self.btn_test_openai, success, msg))

        threading.Thread(target=_target, daemon=True).start()

    def test_or(self):
        key = self.entry_or_key.get().strip()
        self.log("[Info] Testing OpenRouter connection...\n")
        self.btn_test_or.configure(text="...", state="disabled")

        def _target():
            success, msg = llm.LLMService.test_openrouter_connection(key)
            self.after(0, lambda: self._handle_test_result(self.btn_test_or, success, msg))
        
        threading.Thread(target=_target, daemon=True).start()

    def _handle_test_result(self, button, success, message):
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

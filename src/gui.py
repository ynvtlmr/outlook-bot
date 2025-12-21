import customtkinter as ctk
import subprocess
import threading
import os
import sys
import yaml
import dotenv

# --- Configuration & Constants ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yaml')
ENV_PATH = os.path.join(BASE_DIR, '.env')
SYSTEM_PROMPT_PATH = os.path.join(BASE_DIR, 'system_prompt.txt')
MAIN_SCRIPT_PATH = os.path.join(BASE_DIR, 'src', 'main.py')

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

        self.process = None
        self.is_running = False

        # --- Top Control Panel ---
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        self.btn_start = ctk.CTkButton(self.control_frame, text="START BOT", command=self.start_bot, fg_color="green", hover_color="darkgreen")
        self.btn_start.pack(side="left", padx=10, pady=10)

        self.btn_stop = ctk.CTkButton(self.control_frame, text="STOP", command=self.stop_bot, fg_color="darkred", hover_color="#800000", state="disabled")
        self.btn_stop.pack(side="left", padx=10, pady=10)
        
        self.btn_save = ctk.CTkButton(self.control_frame, text="Save All Settings", command=self.save_config, fg_color="#1f538d") # Blueish
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
        self.entry_api_key = ctk.CTkEntry(tab, width=400, show="*") # Masked by default
        self.entry_api_key.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Toggle visibility
        self.chk_show_key = ctk.CTkCheckBox(tab, text="Show", command=self.toggle_key_visibility, width=60)
        self.chk_show_key.grid(row=0, column=2, padx=10, pady=10)

        # Days Threshold
        lbl_days = ctk.CTkLabel(tab, text="Days Threshold:")
        lbl_days.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_days = ctk.CTkEntry(tab, width=100)
        self.entry_days.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Default Reply
        lbl_reply = ctk.CTkLabel(tab, text="Default Reply:")
        lbl_reply.grid(row=2, column=0, padx=10, pady=10, sticky="nw")
        self.txt_default_reply = ctk.CTkTextbox(tab, height=60)
        self.txt_default_reply.grid(row=2, column=1, padx=10, pady=10, sticky="ew", columnspan=2)

        # Models
        lbl_models = ctk.CTkLabel(tab, text="Available Models\n(one per line):")
        lbl_models.grid(row=3, column=0, padx=10, pady=10, sticky="nw")
        self.txt_models = ctk.CTkTextbox(tab, height=100)
        self.txt_models.grid(row=3, column=1, padx=10, pady=10, sticky="ew", columnspan=2)

    def setup_prompt_tab(self):
        tab = self.tab_view.tab("System Prompt")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        self.txt_prompt = ctk.CTkTextbox(tab, wrap="word")
        self.txt_prompt.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    def toggle_key_visibility(self):
        if self.chk_show_key.get():
            self.entry_api_key.configure(show="")
        else:
            self.entry_api_key.configure(show="*")

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def load_all_configs(self):
        self.log("[Info] Loading configurations...\n")
        
        # 1. Load Config YAML
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    data = yaml.safe_load(f) or {}
                
                # Days
                self.entry_days.delete(0, "end")
                self.entry_days.insert(0, str(data.get('days_threshold', 5)))

                # Default Reply
                self.txt_default_reply.delete("0.0", "end")
                self.txt_default_reply.insert("0.0", data.get('default_reply', "Thank you for your email. I will review it and get back to you shortly."))

                # Models
                models = data.get('available_models', [])
                self.txt_models.delete("0.0", "end")
                self.txt_models.insert("0.0", "\n".join(models))
        except Exception as e:
            self.log(f"[Error] Failed to load config.yaml: {e}\n")

        # 2. Load .env
        try:
            if os.path.exists(ENV_PATH):
                dotenv.load_dotenv(ENV_PATH, override=True)
                api_key = os.getenv("GEMINI_API_KEY", "")
                self.entry_api_key.delete(0, "end")
                self.entry_api_key.insert(0, api_key)
        except Exception as e:
            self.log(f"[Error] Failed to load .env: {e}\n")

        # 3. Load System Prompt
        try:
            if os.path.exists(SYSTEM_PROMPT_PATH):
                with open(SYSTEM_PROMPT_PATH, 'r') as f:
                    content = f.read()
                self.txt_prompt.delete("0.0", "end")
                self.txt_prompt.insert("0.0", content)
        except Exception as e:
            self.log(f"[Error] Failed to load system_prompt.txt: {e}\n")

    def save_config(self):
        success = True
        
        # 1. Save YAML
        try:
            days = int(self.entry_days.get())
            default_reply = self.txt_default_reply.get("0.0", "end").strip()
            models_text = self.txt_models.get("0.0", "end").strip()
            models = [m.strip() for m in models_text.split('\n') if m.strip()]

            data = {
                'days_threshold': days,
                'default_reply': default_reply,
                'available_models': models
            }
            with open(CONFIG_PATH, 'w') as f:
                yaml.dump(data, f)
        except ValueError:
            self.log("[Error] Invalid Days Threshold. Must be an integer.\n")
            success = False
        except Exception as e:
            self.log(f"[Error] Failed to save config.yaml: {e}\n")
            success = False

        # 2. Save .env
        try:
            new_key = self.entry_api_key.get().strip()
            if not os.path.exists(ENV_PATH):
                 with open(ENV_PATH, 'w') as f: pass # Create if missing
            
            # Use dotenv.set_key to preserve other vars if any
            dotenv.set_key(ENV_PATH, "GEMINI_API_KEY", new_key)
            # Update current env in memory nicely
            os.environ["GEMINI_API_KEY"] = new_key
        except Exception as e:
            self.log(f"[Error] Failed to save .env: {e}\n")
            success = False

        # 3. Save System Prompt
        try:
            prompt_content = self.txt_prompt.get("0.0", "end").strip()
            with open(SYSTEM_PROMPT_PATH, 'w') as f:
                f.write(prompt_content)
        except Exception as e:
            self.log(f"[Error] Failed to save system_prompt.txt: {e}\n")
            success = False
            
        if success:
            self.log("[Info] All settings saved successfully.\n")
        return success

    def start_bot(self):
        if self.is_running:
            return
        
        # Save before run
        if not self.save_config():
            return

        self.is_running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.log("\n" + "="*30 + "\nStarting Outlook Bot...\n" + "="*30 + "\n")

        threading.Thread(target=self.run_process, daemon=True).start()

    def run_process(self):
        try:
            # We must load the environment variables from the file again 
            # or pass the current os.environ to the subprocess to ensure 
            # the new API key is picked up.
            # subprocess.Popen inherits os.environ by default.
            
            cmd = [sys.executable, "-u", MAIN_SCRIPT_PATH]
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=os.environ.copy() # Explicitly pass current env with new key
            )

            for line in self.process.stdout:
                self.after(0, self.log, line)

            self.process.wait()
            return_code = self.process.returncode
            self.after(0, self.log, f"\n[Process finished with exit code {return_code}]\n")

        except Exception as e:
            self.after(0, self.log, f"\n[Error running process: {e}]\n")
        finally:
            self.after(0, self.process_finished)

    def process_finished(self):
        self.is_running = False
        self.process = None
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def stop_bot(self):
        if self.process and self.is_running:
            self.log("\n[Stopping process...]\n")
            self.process.terminate()
    
    def on_close(self):
        if self.is_running:
            self.stop_bot()
        self.destroy()

if __name__ == "__main__":
    app = OutlookBotGUI()
    app.mainloop()

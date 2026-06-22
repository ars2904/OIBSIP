import tkinter as tk
from tkinter import messagebox, ttk
import threading
import queue
import time
import math
import os
import json

from src.voice import VoiceEngine
from src.nlu import NLUParser
from src.reminder import ReminderManager
from src.actions import (
    load_config, save_config, get_current_time_date,
    perform_web_search, get_weather, answer_general_qa,
    send_email, add_custom_command, execute_custom_command
)

class VoiceAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Nova Voice Assistant")
        self.root.geometry("850x650")
        self.root.configure(bg="#0f172a") # Slate 900
        
        # Make the window non-resizable or handle it gracefully
        self.root.resizable(True, True)
        
        # Configure grid expansion
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # Thread-safe queue for UI updates
        self.ui_queue = queue.Queue()
        
        # Initialize engines
        self.voice = VoiceEngine()
        self.nlu = NLUParser()
        self.reminder = ReminderManager(self.voice)
        
        # Thread controls
        self.listening_active = False
        self.pulse_phase = 0
        self.animation_running = False
        
        # Set up styles
        self.setup_styles()
        
        # Build UI layout
        self.build_ui()
        
        # Start queue processing
        self.process_queue()
        
        # Welcome message
        self.log_message("System", "Nova Assistant Ready. Click the microphone or type to begin.")
        self.voice.speak("Hello! I am Nova, your voice assistant. How can I help you today?")
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure Scrollbar colors
        style.configure("Vertical.TScrollbar", 
                        gripcount=0,
                        background="#334155", # Slate 700
                        troughcolor="#0f172a", 
                        bordercolor="#0f172a", 
                        arrowcolor="#94a3b8")
        
        # Notebook (tabs) styles
        style.configure("TNotebook", background="#1e293b", borderwidth=0)
        style.configure("TNotebook.Tab", 
                        background="#334155", 
                        foreground="#cbd5e1", 
                        font=("Segoe UI", 10, "bold"),
                        padding=[15, 5])
        style.map("TNotebook.Tab",
                  background=[("selected", "#4f46e5")], # Indigo 600
                  foreground=[("selected", "#ffffff")])
        
    def build_ui(self):
        # Create Main tab container
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Tab 1: Assistant Console
        self.tab_console = tk.Frame(self.notebook, bg="#1e293b") # Slate 800
        self.notebook.add(self.tab_console, text="Voice Assistant")
        
        # Tab 2: Custom Commands Manager
        self.tab_commands = tk.Frame(self.notebook, bg="#1e293b")
        self.notebook.add(self.tab_commands, text="Custom Commands")
        
        # Tab 3: Configuration Settings
        self.tab_settings = tk.Frame(self.notebook, bg="#1e293b")
        self.notebook.add(self.tab_settings, text="Configuration")
        
        # --- TAB 1: CONSOLE BUILD ---
        self.build_console_tab()
        
        # --- TAB 2: COMMANDS BUILD ---
        self.build_commands_tab()
        
        # --- TAB 3: SETTINGS BUILD ---
        self.build_settings_tab()
        
    def build_console_tab(self):
        self.tab_console.columnconfigure(0, weight=3)
        self.tab_console.columnconfigure(1, weight=2)
        self.tab_console.rowconfigure(0, weight=1)
        self.tab_console.rowconfigure(1, weight=0)
        
        # Left Panel: Conversation log & Type box
        left_panel = tk.Frame(self.tab_console, bg="#1e293b")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(0, weight=1)
        left_panel.rowconfigure(1, weight=0)
        
        # Chat log Text Box
        self.log_text = tk.Text(left_panel, bg="#0f172a", fg="#e2e8f0", 
                                font=("Consolas", 11), wrap="word", 
                                insertbackground="white", relief="flat", bd=10)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar for log
        scrollbar = ttk.Scrollbar(left_panel, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Tags for styled chat log
        self.log_text.tag_config("user", foreground="#60a5fa", font=("Segoe UI", 11, "bold")) # Light blue
        self.log_text.tag_config("assistant", foreground="#a78bfa", font=("Segoe UI", 11, "bold")) # Lavender
        self.log_text.tag_config("system", foreground="#94a3b8", font=("Segoe UI", 9, "italic")) # Gray
        self.log_text.tag_config("alert", foreground="#f87171", font=("Segoe UI", 11, "bold")) # Red
        self.log_text.config(state="disabled")
        
        # Text input fallback frame
        input_frame = tk.Frame(left_panel, bg="#1e293b")
        input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        input_frame.columnconfigure(0, weight=1)
        
        self.entry_box = tk.Entry(input_frame, bg="#334155", fg="#ffffff", 
                                  font=("Segoe UI", 12), relief="flat", bd=8, insertbackground="white")
        self.entry_box.grid(row=0, column=0, sticky="ew")
        self.entry_box.bind("<Return>", lambda e: self.send_text_command())
        
        btn_send = tk.Button(input_frame, text="Send", bg="#4f46e5", fg="#ffffff", 
                             font=("Segoe UI", 10, "bold"), relief="flat", padx=15, 
                             activebackground="#4338ca", activeforeground="#ffffff",
                             command=self.send_text_command)
        btn_send.grid(row=0, column=1, padx=(10, 0), sticky="ns")
        
        # Right Panel: Mic button, Status label, Active Reminders list
        right_panel = tk.Frame(self.tab_console, bg="#1e293b")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 15), pady=15)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=0)
        right_panel.rowconfigure(1, weight=0)
        right_panel.rowconfigure(2, weight=1)
        
        # Pulsing Soundwave Canvas
        self.anim_canvas = tk.Canvas(right_panel, width=180, height=180, bg="#1e293b", highlightthickness=0)
        self.anim_canvas.grid(row=0, column=0, pady=10)
        self.draw_pulse_mic(False)
        
        # Button: Listen
        self.btn_listen = tk.Button(right_panel, text="Press to Speak", bg="#4f46e5", fg="#ffffff", 
                                    font=("Segoe UI", 12, "bold"), relief="flat", padx=20, pady=10,
                                    activebackground="#4338ca", activeforeground="#ffffff",
                                    command=self.start_listening_flow)
        self.btn_listen.grid(row=1, column=0, pady=10, sticky="ew")
        
        # Status Label
        self.status_label = tk.Label(right_panel, text="Idle", bg="#1e293b", fg="#94a3b8", 
                                     font=("Segoe UI", 11, "italic"))
        self.status_label.grid(row=1, column=0, pady=(60, 5))
        
        # Reminders listbox label
        lbl_reminders = tk.Label(right_panel, text="Active Reminders", bg="#1e293b", fg="#e2e8f0", 
                                 font=("Segoe UI", 11, "bold"))
        lbl_reminders.grid(row=2, column=0, sticky="w", pady=(10, 5))
        
        # Reminders Frame
        reminders_frame = tk.Frame(right_panel, bg="#1e293b")
        reminders_frame.grid(row=3, column=0, sticky="nsew")
        reminders_frame.columnconfigure(0, weight=1)
        reminders_frame.rowconfigure(0, weight=1)
        
        self.reminders_list = tk.Listbox(reminders_frame, bg="#0f172a", fg="#cbd5e1", 
                                         font=("Segoe UI", 10), relief="flat", selectbackground="#4f46e5")
        self.reminders_list.grid(row=0, column=0, sticky="nsew")
        
        # Periodically refresh reminder list UI
        self.refresh_reminders_list()

    def build_commands_tab(self):
        self.tab_commands.columnconfigure(0, weight=1)
        self.tab_commands.rowconfigure(1, weight=1)
        
        # Top Header
        lbl_header = tk.Label(self.tab_commands, text="Manage Custom Voice Actions", 
                              bg="#1e293b", fg="#ffffff", font=("Segoe UI", 14, "bold"))
        lbl_header.grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        # Input Form
        form_frame = tk.Frame(self.tab_commands, bg="#334155", bd=10)
        form_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        form_frame.columnconfigure(1, weight=1)
        
        tk.Label(form_frame, text="Trigger Phrase:", bg="#334155", fg="#e2e8f0", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_trigger = tk.Entry(form_frame, bg="#1e293b", fg="#ffffff", font=("Segoe UI", 11), relief="flat")
        self.entry_trigger.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        tk.Label(form_frame, text="Command Type:", bg="#334155", fg="#e2e8f0", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.combo_type = ttk.Combobox(form_frame, values=["speak", "url"], state="readonly", font=("Segoe UI", 10))
        self.combo_type.set("speak")
        self.combo_type.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=5)
        
        tk.Label(form_frame, text="Response / Action:", bg="#334155", fg="#e2e8f0", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_value = tk.Entry(form_frame, bg="#1e293b", fg="#ffffff", font=("Segoe UI", 11), relief="flat")
        self.entry_value.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        btn_add = tk.Button(form_frame, text="Add Command", bg="#10b981", fg="#ffffff", 
                            font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=5,
                            activebackground="#059669", activeforeground="#ffffff",
                            command=self.save_custom_command_gui)
        btn_add.grid(row=3, column=1, sticky="e", pady=10)
        
        # Display Box of custom commands
        list_frame = tk.Frame(self.tab_commands, bg="#1e293b")
        list_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.custom_cmd_list = tk.Listbox(list_frame, bg="#0f172a", fg="#cbd5e1", 
                                          font=("Segoe UI", 11), relief="flat", selectbackground="#4f46e5")
        self.custom_cmd_list.grid(row=0, column=0, sticky="nsew")
        
        btn_del = tk.Button(list_frame, text="Delete Selected", bg="#ef4444", fg="#ffffff", 
                            font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=5,
                            activebackground="#dc2626", activeforeground="#ffffff",
                            command=self.delete_custom_command_gui)
        self.custom_cmd_list.grid(row=0, column=0, columnspan=2, sticky="nsew")
        btn_del.grid(row=1, column=1, sticky="e", pady=10)
        
        self.refresh_custom_commands_list()

    def build_settings_tab(self):
        self.tab_settings.columnconfigure(0, weight=1)
        
        # Header
        lbl_header = tk.Label(self.tab_settings, text="Assistant Settings", 
                              bg="#1e293b", fg="#ffffff", font=("Segoe UI", 14, "bold"))
        lbl_header.grid(row=0, column=0, sticky="w", padx=20, pady=15)
        
        # Settings Container
        settings_frame = tk.Frame(self.tab_settings, bg="#334155", bd=15)
        settings_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        settings_frame.columnconfigure(1, weight=1)
        
        # Default City
        tk.Label(settings_frame, text="Default City (Weather):", bg="#334155", fg="#e2e8f0", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_city = tk.Entry(settings_frame, bg="#1e293b", fg="#ffffff", font=("Segoe UI", 11), relief="flat")
        self.entry_city.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        # Weather API Key
        tk.Label(settings_frame, text="OpenWeatherMap API Key:", bg="#334155", fg="#e2e8f0", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.entry_weather_key = tk.Entry(settings_frame, bg="#1e293b", fg="#ffffff", font=("Segoe UI", 11), relief="flat")
        self.entry_weather_key.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        # SMTP email settings
        tk.Label(settings_frame, text="SMTP Host Server:", bg="#334155", fg="#e2e8f0", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_smtp_server = tk.Entry(settings_frame, bg="#1e293b", fg="#ffffff", font=("Segoe UI", 11), relief="flat")
        self.entry_smtp_server.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        tk.Label(settings_frame, text="SMTP Port:", bg="#334155", fg="#e2e8f0", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="w", pady=5)
        self.entry_smtp_port = tk.Entry(settings_frame, bg="#1e293b", fg="#ffffff", font=("Segoe UI", 11), relief="flat")
        self.entry_smtp_port.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=5)
        
        tk.Label(settings_frame, text="Sender Email:", bg="#334155", fg="#e2e8f0", font=("Segoe UI", 10, "bold")).grid(row=4, column=0, sticky="w", pady=5)
        self.entry_sender_email = tk.Entry(settings_frame, bg="#1e293b", fg="#ffffff", font=("Segoe UI", 11), relief="flat")
        self.entry_sender_email.grid(row=4, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        tk.Label(settings_frame, text="Sender SMTP Password (or App Password):", bg="#334155", fg="#e2e8f0", font=("Segoe UI", 10, "bold")).grid(row=5, column=0, sticky="w", pady=5)
        self.entry_sender_pass = tk.Entry(settings_frame, show="*", bg="#1e293b", fg="#ffffff", font=("Segoe UI", 11), relief="flat")
        self.entry_sender_pass.grid(row=5, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        btn_save_sets = tk.Button(settings_frame, text="Save Config Settings", bg="#4f46e5", fg="#ffffff", 
                                  font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=6,
                                  activebackground="#4338ca", activeforeground="#ffffff",
                                  command=self.save_settings_gui)
        btn_save_sets.grid(row=6, column=1, sticky="e", pady=10)
        
        # Load active config into fields
        self.load_settings_into_fields()

    # --- CANVAS PULSING GRAPHICS ---
    def draw_pulse_mic(self, listening=False):
        self.anim_canvas.delete("all")
        cx, cy = 90, 90
        
        if listening:
            # Listening state: Pulsing purple aura
            factor = (math.sin(self.pulse_phase) + 1.0) / 2.0  # value between 0 and 1
            radius_outer = 45 + (factor * 30)
            color_aura = f"#{int(79 + factor * 50):02x}{int(70 + factor * 30):02x}{int(229 + factor * 26):02x}" # Pulsing Indigo
            
            self.anim_canvas.create_oval(cx - radius_outer, cy - radius_outer, 
                                         cx + radius_outer, cy + radius_outer, 
                                         fill="", outline=color_aura, width=3)
            
            radius_inner = 40 + (factor * 10)
            self.anim_canvas.create_oval(cx - radius_inner, cy - radius_inner, 
                                         cx + radius_inner, cy + radius_inner, 
                                         fill="#4f46e5", outline="")
            
            # Draw microphone icon lines inside
            self.anim_canvas.create_rectangle(cx - 8, cy - 20, cx + 8, cy + 8, fill="#ffffff", outline="", rx=5, ry=5)
            self.anim_canvas.create_arc(cx - 15, cy - 8, cx + 15, cy + 12, start=180, extent=180, fill="", outline="#ffffff", width=3)
            self.anim_canvas.create_line(cx, cy + 12, cx, cy + 25, fill="#ffffff", width=3)
            
            self.pulse_phase += 0.15
            self.root.after(30, lambda: self.draw_pulse_mic(True))
        else:
            # Idle state: Solid gray/indigo circle
            self.anim_canvas.create_oval(cx - 45, cy - 45, cx + 45, cy + 45, fill="#334155", outline="")
            self.anim_canvas.create_rectangle(cx - 8, cy - 20, cx + 8, cy + 8, fill="#94a3b8", outline="")
            self.anim_canvas.create_arc(cx - 15, cy - 8, cx + 15, cy + 12, start=180, extent=180, fill="", outline="#94a3b8", width=3)
            self.anim_canvas.create_line(cx, cy + 12, cx, cy + 25, fill="#94a3b8", width=3)
            self.pulse_phase = 0

    # --- QUEUE & COMM HANDLING ---
    def queue_put(self, msg_type, text_or_data):
        self.ui_queue.put({"type": msg_type, "data": text_or_data})
        
    def process_queue(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                msg_type = msg.get("type")
                msg_data = msg.get("data")
                
                if msg_type == "status":
                    self.status_label.config(text=msg_data)
                elif msg_type == "log_user":
                    self.log_message("User", msg_data)
                elif msg_type == "log_assistant":
                    self.log_message("Assistant", msg_data)
                elif msg_type == "log_system":
                    self.log_message("System", msg_data)
                elif msg_type == "log_alert":
                    self.log_message("Alert", msg_data)
                elif msg_type == "animation":
                    if msg_data == "start":
                        if not self.animation_running:
                            self.animation_running = True
                            self.draw_pulse_mic(True)
                    elif msg_data == "stop":
                        self.animation_running = False
                        # redraw idle icon
                        self.draw_pulse_mic(False)
                elif msg_type == "refresh_reminders":
                    self.refresh_reminders_list()
                    
                self.ui_queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def log_message(self, sender, text):
        self.log_text.config(state="normal")
        if sender == "User":
            self.log_text.insert(tk.END, f"You: ", "user")
            self.log_text.insert(tk.END, f"{text}\n\n")
        elif sender == "Assistant":
            self.log_text.insert(tk.END, f"Nova: ", "assistant")
            self.log_text.insert(tk.END, f"{text}\n\n")
        elif sender == "System":
            self.log_text.insert(tk.END, f"[System] {text}\n\n", "system")
        elif sender == "Alert":
            self.log_text.insert(tk.END, f"[Reminder Alert] {text}\n\n", "alert")
            
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    # --- CONTROLLER FLOWS ---
    def send_text_command(self):
        cmd = self.entry_box.get().strip()
        if not cmd:
            return
            
        self.entry_box.delete(0, tk.END)
        self.log_message("User", cmd)
        
        # Run command processing in background thread
        threading.Thread(target=self.process_text_command_thread, args=(cmd,), daemon=True).start()

    def process_text_command_thread(self, query):
        self.queue_put("status", "Processing query...")
        self.handle_assistant_request(query)
        self.queue_put("status", "Idle")

    def start_listening_flow(self):
        if self.listening_active:
            return # Prevent overlapping listen loops
            
        self.listening_active = True
        self.btn_listen.config(state="disabled", text="Listening...")
        self.queue_put("animation", "start")
        
        def _listen_thread():
            try:
                # Capture voice
                self.queue_put("status", "Listening...")
                spoken_query = self.voice.listen(callback_status=lambda s: self.queue_put("status", s))
                
                if spoken_query is None:
                    # Speech error / silence / timeout
                    self.voice.speak("I didn't hear anything. Please try speaking again.")
                    self.queue_put("log_system", "No speech detected.")
                elif spoken_query == "":
                    # Not understood
                    self.voice.speak("I am sorry, I couldn't understand that. Could you please repeat?")
                    self.queue_put("log_system", "Audio could not be transcribed.")
                else:
                    # Successfully heard
                    self.queue_put("log_user", spoken_query)
                    self.handle_assistant_request(spoken_query)
            except Exception as e:
                print(f"Listen thread error: {e}")
            finally:
                self.listening_active = False
                self.btn_listen.config(state="normal", text="Press to Speak")
                self.queue_put("status", "Idle")
                self.queue_put("animation", "stop")

        threading.Thread(target=_listen_thread, daemon=True).start()

    def handle_assistant_request(self, query):
        # 1. Custom Command Exact Match First
        is_custom = execute_custom_command(query, self.voice)
        if is_custom:
            self.queue_put("log_assistant", f"Executed custom command for: '{query}'")
            return
            
        # 2. Parse request using NLU Parser
        parsed = self.nlu.parse_intent(query)
        intent = parsed["intent"]
        params = parsed["params"]
        
        # 3. Check for specific voice custom prompt "add custom command"
        if "add custom command" in query.lower():
            self.voice.speak_sync("Sure! Please type the trigger phrase in the pop up.")
            # Trigger pop up in main thread
            self.root.after(0, self.voice_guided_add_command)
            return

        # 4. Dispatch Intents
        if intent == "wake_word":
            reply = "Yes? I'm listening. How can I help you?"
            self.voice.speak(reply)
            self.queue_put("log_assistant", reply)
            
        elif intent == "chitchat":
            phrase = params.get("phrase", "")
            if "thank" in phrase:
                reply = "You're very welcome! Let me know if there's anything else I can do."
            elif phrase in ["no thank you", "no thanks", "nevermind", "cancel", "no", "nothing", "that's all", "thats all"]:
                reply = "Alright, no problem. I'll be here if you need me!"
            else:
                reply = "Okay! Let me know what you need."
            self.voice.speak(reply)
            self.queue_put("log_assistant", reply)
            
        elif intent == "greet":
            reply = "Hello! I am Nova, your personal desktop voice assistant. I can open web searches, tell time, alert you on reminders, fetch weather reports, send emails, or answer general knowledge questions. How can I help you today?"
            self.voice.speak(reply)
            self.queue_put("log_assistant", reply)
            
        elif intent == "time_date":
            reply = get_current_time_date()
            self.voice.speak(reply)
            self.queue_put("log_assistant", reply)
            
        elif intent == "web_search":
            q = params.get("query")
            reply = perform_web_search(q)
            self.voice.speak(reply)
            self.queue_put("log_assistant", reply)
            
        elif intent == "weather":
            city = params.get("city")
            reply = get_weather(city)
            self.voice.speak(reply)
            self.queue_put("log_assistant", reply)
            
        elif intent == "general_qa":
            q = params.get("query")
            reply = answer_general_qa(q)
            self.voice.speak(reply)
            self.queue_put("log_assistant", reply)
            
        elif intent == "send_email":
            rec = params.get("recipient")
            msg = params.get("message")
            if not msg:
                # Ask user for body
                self.voice.speak_sync(f"What should I say in the email to {rec}?")
                self.queue_put("status", "Listening for email body...")
                msg = self.voice.listen(callback_status=lambda s: self.queue_put("status", s))
                if not msg:
                    self.voice.speak("Email cancelled because no message body was heard.")
                    self.queue_put("log_system", "Email cancelled (empty body).")
                    return
                    
            reply = send_email(rec, msg)
            self.voice.speak(reply)
            self.queue_put("log_assistant", reply)
            
        elif intent == "set_reminder":
            act = params.get("action")
            dur = params.get("duration")
            unit = params.get("unit")
            
            # Map unit to seconds
            multiplier = 1
            if "minute" in unit:
                multiplier = 60
            elif "hour" in unit:
                multiplier = 3600
                
            total_seconds = dur * multiplier
            
            # Set reminder with callback to alert GUI
            def reminder_alert_callback(msg):
                self.queue_put("log_alert", msg)
                self.queue_put("refresh_reminders", None)
                self.voice.speak(msg)
                
            self.reminder.set_reminder(act, total_seconds, reminder_alert_callback)
            
            reply = f"I've scheduled a reminder for you to {act} in {dur} {unit}s."
            self.voice.speak(reply)
            self.queue_put("log_assistant", reply)
            self.queue_put("refresh_reminders", None)
            
        elif intent == "exit":
            self.voice.speak_sync("Goodbye! Have a wonderful day.")
            self.root.after(500, self.root.destroy)
            
        else:
            # General fallback QA Search
            reply = answer_general_qa(query)
            self.voice.speak(reply)
            self.queue_put("log_assistant", reply)

    def voice_guided_add_command(self):
        # Interactive prompt to add custom command
        trigger = tk.simpledialog.askstring("Voice Assistant Prompt", "Enter trigger phrase (e.g. 'open portal'):")
        if not trigger:
            self.voice.speak("Operation cancelled.")
            return
            
        val = tk.simpledialog.askstring("Voice Assistant Prompt", "Enter URL to open or text to speak:")
        if not val:
            self.voice.speak("Operation cancelled.")
            return
            
        cmd_type = "url" if val.startswith("http") else "speak"
        msg = add_custom_command(trigger, cmd_type, val)
        self.voice.speak(msg)
        self.log_message("System", msg)
        self.refresh_custom_commands_list()

    # --- REFRESH / SAVE VIEW HANDLERS ---
    def refresh_reminders_list(self):
        self.reminders_list.delete(0, tk.END)
        active = self.reminder.get_active_reminders()
        for r in active:
            time_left = int(r["expires_at"] - time.time())
            if time_left > 0:
                mins, secs = divmod(time_left, 60)
                self.reminders_list.insert(tk.END, f"#{r['id']}: {r['action']} ({mins:02d}m {secs:02d}s left)")
        
        # Periodic update of lists
        self.root.after(1000, self.refresh_reminders_list_timer)
        
    def refresh_reminders_list_timer(self):
        # Check active tab to avoid polling overhead when not in console
        if self.notebook.index("current") == 0:
            self.reminders_list.delete(0, tk.END)
            active = self.reminder.get_active_reminders()
            for r in active:
                time_left = int(r["expires_at"] - time.time())
                if time_left > 0:
                    mins, secs = divmod(time_left, 60)
                    self.reminders_list.insert(tk.END, f"#{r['id']}: {r['action']} ({mins:02d}m {secs:02d}s left)")
        self.root.after(1000, self.refresh_reminders_list_timer)

    def load_settings_into_fields(self):
        config = load_config()
        self.entry_city.delete(0, tk.END)
        self.entry_city.insert(0, config.get("default_city", "New Delhi"))
        
        self.entry_weather_key.delete(0, tk.END)
        self.entry_weather_key.insert(0, config.get("weather_api_key", ""))
        
        smtp = config.get("smtp", {})
        self.entry_smtp_server.delete(0, tk.END)
        self.entry_smtp_server.insert(0, smtp.get("server", "smtp.gmail.com"))
        
        self.entry_smtp_port.delete(0, tk.END)
        self.entry_smtp_port.insert(0, str(smtp.get("port", 587)))
        
        self.entry_sender_email.delete(0, tk.END)
        self.entry_sender_email.insert(0, smtp.get("sender_email", ""))
        
        self.entry_sender_pass.delete(0, tk.END)
        self.entry_sender_pass.insert(0, smtp.get("sender_password", ""))

    def save_settings_gui(self):
        config = load_config()
        config["default_city"] = self.entry_city.get().strip()
        config["weather_api_key"] = self.entry_weather_key.get().strip()
        
        try:
            port = int(self.entry_smtp_port.get().strip())
        except ValueError:
            port = 587
            
        config["smtp"] = {
            "server": self.entry_smtp_server.get().strip(),
            "port": port,
            "sender_email": self.entry_sender_email.get().strip(),
            "sender_password": self.entry_sender_pass.get().strip()
        }
        
        save_config(config)
        messagebox.showinfo("Success", "Configuration settings saved successfully!")
        self.log_message("System", "Configuration updated.")

    def refresh_custom_commands_list(self):
        self.custom_cmd_list.delete(0, tk.END)
        config = load_config()
        cmds = config.get("custom_commands", {})
        for trigger, info in cmds.items():
            self.custom_cmd_list.insert(tk.END, f"'{trigger}' -> [{info['type']}] {info['data']}")

    def save_custom_command_gui(self):
        trigger = self.entry_trigger.get().strip()
        cmd_type = self.combo_type.get()
        value = self.entry_value.get().strip()
        
        if not trigger or not value:
            messagebox.showwarning("Validation Error", "Please provide trigger phrase and value!")
            return
            
        add_custom_command(trigger, cmd_type, value)
        self.entry_trigger.delete(0, tk.END)
        self.entry_value.delete(0, tk.END)
        
        self.refresh_custom_commands_list()
        messagebox.showinfo("Success", f"Custom command '{trigger}' added successfully!")

    def delete_custom_command_gui(self):
        selection = self.custom_cmd_list.curselection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a custom command to delete!")
            return
            
        selected_text = self.custom_cmd_list.get(selection[0])
        # Parse trigger out from selection text
        # Format: 'trigger' -> [type] data
        parts = selected_text.split(" -> ")
        if len(parts) > 0:
            trigger = parts[0].strip("'")
            config = load_config()
            if "custom_commands" in config and trigger in config["custom_commands"]:
                del config["custom_commands"][trigger]
                save_config(config)
                self.refresh_custom_commands_list()
                messagebox.showinfo("Deleted", f"Deleted command '{trigger}'.")

import time
import threading
import winsound
import pythoncom
import pyttsx3

class ReminderManager:
    def __init__(self, voice_engine=None):
        self.voice_engine = voice_engine
        self.reminders = []
        self.lock = threading.Lock()

    def set_reminder(self, action, duration_secs, voice_engine_speak_func=None):
        """Schedules a reminder in a background thread."""
        reminder_info = {
            "id": len(self.reminders) + 1,
            "action": action,
            "duration": duration_secs,
            "expires_at": time.time() + duration_secs,
            "active": True
        }
        
        with self.lock:
            self.reminders.append(reminder_info)
            
        def _reminder_thread():
            time.sleep(duration_secs)
            
            # Check if reminder is still active (not deleted)
            if not reminder_info["active"]:
                return
                
            # Trigger Audible Alert
            # 1. Beeps using winsound
            try:
                for _ in range(3):
                    winsound.Beep(880, 400) # 880Hz beep for 400ms
                    time.sleep(0.1)
            except Exception as e:
                print(f"Winsound alert error: {e}")
                
            # 2. Speak the reminder message
            message = f"Attention: This is your reminder to {action}!"
            if voice_engine_speak_func:
                voice_engine_speak_func(message)
            elif self.voice_engine:
                self.voice_engine.speak(message)
            else:
                print(f"ALERT: {message}")
                
            # Set active status to False
            reminder_info["active"] = False

        t = threading.Thread(target=_reminder_thread, daemon=True)
        t.start()
        return reminder_info

    def get_active_reminders(self):
        with self.lock:
            # Clean up expired reminders
            now = time.time()
            self.reminders = [r for r in self.reminders if r["active"] and r["expires_at"] > now]
            return list(self.reminders)
            
    def cancel_reminder(self, reminder_id):
        with self.lock:
            for r in self.reminders:
                if r["id"] == reminder_id:
                    r["active"] = False
                    return True
        return False

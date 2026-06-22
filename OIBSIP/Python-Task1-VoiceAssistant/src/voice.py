import speech_recognition as sr
import pyttsx3
import pythoncom
import threading

class VoiceEngine:
    def __init__(self):
        # Initialize COM library for the current thread
        try:
            pythoncom.CoInitialize()
        except Exception:
            pass
            
        self.tts_lock = threading.Lock()
        
        # Test TTS initialization
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            # Select a female voice if available, else default
            for voice in voices:
                if "female" in voice.name.lower() or "zira" in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            engine.setProperty('rate', 180)
            engine.setProperty('volume', 1.0)
            self.has_tts = True
        except Exception as e:
            print(f"Warning: TTS initialization failed: {e}")
            self.has_tts = False
            
        # Initialize STT
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.mic = None
        
        try:
            self.mic = sr.Microphone()
        except Exception as e:
            print(f"Warning: Microphone initialization failed: {e}")

    def speak(self, text):
        """Speak the given text. Uses a lock to prevent concurrent speech requests."""
        if not self.has_tts:
            print(f"[Speech Disabled] Assistant: {text}")
            return
            
        def _speak_thread():
            with self.tts_lock:
                try:
                    pythoncom.CoInitialize()
                    engine = pyttsx3.init()
                    voices = engine.getProperty('voices')
                    for voice in voices:
                        if "female" in voice.name.lower() or "zira" in voice.name.lower():
                            engine.setProperty('voice', voice.id)
                            break
                    engine.setProperty('rate', 180)
                    engine.setProperty('volume', 1.0)
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    print(f"TTS Speech error: {e}")
                finally:
                    try:
                        pythoncom.CoUninitialize()
                    except Exception:
                        pass

        # Run TTS in a daemon thread so it doesn't block the GUI
        t = threading.Thread(target=_speak_thread, daemon=True)
        t.start()
        print(f"Assistant: {text}")

    def speak_sync(self, text):
        """Synchronously speak the text (blocks until speaking is done)."""
        if not self.has_tts:
            print(f"[Speech Disabled] Assistant: {text}")
            return
            
        with self.tts_lock:
            try:
                pythoncom.CoInitialize()
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                for voice in voices:
                    if "female" in voice.name.lower() or "zira" in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
                engine.setProperty('rate', 180)
                engine.setProperty('volume', 1.0)
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"TTS Synchronous Speech error: {e}")
            finally:
                try:
                    pythoncom.CoUninitialize()
                except Exception:
                    pass
        print(f"Assistant: {text}")

    def listen(self, callback_status=None):
        """Listens for user input from the microphone.
        Returns:
            str: Recognized text query, empty string if not understood, or None if errors/timeout occur.
        """
        if not self.mic:
            if callback_status:
                callback_status("Microphone not available")
            return None
            
        try:
            with self.mic as source:
                if callback_status:
                    callback_status("Adjusting background noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                
                if callback_status:
                    callback_status("Listening...")
                print("Listening...")
                
                audio = self.recognizer.listen(source, timeout=4, phrase_time_limit=7)
                
                if callback_status:
                    callback_status("Recognizing...")
                print("Recognizing...")
                
                query = self.recognizer.recognize_google(audio)
                print(f"User (Spoken): {query}")
                return query
        except sr.WaitTimeoutError:
            if callback_status:
                callback_status("Listen timeout")
            print("Listening timed out.")
            return None
        except sr.UnknownValueError:
            if callback_status:
                callback_status("Could not understand")
            print("Speech recognition could not understand audio.")
            return ""
        except sr.RequestError as e:
            if callback_status:
                callback_status("API error")
            print(f"Speech recognition service request error: {e}")
            return None
        except Exception as e:
            if callback_status:
                callback_status("Mic error")
            print(f"Mic capture error: {e}")
            return None

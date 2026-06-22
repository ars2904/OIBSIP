import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

# Ensure NLTK data is downloaded (with fallbacks if offline)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    try:
        nltk.download('punkt', quiet=True)
    except Exception:
        pass

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    try:
        nltk.download('stopwords', quiet=True)
    except Exception:
        pass

class NLUParser:
    def __init__(self):
        # List of stopwords fallback
        try:
            self.stop_words = set(stopwords.words('english'))
        except Exception:
            self.stop_words = {"is", "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "what", "how"}

        # Define intent patterns and keyword associations for fallbacks
        self.intents_templates = {
            "greet": [
                "hello", "hi", "hey", "greetings", "good morning", "good afternoon", "how are you", "who are you"
            ],
            "chitchat": [
                "thank you", "thanks", "no thank you", "no thanks", "nevermind", "cancel", "no", "that is all", "nothing", "okay", "ok"
            ],
            "wake_word": [
                "nova", "hey nova", "ok nova", "hi nova"
            ],
            "time_date": [
                "time", "date", "clock", "day today", "current time", "what day", "what is the date", "what time is it"
            ],
            "web_search": [
                "search the web", "search", "google", "web search", "look up", "find online", "search for"
            ],
            "send_email": [
                "email", "send an email", "send email", "mail"
            ],
            "set_reminder": [
                "remind", "reminder", "set a reminder", "alert me", "timer"
            ],
            "weather": [
                "weather", "temperature", "forecast", "climate", "how hot", "how cold", "rain"
            ],
            "general_qa": [
                "wikipedia", "what is", "who is", "who was", "define", "tell me about", "tell me what is"
            ],
            "exit": [
                "exit", "quit", "stop listening", "bye", "goodbye", "close"
            ]
        }

    def tokenize_and_clean(self, text):
        """Tokenize text and remove punctuation and stopwords."""
        text = text.lower()
        try:
            tokens = word_tokenize(text)
        except Exception:
            # Fallback to simple split if nltk word_tokenize fails
            tokens = re.findall(r'\b\w+\b', text)
            
        cleaned = [t for t in tokens if t not in string.punctuation and t not in self.stop_words]
        return cleaned if cleaned else tokens

    def parse_intent(self, text):
        """Parses the intent and parameters from the text.
        Returns:
            dict: { "intent": str, "confidence": float, "params": dict }
        """
        if not text:
            return {"intent": "unknown", "confidence": 0.0, "params": {}}
            
        text_lower = text.lower().strip()
        
        # CHECK WAKE WORD
        if text_lower in ["nova", "hey nova", "hello nova", "hi nova", "ok nova"]:
            return {
                "intent": "wake_word",
                "confidence": 1.0,
                "params": {}
            }
            
        # CHECK CHITCHAT
        if text_lower in ["thank you", "thanks", "no thank you", "no thanks", "nevermind", "cancel", "no", "nothing", "that's all", "thats all", "okay", "ok"]:
            return {
                "intent": "chitchat",
                "confidence": 1.0,
                "params": {"phrase": text_lower}
            }
            
        # 1. Exact custom commands matching check (done in main loop, but we handle keywords here too)
        
        # 2. Rule-based checks (high priority regex matching for parameter extraction)
        
        # CHECK EMAIL INTENT
        # Pattern: email [name] (saying/that) [message]
        email_match = re.search(r'\b(?:email|send email to|send an email to)\s+([a-zA-Z0-9]+)(?:\s+(?:saying|that|with|to)\s+(.*))?', text_lower)
        if email_match:
            recipient = email_match.group(1).strip()
            message = email_match.group(2).strip() if email_match.group(2) else ""
            # Clean common joining words from the start of the message
            message = re.sub(r'^(?:saying|that|message|is|body|with)\s+', '', message).strip()
            return {
                "intent": "send_email",
                "confidence": 0.95,
                "params": {"recipient": recipient, "message": message}
            }
            
        # CHECK REMINDER INTENT
        # Pattern: remind me to [action] in [duration] [seconds/minutes/hours]
        reminder_match = re.search(r'\bremind\s+me\s+to\s+(.*?)\s+in\s+(\d+)\s*(second|minute|hour)s?', text_lower)
        if reminder_match:
            action = reminder_match.group(1).strip()
            duration = int(reminder_match.group(2))
            unit = reminder_match.group(3)
            return {
                "intent": "set_reminder",
                "confidence": 0.95,
                "params": {"action": action, "duration": duration, "unit": unit}
            }
            
        # Alternative Reminder Pattern: set a reminder for [duration] [seconds/minutes/hours] to [action]
        reminder_match2 = re.search(r'\bset\s+(?:a\s+)?reminder\s+for\s+(\d+)\s*(second|minute|hour)s?\s+to\s+(.*)', text_lower)
        if reminder_match2:
            duration = int(reminder_match2.group(1))
            unit = reminder_match2.group(2)
            action = reminder_match2.group(3).strip()
            return {
                "intent": "set_reminder",
                "confidence": 0.95,
                "params": {"action": action, "duration": duration, "unit": unit}
            }

        # CHECK WEATHER INTENT
        # Pattern: weather in [city]
        weather_match = re.search(r'\bweather\s+(?:in|at|for)\s+([a-zA-Z\s]+)', text_lower)
        if weather_match:
            city = weather_match.group(1).strip()
            return {
                "intent": "weather",
                "confidence": 0.9,
                "params": {"city": city}
            }
            
        # CHECK WEB SEARCH INTENT
        # Pattern: search (for) [query], google [query]
        search_match = re.search(r'\b(?:search\s+for|search|google|lookup|look\s+up)\s+(.*)', text_lower)
        if search_match:
            query = search_match.group(1).strip()
            return {
                "intent": "web_search",
                "confidence": 0.85,
                "params": {"query": query}
            }
            
        # CHECK GENERAL QA INTENT
        # Pattern: who is/was [query], what is/was [query], tell me about [query]
        qa_match = re.search(r'\b(?:who\s+is|who\s+was|what\s+is|what\s+was|tell\s+me\s+about|define)\s+(.*)', text_lower)
        if qa_match:
            query = qa_match.group(1).strip()
            return {
                "intent": "general_qa",
                "confidence": 0.9,
                "params": {"query": query}
            }

        # 3. Bag-of-Words Jaccard Similarity matching for intent classification fallback
        cleaned_text = self.tokenize_and_clean(text_lower)
        best_intent = "unknown"
        best_score = 0.0
        
        for intent, templates in self.intents_templates.items():
            for template in templates:
                cleaned_template = self.tokenize_and_clean(template)
                # Compute Jaccard Similarity
                intersection = len(set(cleaned_text).intersection(set(cleaned_template)))
                union = len(set(cleaned_text).union(set(cleaned_template)))
                score = intersection / union if union > 0 else 0.0
                
                # Check for direct keyword overlap bonus
                keyword_match_count = sum(1 for word in cleaned_template if word in cleaned_text)
                keyword_score = keyword_match_count / len(cleaned_template) if len(cleaned_template) > 0 else 0.0
                
                final_score = max(score, keyword_score * 0.7)
                if final_score > best_score:
                    best_score = final_score
                    best_intent = intent

        # If score is too low, we flag as unknown
        if best_score < 0.25:
            # Let's try simple keyword checks as a absolute fallback
            if any(k in text_lower for k in ["hello", "hi", "hey"]):
                best_intent = "greet"
                best_score = 0.5
            elif any(k in text_lower for k in ["time", "date", "today"]):
                best_intent = "time_date"
                best_score = 0.5
            elif any(k in text_lower for k in ["quit", "exit", "bye"]):
                best_intent = "exit"
                best_score = 0.5
            else:
                best_intent = "unknown"
                best_score = 0.0

        # Fill default parameters based on predicted intent if not extracted by rules
        params = {}
        if best_intent == "web_search":
            # Strip intent verbs to find the query
            query = text_lower
            for phrase in self.intents_templates["web_search"]:
                query = query.replace(phrase, "")
            params["query"] = query.strip()
        elif best_intent == "weather":
            # Extract potential city, default to None (actions will check config or ask IP location)
            params["city"] = None
        elif best_intent == "general_qa":
            query = text_lower
            for phrase in ["wikipedia", "who is", "who was", "what is", "define", "tell me about"]:
                query = query.replace(phrase, "")
            params["query"] = query.strip()

        return {
            "intent": best_intent,
            "confidence": best_score,
            "params": params
        }

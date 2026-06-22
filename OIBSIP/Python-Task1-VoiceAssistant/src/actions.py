import datetime
import webbrowser
import requests
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.parse

# Path to the config file
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading config: {e}")
    return {}

def save_config(config):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

def get_current_time_date():
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%A, %B %d, %Y")
    return f"Today is {date_str}, and the current time is {time_str}."

def perform_web_search(query):
    if not query:
        return "What would you like me to search for?"
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    webbrowser.open(url)
    return f"Searching the web for {query}."

def get_weather(city=None):
    config = load_config()
    
    # Use default city if not specified
    if not city:
        city = config.get("default_city", "New York")
        
    # Check if OpenWeatherMap key is available
    owm_key = config.get("weather_api_key", "").strip()
    
    if owm_key:
        # Query OpenWeatherMap
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={urllib.parse.quote(city)}&appid={owm_key}&units=metric"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                temp = data["main"]["temp"]
                desc = data["weather"][0]["description"]
                humidity = data["main"]["humidity"]
                return f"The current weather in {city} is {temp}°C with {desc} and {humidity}% humidity."
            elif res.status_code == 401:
                return "Invalid weather API key in config.json. Falling back to free forecast API."
        except Exception as e:
            print(f"OpenWeatherMap error: {e}")
            
    # Fallback to Open-Meteo (completely free, no API key required)
    try:
        # Step 1: Geocoding (City -> Lat/Lon)
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=en&format=json"
        geo_res = requests.get(geocode_url, timeout=5)
        if geo_res.status_code == 200:
            geo_data = geo_res.json()
            if "results" in geo_data and len(geo_data["results"]) > 0:
                result = geo_data["results"][0]
                lat = result["latitude"]
                lon = result["longitude"]
                country = result.get("country", "")
                resolved_name = f"{result['name']}, {country}" if country else result['name']
                
                # Step 2: Forecast data
                forecast_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                f_res = requests.get(forecast_url, timeout=5)
                if f_res.status_code == 200:
                    f_data = f_res.json()
                    temp = f_data["current_weather"]["temperature"]
                    windspeed = f_data["current_weather"]["windspeed"]
                    weathercode = f_data["current_weather"]["weathercode"]
                    
                    # Map weather codes to simple descriptions
                    weather_codes = {
                        0: "clear sky",
                        1: "mainly clear", 2: "partly cloudy", 3: "overcast",
                        45: "fog", 48: "depositing rime fog",
                        51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
                        61: "slight rain", 63: "moderate rain", 65: "heavy rain",
                        71: "slight snow fall", 73: "moderate snow fall", 75: "heavy snow fall",
                        77: "snow grains",
                        80: "slight rain showers", 81: "moderate rain showers", 82: "violent rain showers",
                        85: "slight snow showers", 86: "heavy snow showers",
                        95: "thunderstorm", 96: "thunderstorm with slight hail", 99: "thunderstorm with heavy hail"
                    }
                    desc = weather_codes.get(weathercode, "unknown conditions")
                    return f"The current weather in {resolved_name} is {temp}°C with {desc}. Wind speed is {windspeed} kilometers per hour."
            return f"I couldn't find weather coordinates for the city: {city}."
    except Exception as e:
        print(f"Open-Meteo error: {e}")
        
    return f"Sorry, I am unable to retrieve the weather details for {city} right now. Please check your internet connection."

def answer_general_qa(query):
    if not query:
        return "What is your question?"
        
    # Step 1: Query DuckDuckGo Instant Answer API (Free, simple, fast)
    try:
        ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
        res = requests.get(ddg_url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            abstract = data.get("AbstractText", "")
            if abstract:
                # Truncate to first two sentences for brief speech readout
                sentences = abstract.split(". ")
                return ". ".join(sentences[:2]) + "."
    except Exception as e:
        print(f"DuckDuckGo QA error: {e}")
        
    # Step 2: Fallback to Wikipedia SEARCH API to resolve actual titles (highly robust)
    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json"
        search_res = requests.get(search_url, timeout=5)
        if search_res.status_code == 200:
            search_data = search_res.json()
            search_results = search_data.get("query", {}).get("search", [])
            if search_results:
                best_title = search_results[0]["title"]
                
                # Step 3: Fetch Wikipedia extract for resolved title
                wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts&exintro=1&explaintext=1&titles={urllib.parse.quote(best_title)}&redirects=1"
                res = requests.get(wiki_url, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    pages = data.get("query", {}).get("pages", {})
                    for page_id, page in pages.items():
                        if page_id != "-1":
                            extract = page.get("extract", "")
                            if extract:
                                sentences = extract.split(". ")
                                return ". ".join(sentences[:2]) + "."
    except Exception as e:
        print(f"Wikipedia QA error: {e}")
        
    return None

def send_email(recipient, message):
    config = load_config()
    smtp_settings = config.get("smtp", {})
    contacts = config.get("contacts", {})
    
    sender_email = smtp_settings.get("sender_email", "")
    sender_password = smtp_settings.get("sender_password", "")
    smtp_server = smtp_settings.get("server", "smtp.gmail.com")
    smtp_port = smtp_settings.get("port", 587)
    
    if not sender_email or not sender_password:
        return "Email is not configured in your config.json. Please add your credentials."
        
    # Resolve recipient to email address
    recipient_email = contacts.get(recipient.lower(), recipient)
    
    # Check if recipient_email is valid format (contains '@')
    if "@" not in recipient_email:
        return f"I don't have an email address saved for {recipient}. Please specify their full email address."
        
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "Voice Assistant Outbound Mail"
        
        body = f"Hello,\n\nThis is an email sent via Voice Assistant.\n\nMessage:\n{message}\n\nBest regards,\nYour Voice Assistant"
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return f"Email successfully sent to {recipient}."
    except Exception as e:
        print(f"SMTP error: {e}")
        return f"Failed to send email. Error: {str(e)}"

def add_custom_command(trigger, command_type, value):
    config = load_config()
    if "custom_commands" not in config:
        config["custom_commands"] = {}
        
    config["custom_commands"][trigger.lower().strip()] = {
        "type": command_type,
        "data": value
    }
    save_config(config)
    return f"Successfully added custom command: '{trigger}'."

def execute_custom_command(trigger, voice_engine):
    config = load_config()
    custom_commands = config.get("custom_commands", {})
    
    cmd = custom_commands.get(trigger.lower().strip())
    if not cmd:
        return False
        
    cmd_type = cmd.get("type")
    data = cmd.get("data")
    
    if cmd_type == "url":
        webbrowser.open(data)
        voice_engine.speak(f"Opening link for {trigger}.")
        return True
    elif cmd_type == "speak":
        voice_engine.speak(data)
        return True
    elif cmd_type == "sys":
        try:
            os.system(data)
            voice_engine.speak(f"Running system command.")
            return True
        except Exception as e:
            voice_engine.speak("Failed to execute system command.")
            return True
            
    return False

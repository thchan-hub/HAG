import os
import time
import datetime
import requests
from bs4 import BeautifulSoup

TARGET_GYM = "Hougang ActiveSG Gym"
URL = "https://activesg.gov.sg"

# Configurations: Safely reads your secret API key from the GitHub cloud environment
THINGSPEAK_WRITE_KEY = os.environ.get("THINGSPEAK_WRITE_KEY")

def push_to_thingspeak(value):
    """Sends the numeric capacity percentage directly to your ThingSpeak channel."""
    url = "https://thingspeak.com"
    payload = {
        'api_key': THINGSPEAK_WRITE_KEY,
        'field1': value
    }
    
    try:
        print(f"[{datetime.datetime.now()}] Sending {value}% capacity to ThingSpeak...")
        response = requests.get(url, params=payload, timeout=10)
        
        if response.status_code == 200 and response.text != "0":
            print(f"Successfully updated ThingSpeak! Entry ID: {response.text}")
        elif response.text == "0":
            print("ThingSpeak rejected the update. Double-check your API key or ensure a 15+ second gap.")
        else:
            print(f"Failed to connect to ThingSpeak. Status code: {response.status_code}")
    except Exception as e:
        print(f"Network error updating ThingSpeak: {str(e)}")

def log_capacity():
    current_hour = datetime.datetime.now().hour
    # Skip tracking loops if the facility is closed overnight (10:00 PM to 7:00 AM)
    if current_hour < 7 or current_hour >= 22:
        print(f"[{datetime.datetime.now()}] Facility is currently closed. Skipping data run.")
        return

    # Using native browser headers to access the web endpoint source securely
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }

    try:
        print("Connecting directly to data endpoint source...")
        response = requests.get(URL, headers=headers, timeout=20)
        
        if response.status_code == 403:
            print("Direct IP request blocked by data center rule. Attempting fallback text parsing...")
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Scrape all readable components containing text structures matching our location target
        elements = soup.find_all(text=lambda text: text and "Hougang" in text)
        
        capacity_num = None
        capacity_str = "N/A"
        
        if not elements:
            print("No visible card tags found in root structure. Injecting direct backend payload match...")
            # Fallback block parsing to scan embedded script data values if elements are compressed
            script_data = soup.find_all("script")
            for script in script_data:
                if script.string and "Hougang" in script.string:
                    match = re.search(r'Hougang ActiveSG Gym.*?(\d{1,3})%', script.string)
                    if match:
                        capacity_num = int(match.group(1))
                        capacity_str = f"{capacity_num}%"
                        break

        for element in elements:
            parent = element.find_parent(["li", "div", "p"])
            if parent:
                text_content = parent.get_text(separator=" ").strip()
                if "Closed" in text_content:
                    capacity_num = 0
                    capacity_str = "0% (Closed)"
                    break
                
                digits = [int(s) for s in text_content.replace('%', ' ').split() if s.isdigit()]
                if digits:
                    capacity_num = digits[0]
                    capacity_str = f"{capacity_num}%"
                    break

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp},{capacity_str}\n"
        
        # Append rows natively into the local spreadsheet output log file
        file_exists = os.path.isfile("gym_data.csv")
        with open("gym_data.csv", "a") as csv_file:
            if not file_exists:
                csv_file.write("Timestamp,Capacity\n")
            csv_file.write(log_entry)
            
        print(f"Logged locally: {timestamp} -> {TARGET_GYM}: {capacity_str}")
        
        # Trigger the ThingSpeak upload if a valid number was successfully parsed
        if capacity_num is not None:
            push_to_thingspeak(capacity_num)
        else:
            print("Could not extract a valid numeric percentage to send to ThingSpeak.")
            
    except Exception as e:
        print(f"API logging transaction error: {str(e)}")

if __name__ == "__main__":
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"🚀 ActiveSG Data Processor engaged via GitHub Cloud for {TARGET_GYM}...")
        log_capacity()

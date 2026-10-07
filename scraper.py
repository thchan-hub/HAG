import time
import datetime
import os
import re
import requests  # Added for handling the ThingSpeak API calls
from playwright.sync_api import sync_playwright

TARGET_GYM = "Hougang ActiveSG Gym"
URL = "https://activesg.gov.sg"

# 💡 Configurations: Safely reads your secret API key from the GitHub cloud environment
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

    # Launch automated background browser environment
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            # Navigate to the page and wait for full client-side React hydration to complete
            page.goto(URL, timeout=30000)
            page.wait_for_timeout(5000) # Give it 5 seconds to load text parameters fully
            
            # Extract the raw rendered text content from the browser viewport
            body_text = page.locator("body").inner_text()
            browser.close()
            
            # Clean and compress the text array lines
            clean_text = ' '.join(body_text.split())
            
            # Match pattern searching for: "Hougang ActiveSG Gym [any text] XX%"
            pattern = re.compile(rf"{re.escape(TARGET_GYM)}[\s\S]*?(\d{{1,3}})\s*%", re.IGNORECASE)
            match = pattern.search(clean_text)
            
            capacity_num = None
            capacity_str = "N/A"
            
            if match:
                capacity_num = int(match.group(1))
                capacity_str = f"{capacity_num}%"
            else:
                # Broad fallback sweep if naming format orders shuffle sequences
                fallback_match = re.search(r"Hougang[\s\S]{1,100}?(\d{1,3})\s*%", clean_text, re.IGNORECASE)
                if fallback_match:
                    capacity_num = int(fallback_match.group(1))
                    capacity_str = f"{capacity_num}%"

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp},{capacity_str}\n"
            
            # Append rows natively into the local spreadsheet output log file
            file_exists = os.path.isfile("gym_data.csv")
            with open("gym_data.csv", "a") as csv_file:
                if not file_exists:
                    csv_file.write("Timestamp,Capacity\n")
                csv_file.write(log_entry)
                
            print(f"Logged locally: {timestamp} -> {TARGET_GYM}: {capacity_str}")
            
            # 💡 Trigger the ThingSpeak upload if a valid number was successfully parsed
            if capacity_num is not None:
                push_to_thingspeak(capacity_num)
            else:
                print("Could not extract a valid numeric percentage to send to ThingSpeak.")
            
        except Exception as e:
            print(f"Automated browser event error: {str(e)}")

# 💡 Note for Cloud Execution:
# When running on GitHub Actions, the workflow system runs the script file once per cron cycle.
# The "while True" infinite loop structure is bypassed in the cloud to avoid dragging system resources.
if __name__ == "__main__":
    # If running in GitHub Actions cloud, run once and finish.
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"🚀 ActiveSG Browser Tracker triggered via GitHub Cloud for {TARGET_GYM}...")
        log_capacity()
    else:
        # Loop backup execution layout if you decide to test run it locally on your computer instead
        print(f"🚀 ActiveSG Local Continuous Loop Tracker engaged for {TARGET_GYM}...")
        while True:
            log_capacity()
            time.sleep(10 * 60) # Runs every 10 minutes locally

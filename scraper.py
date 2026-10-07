import time
import datetime
import os
import re
import requests
from playwright.sync_api import sync_playwright

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

    # Launch automated background browser environment
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            # Navigate to the page and wait for full hydration to complete
            page.goto(URL, timeout=30000)
            page.wait_for_timeout(7000) # Increased to 7 seconds to let heavy text load completely
            
            # Extract the raw rendered text content from the browser viewport
            body_text = page.locator("body").inner_text()
            browser.close()
            
            # 💡 DEBUG: Split text into clean lines to inspect in the GitHub Action logs
            lines = [line.strip() for line in body_text.split('\n') if line.strip()]
            print("--- BEGIN PAGE SNAPSHOT LOG ---")
            for idx, line in enumerate(lines[:100]): # Print the first 100 loaded text fragments
                print(f"[{idx}] {line}")
            print("--- END PAGE SNAPSHOT LOG ---")
            
            capacity_num = None
            capacity_str = "N/A"
            
            # 💡 Iterative Matching Logic: Locate the gym name line and search adjacent rows
            for i, line in enumerate(lines):
                if "Hougang" in line and "Gym" in line:
                    print(f"Target found at line block [{i}]: {line}")
                    
                    # Look at this line and the next 2 lines down for the percentage indicator
                    for search_idx in range(i, min(i + 3, len(lines))):
                        check_text = lines[search_idx]
                        if "%" in check_text:
                            digits = [int(s) for s in check_text.replace('%', ' ').split() if s.isdigit()]
                            if digits:
                                capacity_num = digits[0]
                                capacity_str = f"{capacity_num}%"
                                break
                        elif "Closed" in check_text:
                            capacity_num = 0
                            capacity_str = "0% (Closed)"
                            break
                    if capacity_num is not None:
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
            print(f"Automated browser event error: {str(e)}")

if __name__ == "__main__":
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"🚀 ActiveSG Browser Tracker triggered via GitHub Cloud for {TARGET_GYM}...")
        log_capacity()

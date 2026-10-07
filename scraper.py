import os
import requests
from bs4 import BeautifulSoup

# --- Configurations ---
THINGSPEAK_WRITE_KEY = os.environ.get("THINGSPEAK_WRITE_KEY")
ACTIVESG_URL = "https://activesg.gov.sg"
FACILITY_NAME = "Hougang ActiveSG Gym"

def get_hougang_capacity():
    # Disguise the script as a normal browser header
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        print("Fetching data from ActiveSG...")
        response = requests.get(ACTIVESG_URL, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"Failed to fetch page. HTTP Status: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Search the raw page elements for the facility text string
        elements = soup.find_all(text=lambda text: text and FACILITY_NAME in text)
        
        for element in elements:
            # Navigate to the nearest container parent holding the capacity values
            parent = element.find_parent(["li", "div"])
            if parent:
                text_content = parent.get_text(separator=" ").strip()
                print(f"Match Found! Raw Data:\n{text_content}")
                
                if "Closed" in text_content:
                    return 0
                    
                # Look for the percentage number string
                for word in text_content.replace('%', ' ').split():
                    if word.isdigit():
                        return int(word)
                        
        print(f"Could not find data for {FACILITY_NAME}")
        return None
        
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def push_to_thingspeak(value):
    url = "https://thingspeak.com"
    payload = {
        'api_key': THINGSPEAK_WRITE_KEY,
        'field1': value
    }
    
    print(f"Sending {value}% payload to ThingSpeak...")
    response = requests.get(url, params=payload)
    
    if response.status_code == 200 and response.text != "0":
        print(f"Successfully sent to ThingSpeak! Entry ID: {response.text}")
    elif response.text == "0":
        print("ThingSpeak rejected the update. Check your API key or wait 15 seconds.")
    else:
        print(f"Failed to send data. Status code: {response.status_code}")

if __name__ == "__main__":
    if not THINGSPEAK_WRITE_KEY or THINGSPEAK_WRITE_KEY == "YOUR_THINGSPEAK_WRITE_API_KEY":
        print("Error: THINGSPEAK_WRITE_KEY secret is not set in GitHub Settings.")
    else:
        capacity = get_hougang_capacity()
        if capacity is not None:
            push_to_thingspeak(capacity)

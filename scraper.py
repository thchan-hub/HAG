import os
import cloudscraper
from bs4 import BeautifulSoup

# --- Configurations ---
THINGSPEAK_WRITE_KEY = os.environ.get("THINGSPEAK_WRITE_KEY")
ACTIVESG_URL = "https://activesg.gov.sg/gym-pool-crowd"
FACILITY_NAME = "Hougang ActiveSG Gym"

def get_hougang_capacity():
    try:
        print("Initializing anti-bot session...")
        # Create a scraper instance that mimics a real desktop browser engine
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        print("Fetching data from ActiveSG...")
        response = scraper.get(ACTIVESG_URL, timeout=30)
        
        if response.status_code != 200:
            print(f"Failed to fetch page. HTTP Status: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Look for the container element that holds our facility text
        elements = soup.find_all(text=lambda text: text and FACILITY_NAME in text)
        
        for element in elements:
            parent = element.find_parent(["li", "div"])
            if parent:
                text_content = parent.get_text(separator=" ").strip()
                print(f"Match Found! Raw Data:\n{text_content}")
                
                if "Closed" in text_content:
                    return 0
                    
                # Isolate the digits directly next to the percent sign
                for word in text_content.replace('%', ' ').split():
                    if word.isdigit():
                        return int(word)
                        
        print(f"Could not find exact text match data for {FACILITY_NAME}")
        return None
        
    except Exception as e:
        print(f"Cloudflare bypass failed or timed out: {e}")
        return None

def push_to_thingspeak(value):
    # Re-initialized clean requests session to hit ThingSpeak API
    import requests
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
        print("ThingSpeak rejected the update. Check your API key parameters.")
    else:
        print(f"Failed to send data. Status code: {response.status_code}")

if __name__ == "__main__":
    if not THINGSPEAK_WRITE_KEY or THINGSPEAK_WRITE_KEY == "YOUR_THINGSPEAK_WRITE_API_KEY":
        print("Error: THINGSPEAK_WRITE_KEY secret is missing or not set in GitHub Settings.")
    else:
        capacity = get_hougang_capacity()
        if capacity is not None:
            push_to_thingspeak(capacity)

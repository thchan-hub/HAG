import os
THINGSPEAK_WRITE_KEY = os.environ.get("THINGSPEAK_WRITE_KEY")
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# --- Configurations ---
THINGSPEAK_WRITE_KEY = "YOUR_THINGSPEAK_WRITE_API_KEY"
ACTIVESG_URL = "https://activesg.gov.sg/gym-pool-crowd"
FACILITY_NAME = "Hougang ActiveSG Gym"

def get_hougang_capacity():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(ACTIVESG_URL)
        time.sleep(7)  # Increased slightly to give the elements ample time to populate
        
        # Pull all list items on the page directly
        elements = driver.find_elements(By.TAG_NAME, "li")
        
        for element in elements:
            text_content = element.text.strip()
            
            # Look for our facility name in the text string
            if FACILITY_NAME in text_content:
                print(f"Match Found! Raw Data: {text_content}")
                
                if "Closed" in text_content:
                    return 0
                
                # Extracts the number sequence before the % sign (e.g., "72% full" -> 72)
                numbers = [int(s) for s in text_content.replace('%', ' ').split() if s.isdigit()]
                if numbers:
                    return numbers[0]
                    
        print(f"Could not find a list item containing: {FACILITY_NAME}")
        return None
        
    except Exception as e:
        print(f"Error scraping data: {e}")
        return None
    finally:
        driver.quit()

def push_to_thingspeak(value):
    url = f"https://thingspeak.com{THINGSPEAK_WRITE_KEY}&field1={value}"
    response = requests.get(url)
    if response.status_code == 200:
        print(f"Successfully sent {value}% capacity to ThingSpeak!")
    else:
        print("Failed to send data to ThingSpeak.")

if __name__ == "__main__":
    capacity = get_hougang_capacity()
    if capacity is not None:
        push_to_thingspeak(capacity)

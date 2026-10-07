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
    # Set up headless browser parameters
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Modern headless flag
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(ACTIVESG_URL)
        time.sleep(5)  # Let dynamic Javascript load the capacities
        
        # Locate the specific list item for Hougang Gym
        # ActiveSG lists facilities usually inside list elements containing the name and percentage
        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{FACILITY_NAME}')]/ancestor::li")
        
        if elements:
            text_content = elements[0].text
            # Expected text format looks like: "Hougang ActiveSG Gym\n35% full" or "Closed"
            print(f"Raw Scraped Data: {text_content}")
            
            if "Closed" in text_content:
                return 0
                
            # Extract numbers from the parsed string (e.g., "35% full" -> 35)
            percentage = [int(s) for s in text_content.split() if s.replace('%','').isdigit()]
            if percentage:
                return percentage[0]
        else:
            print("Facility element not found.")
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

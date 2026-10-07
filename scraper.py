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

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_hougang_capacity():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(ACTIVESG_URL)
        
        # 1. Force Selenium to wait up to 20 seconds for Hougang text to actively render
        print("Waiting for dynamic content to load...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{FACILITY_NAME}')]"))
        )
        
        # 2. Grab the specific container card holding Hougang's data using XPath
        # This matches the element containing the text and steps up to its parent block
        hougang_element = driver.find_element(By.XPATH, f"//*[contains(text(), '{FACILITY_NAME}')]/ancestor::*[self::li or self::div][1]")
        text_content = hougang_element.text.strip()
        print(f"Match Found! Raw Data: {text_content}")
        
        if "Closed" in text_content:
            return 0
        
        # 3. Pull numbers sequence before the % sign (e.g., "72% full" -> 72)
        numbers = [int(s) for s in text_content.replace('%', ' ').split() if s.isdigit()]
        if numbers:
            return numbers[0]
            
        print("Could not parse capacity numbers from text.")
        return None
        
    except Exception as e:
        print(f"Scraper timed out or failed: {e}")
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

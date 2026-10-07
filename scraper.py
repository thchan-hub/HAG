import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Configurations ---
# Safely reads from GitHub Secrets. If running locally, replace the right side with your actual key string.
THINGSPEAK_WRITE_KEY = os.environ.get("THINGSPEAK_WRITE_KEY", "YOUR_THINGSPEAK_WRITE_API_KEY")
ACTIVESG_URL = "https://activesg.gov.sg"
FACILITY_NAME = "Hougang ActiveSG Gym"

def get_hougang_capacity():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    try:
        print("Navigating to ActiveSG...")
        driver.get(ACTIVESG_URL)
        
        print("Waiting for dynamic elements to load...")
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{FACILITY_NAME}')]"))
        )
        
        hougang_element = driver.find_element(By.XPATH, f"//*[contains(text(), '{FACILITY_NAME}')]/ancestor::*[self::li or self::div]")
        text_content = hougang_element.text.strip()
        print(f"Match Found! Raw Data:\n{text_content}")
        
        if "Closed" in text_content:
            return 0
        
        lines = text_content.split('\n')
        for line in lines:
            if "%" in line:
                digits = [int(s) for s in line.replace('%', ' ').split() if s.isdigit()]
                if digits:
                    return digits[0] # Return the integer directly

        print("Could not parse capacity numbers from text.")
        return None
        
    except Exception as e:
        print(f"Scraper timed out or failed: {e}")
        return None
    finally:
        driver.quit()

def push_to_thingspeak(value):
    # Properly formatted URL query parameters to avoid string replacement injection errors
    url = "https://thingspeak.com"
    payload = {
        'api_key': THINGSPEAK_WRITE_KEY,
        'field1': value
    }
    
    print(f"Sending payload to ThingSpeak...")
    response = requests.get(url, params=payload)
    
    if response.status_code == 200 and response.text != "0":
        print(f"Successfully sent {value}% capacity to ThingSpeak! Entry ID: {response.text}")
    elif response.text == "0":
        print("ThingSpeak rejected the update. Double-check your API Key or wait 15+ seconds between updates.")
    else:
        print(f"Failed to send data. Status code: {response.status_code}")

if __name__ == "__main__":
    capacity = get_hougang_capacity()
    if capacity is not None:
        push_to_thingspeak(capacity)

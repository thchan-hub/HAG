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
    
    # 💡 Crucial additions to bypass Cloudflare bot detection:
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Overwrite the navigator.webdriver property to appear completely organic
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    try:
        print("Navigating to ActiveSG...")
        driver.get(ACTIVESG_URL)
        
        # Force Selenium to wait up to 25 seconds for Hougang text to actively render
        print("Waiting for dynamic elements to load...")
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{FACILITY_NAME}')]"))
        )
        
        # Grab the specific container card holding Hougang's data
        hougang_element = driver.find_element(By.XPATH, f"//*[contains(text(), '{FACILITY_NAME}')]/ancestor::*[self::li or self::div]")
        text_content = hougang_element.text.strip()
        print(f"Match Found! Raw Data:\n{text_content}")
        
        if "Closed" in text_content:
            return 0
        
        # Split string by newlines to inspect the lines (e.g., Line 1: Name, Line 2: "49% full")
        lines = text_content.split('\n')
        for line in lines:
            if "%" in line:
                # Isolate the digits directly attached to the % sign
                digits = [int(s) for s in line.replace('%', ' ').split() if s.isdigit()]
                if digits:
                    return digits[0] # Return the actual 49% value explicitly

        print("Could not parse capacity numbers from text.")
        return None

             
    except Exception as e:
        print(f"Scraper timed out or failed: {e}")
        return None
    finally:
        driver.quit()

def push_to_thingspeak(value):
    # Ensure there is a proper slash after ://thingspeak.com and the update parameter is correct
    url = f"https://://thingspeak.com/update?api_key={THINGSPEAK_WRITE_KEY}&field1={value}"
    print(f"Sending payload to ThingSpeak...")
    response = requests.get(url)
    if response.status_code == 200:
        print(f"Successfully sent {value}% capacity to ThingSpeak!")
    else:
        print(f"Failed to send data. Status code: {response.status_code}")

if __name__ == "__main__":
    capacity = get_hougang_capacity()
    if capacity is not None:
        push_to_thingspeak(capacity)

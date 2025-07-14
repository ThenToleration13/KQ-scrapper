import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from time import sleep

# Configure Chrome options
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Run in headless mode for production
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_experimental_option("detach", True)  # Keep browser open

# For automatic driver management
from webdriver_manager.chrome import ChromeDriverManager
service = Service(ChromeDriverManager().install())

# Initialize the driver
driver = webdriver.Chrome(service=service, options=chrome_options)

# URL to scrape
url = "https://www.kenya-airways.com/en-ke/flight-deals/"

try:
    # Open the webpage
    print("Launching Chrome browser...")
    driver.get(url)
    print("Page loading...")
    
    # Wait for and accept cookies if the popup appears
    try:
        cookie_accept = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "cookieConsentAccept"))
        )
        cookie_accept.click()
        print("Cookie popup accepted")
        sleep(2)  # Wait after accepting cookies
    except Exception as e:
        print(f"No cookie popup found or couldn't accept it: {str(e)}")
    
    # Wait for the initial page to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "cta__destination-image-content"))
    )
    print("Initial page loaded successfully")
    sleep(3)  # Additional buffer time
    
    # Click "Show More" button multiple times with proper waits
    show_more_button_xpath = "//button[contains(text(), 'Show more') or contains(text(), 'SHOW MORE')]"
    
    for i in range(3):  # Try to click 3 times
        try:
            # Scroll to bottom to make sure button is in view
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"Scrolled to bottom (attempt {i+1})")
            sleep(2)  # Wait for scrolling
            
            # Wait for button to be clickable
            show_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, show_more_button_xpath))
            )
            
            # Use JavaScript click as it's more reliable
            driver.execute_script("arguments[0].click();", show_more_button)
            print(f"Clicked 'Show More' button {i+1} time(s)")
            
            # Wait for new content to load
            sleep(4)  # Increased wait time for content loading
            
            # Additional check - wait for loading indicator to disappear if present
            try:
                WebDriverWait(driver, 10).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loading-indicator"))
                )
            except:
                pass
            
        except Exception as e:
            print(f"Couldn't click 'Show More' button attempt {i+1}: {str(e)}")
            if i == 0:
                print("No 'Show More' button found - may have all deals already")
            break
    
    # Final scroll to trigger any lazy-loaded elements
    print("Final scrolling to load all elements...")
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(1.5)
    
    # Extended wait for all content to stabilize
    sleep(5)
    
    # Find all deal containers with refreshed search
    print("Locating all deal containers...")
    image_containers = WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "cta__destination-image-content"))
    )
    content_containers = driver.find_elements(By.CLASS_NAME, "cta__destination-content")
    
    # Check container counts
    print(f"Found {len(image_containers)} image containers and {len(content_containers)} content containers")
    
    # Prepare data collection
    deals = []
    
    # Extract data from each deal with error handling
    print("Extracting deal information...")
    for idx, (img_container, content_container) in enumerate(zip(image_containers, content_containers)):
        try:
            # Scroll to each element to ensure visibility
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", img_container)
            sleep(0.2)  # Small delay between scrolls
            
            # Extract data with individual waits
            plane_class = WebDriverWait(img_container, 5).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "cta__class"))
            ).text.strip()
            
            destination = WebDriverWait(img_container, 5).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "cta__title"))
            ).text.strip()
            
            date = WebDriverWait(content_container, 5).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "cta__date"))
            ).text.strip()
            
            price = WebDriverWait(content_container, 5).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "cta__price"))
            ).text.strip()
            
            deals.append({
                "Destination": destination,
                "Class": plane_class,
                "Travel Period": date,
                "Price": price
            })
            
            if (idx + 1) % 5 == 0:
                print(f"Processed {idx + 1} deals so far...")
                
        except Exception as e:
            print(f"Error processing deal {idx + 1}: {str(e)}")
            continue
    
    # Create DataFrame
    df = pd.DataFrame(deals)
    
    # Define output path
    output_dir = r"C:\Users\Training 24\Desktop\Exotic"
    output_file = os.path.join(output_dir, "KQ_flight_deals2.0.07.xlsx")
    
    # Create directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to Excel
    df.to_excel(output_file, index=False)
    print(f"\nSuccess! Scraped {len(deals)} flight deals saved to:\n{output_file}")
    
except Exception as e:
    print(f"\nError occurred during scraping: {str(e)}")
finally:
    # Keep browser open for inspection
    input("Press Enter to close the browser...")
    driver.quit()
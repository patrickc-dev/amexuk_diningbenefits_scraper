"""
Script to scrape restaurants from American Express UK Dining Benefit page
and save them to a CSV file.
"""

from ast import parse
import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import urllib.robotparser


def check_robots_txt(url_to_check, user_agent='*'):
    # 1. Parse the base domain to find the robots.txt location
    from urllib.parse import urlparse
    
    parsed_url = urlparse(url_to_check)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

    # 2. Initialize the parser
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    
    try:
        rp.read()
    except Exception as e:
        print(f"Could not read robots.txt: {e}")
        return False

    # 3. Check if the specific user-agent is allowed to visit the URL
    can_fetch = rp.can_fetch(user_agent, url_to_check)
    
    if can_fetch:
        print(f"✅ Allowed: You can crawl {url_to_check}")
    else:
        print(f"❌ Disallowed: {user_agent} is blocked from {url_to_check}")
    
    return can_fetch

def setup_driver(headless=True):
    """Setup and return a Chrome WebDriver instance."""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--window-size=1920,1080')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("Make sure Google Chrome is installed on your system")
        raise

def load_website(headless=True):

    print("Setting up browser...")
    driver = setup_driver(headless=headless)

    """Load the HTML of the page."""
    url = 'https://www.americanexpress.com/en-gb/benefits/diningbenefit/'
    can_fetch = check_robots_txt(url)
    if not can_fetch:
        return driver

    print(f"Loading page: {url}")
    driver.get(url)

    
    # Wait for page to load
    print("Waiting for page to load...")
    time.sleep(2)  # Increased wait time for dynamic content
    
    # Wait for any restaurant content to appear
    try:
        WebDriverWait(driver, 15).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "div, article, section")) > 10
        )
    except TimeoutException:
        print("Warning: Page may not have loaded completely")

    # Scroll to load dynamic content
    print("Scrolling to load all content...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    max_scrolls = 15  # Increased scroll attempts
    
    while scroll_attempts < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Increased wait between scrolls
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            scroll_attempts += 1
            if scroll_attempts >= 3:  # If height doesn't change 3 times, break
                break
        else:
            scroll_attempts = 0
        last_height = new_height
    
    # Scroll back to top slowly
    print("Scrolling back to top...")
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    # Always save HTML for debugging
    print("\nSaving page HTML for inspection...")
    save_page_html(driver)

    return driver

def save_page_html(driver, filename='page_source.html'):
    """Always save page HTML for debugging."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"Page HTML saved to '{filename}' for debugging.")
    except Exception as e:
        print(f"Warning: Could not save HTML file: {e}")

def scrape_restaurants(headless=True):

    try:        
        driver = load_website(headless=headless)
        print("Extracting restaurant data...")
        
        restaurants = []
        
        # Based on HTML analysis, restaurants are structured as:
        # Name: <div class="sc-dCFHLb..."><div id="flags"></div>RESTAURANT_NAME</div>
        # Address: <div class="sc-fhzFiK...">ADDRESS</div>
        
        # Find all restaurant name containers and extract details from parent
        try:
            # Find divs with class containing "sc-dCFHLb" that have a flags div inside
            restaurant_containers = driver.find_elements(By.CSS_SELECTOR, "div.sc-kOPcWz")
            print(f"Found {len(restaurant_containers)} potential name containers")

            if debug:
                print("Example name container:")
                sample_container = restaurant_containers[1]
                sample = sample_container.find_element(By.CSS_SELECTOR, "div.sc-dCFHLb")
                

                print("Text:")
                print(sample.text)
                print('textContent')
                print(sample.get_attribute("textContent"))
                print("Inner HTML:")
                print(sample.get_attribute('innerHTML'))
                print("Outer HTML:")
                print(sample.get_attribute('outerHTML'))

            for restaurant_container in restaurant_containers:
                try:
                    # Extract Name
                    name_div = restaurant_container.find_element(By.CSS_SELECTOR, "div.sc-dCFHLb")
                    name = name_div.get_attribute("textContent")
                    
                    # Find address div within the same parent
                    address_div = restaurant_container.find_elements(By.CSS_SELECTOR, "div.sc-fhzFiK")
                    if address_div:
                        address = address_div[0].get_attribute("innerHTML").strip()
                        if debug:
                            print(address) 
                        # Replace line breaks with commas
                        address = address.replace('<br>', ', ')
                        if debug:
                            print(address) 
                    
                    # Find cuisine - it's in div[class*='sc-jxOSlx'] (text after SVG)
                    cuisine_divs = restaurant_container.find_elements(By.CSS_SELECTOR, "div.sc-jxOSlx")
                    if cuisine_divs:
                        # Get the inner HTML to extract text after SVG
                        cuisine_html = cuisine_divs[0].get_attribute('innerHTML')
                        if cuisine_html:
                            # Extract text after the last </svg> tag
                            cuisine_match = re.search(r'</svg>([^<]+)', cuisine_html, re.DOTALL)
                            if cuisine_match:
                                cuisine = cuisine_match.group(1).strip()
                            else:
                                # Fallback: use text content and try to clean it
                                cuisine_text = cuisine_divs[0].text.strip()
                                cuisine = ' '.join(cuisine_text.split())
                        else:
                            cuisine_text = cuisine_divs[0].text.strip()
                            cuisine = ' '.join(cuisine_text.split())
                    
                    # Find Google Maps link - it's in an <a> tag with href containing "google.com/maps"
                    map_links = restaurant_container.find_elements(By.CSS_SELECTOR, "a[href*='google.com/maps']")
                    if map_links:
                        google_maps_link = map_links[0].get_attribute('href')
                        # Decode HTML entities if any
                        if google_maps_link:
                            google_maps_link = google_maps_link.replace('&amp;', '&')
                    
                    
                    restaurant_data = {
                        'Name': name,
                        'Address': address,
                        'Cuisine': cuisine,
                        'Google_Maps_Link': google_maps_link
                    }

                    restaurants.append(restaurant_data)
                    
                except Exception as e:
                    continue
                
        except Exception as e:
            print(f"Error extracting restaurants: {e}")
            import traceback
            traceback.print_exc()
    
        
        print(f"\nFound {len(restaurants)} restaurants after filtering")
        
        return restaurants
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        if driver:
            save_page_html(driver)
        raise
    
    finally:
        if driver:
            driver.quit()
            print("Browser closed.")


def save_to_csv(restaurants, filename='amex_restaurants.csv'):
    """Save restaurant data to CSV file."""
    if not restaurants:
        print("No restaurants to save.")
        return
    
    # Create DataFrame
    df = pd.DataFrame(restaurants)
    
    # Save to CSV
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"\nSuccessfully saved {len(restaurants)} restaurants to {filename}")
    
    if debug:
        # Display first few entries (only Name and Cuisine)
        print("\nFirst 5 entries:")
        if 'Name' in df.columns and 'Cuisine' in df.columns:
            display_df = df[['Name', 'Cuisine']].head()
            print(display_df.to_string(index=False))
        else:
            print(df.head().to_string())


def main():
    """Main function to run the scraper."""
    import sys
    
    print("=" * 60)
    print("American Express Dining Benefit Restaurant Scraper")
    print("=" * 60)
    
    # Check for headless flag
    headless = '--visible' not in sys.argv
    global debug 
    debug = '--debug' in sys.argv
    
    if not headless:
        print("Running in VISIBLE mode (browser window will be shown)")
        print("Use default mode (headless) by not passing --visible flag")
    else:
        print("Running in HEADLESS mode (no browser window)")
        print("Add --visible flag to see the browser window for debugging")
    
    try:
        restaurants = scrape_restaurants(headless=headless)
        save_to_csv(restaurants)
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


"""
Script to scrape restaurants from American Express UK Dining Benefit page
and save them to a CSV file.
"""

from ast import parse
from logging import raiseExceptions
from sys import exception
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

    # Dismiss Cookie Question
    cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "user-consent-management-granular-banner-decline-all-button")))
    cookie_button.click()
    
    
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
        time.sleep(1)  # Increased wait between scrolls
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
    time.sleep(1)
    
    # Always save HTML for debugging
    print("\nSaving page HTML for inspection...")
    save_page_html(driver)

    return driver

def get_available_countries(driver):
    """Get list of available country codes and names."""
    try:
        select = driver.find_element(By.ID, "country")
        options = select.find_elements(By.TAG_NAME, "option")
        countries = {}
        for opt in options:
            val = opt.get_attribute("value")
            text = opt.text
            if val and text:
                countries[val] = text
        return countries
    except Exception as e:
        print(f"Error getting available countries: {e}")
        return {}

def switch_country(driver, country_code):
    """Switch the country dropdown."""
    print(f"Switching to country code: {country_code}")
    try:
        # Use JavaScript to set value and trigger change event (as found in exploration)
        driver.execute_script("""
            const select = document.getElementById('country');
            select.value = arguments[0];
            select.dispatchEvent(new Event('change', { bubbles: true }));
        """, country_code)
        
        # Wait for content to update
        print("Waiting for content update...")
        time.sleep(3) # Give it a moment to start loading
        
        # Wait for restaurant containers to be present
        try:
            WebDriverWait(driver, 15).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "div.sc-kOPcWz")) > 0
            )
        except TimeoutException:
            print("Warning: Content update timed out or no restaurants found for this country.")
            
    except Exception as e:
        print(f"Error switching country: {e}")
        raise

def save_page_html(driver, filename_params=''):
    """Always save page HTML for debugging."""
    filename = f'page_source{filename_params}.html'
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"Page HTML saved to '{filename}' for debugging.")
    except Exception as e:
        print(f"Warning: Could not save HTML file: {e}")

def extract_details_from_restuarant_container(restaurant_container, div_tags):

    # Extract Name
    name = ""
    name_div = restaurant_container.find_element(By.CSS_SELECTOR, div_tags['name'])
    name = name_div.text
    name = name.replace('\n', ' - ')
    
    # Extract Address
    address = ""
    address_div = restaurant_container.find_elements(By.CSS_SELECTOR, div_tags['address'])
    if address_div:
        address = address_div[0].get_attribute("innerHTML").strip()
        if debug:
            print(address) 
        # Replace line breaks with commas
        address = address.replace('<br>', ', ')
        if debug:
            print(address) 
    
    # Extract Cuisine
    cuisine = ""
    cuisine_div = restaurant_container.find_element(By.CSS_SELECTOR, div_tags['cuisine'])
    if cuisine_div:
        # Get the inner HTML to extract text after SVG
        cuisine = cuisine_div.text
    
    # Find Google Maps link - it's in an <a> tag with href containing "google.com/maps"
    google_maps_link = ""
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

    return restaurant_data


def scrape_restaurants(driver, country_code): 
            
    location_div_tags = {
        'restaurant': 'div.sc-kOPcWz',
        'name': 'div.sc-dCFHLb',
        'address': 'div.sc-fhzFiK',
        'cuisine': 'div.sc-jxOSlx',
    }
    sub_location_div_tags = {
        'restaurant': 'div.sc-dhKdcB',
        'name': 'h2.sc-eldPxv',
        'address': 'div.sc-fPXMVe',
        'cuisine': 'div.sc-gFqAkR',
    }

    try:        
        # Switch to the requested country
        switch_country(driver, country_code)
        
        # Scroll to load dynamic content (needs to be done AFTER switching country)
        print("Scrolling to load all content...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 20
        
        while scroll_attempts < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
                if scroll_attempts >= 3:
                    break
            else:
                scroll_attempts = 0
            last_height = new_height
            
        driver.execute_script("window.scrollTo(0, 0);")
        
        print(f"Extracting restaurant data for {country_code}...")
        
        restaurants = []
        
        # Based on HTML analysis, restaurants are structured as:
        # Name: <div class="sc-dCFHLb..."><div id="flags"></div>RESTAURANT_NAME</div>
        # Address: <div class="sc-fhzFiK...">ADDRESS</div>
        
        # Find all restaurant name containers and extract details from parent
        try:
            # Find divs with class containing "sc-dCFHLb" that have a flags div inside
            restaurant_containers = driver.find_elements(By.CSS_SELECTOR, "div.sc-kOPcWz")
            print(f"Found {len(restaurant_containers)} restaurant containers")

            for restaurant_container in restaurant_containers:
                try:

                    view_location_btn = restaurant_container.find_elements(By.CSS_SELECTOR, "button.sc-fXSgeo")

                    if len(view_location_btn) > 0:

                        # Open Sub Restaurant List
                        view_location_btn[0].click()
                        WebDriverWait(driver, 5).until(
                            lambda d: len(d.find_elements(By.CSS_SELECTOR, sub_location_div_tags["restaurant"])) > 0
                        )
                        time.sleep(1)
                        sub_restaurant_containers = driver.find_elements(By.CSS_SELECTOR, sub_location_div_tags["restaurant"])
                        print(f"Found {len(sub_restaurant_containers)} sub-restaurant containers")
                        for sub_restaurant_container in sub_restaurant_containers:
                            restaurant_data = extract_details_from_restuarant_container(sub_restaurant_container, sub_location_div_tags)
                            restaurant_data['CountryCode'] = country_code
                            restaurants.append(restaurant_data)
                        # Close Sub Restaurant List
                        close_button = driver.find_element(By.CSS_SELECTOR, "button.sc-iHGNWf")
                        close_button.click()

                        WebDriverWait(driver, 5).until(
                            lambda d: len(d.find_elements(By.CSS_SELECTOR, "button.sc-iHGNWf")) == 0
                        )
                        time.sleep(1)

                    
                    else:
                        restaurant_data = extract_details_from_restuarant_container(restaurant_container, location_div_tags)
                        restaurant_data['CountryCode'] = country_code
                        restaurants.append(restaurant_data)
                    
                except Exception as e:
                    print(f"Error extracting individual restaurant: {e}")
                    continue
                
        except Exception as e:
            print(f"Error extracting restaurants: {e}")
            import traceback
            traceback.print_exc()
    
        
        print(f"Found {len(restaurants)} restaurants for {country_code}")
        
        return restaurants
        
    except Exception as e:
        print(f"Error during scraping {country_code}: {e}")
        if driver:
            save_page_html(driver, f'_{country_code}')
        raise


def save_to_csv(restaurants, country_code):
    """Save restaurant data to CSV file."""
    if not restaurants:
        print(f"No restaurants to save for {country_code}.")
        return
    
    filename = f'amex_restaurants_{country_code}.csv'
    
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
    import argparse
    
    print("=" * 60)
    print("American Express Dining Benefit Restaurant Scraper")
    print("=" * 60)
    
    parser = argparse.ArgumentParser(description='Scrape AMEX Dining Benefits')
    parser.add_argument('--visible', action='store_true', help='Run with visible browser window')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--country', type=str, default='GB', help='Country code to scrape (e.g., GB, US, FR) or "ALL"')
    
    args = parser.parse_args()
    
    headless = not args.visible
    global debug 
    debug = args.debug
    target_country = args.country.upper()
    
    if not headless:
        print("Running in VISIBLE mode")
    else:
        print("Running in HEADLESS mode")

    driver = None
    try:
        # Initialize driver once
        driver = load_website(headless=headless)
        
        available_countries = get_available_countries(driver)
        print(f"Available countries: {', '.join(available_countries.keys())}")
        
        countries_to_scrape = []
        if target_country == 'ALL':
            countries_to_scrape = list(available_countries.keys())
        elif target_country in available_countries:
            countries_to_scrape = [target_country]
        else:
            print(f"Error: Country '{target_country}' not found in available countries.")
            print(f"Available: {', '.join(available_countries.keys())}")
            return

        print(f"Will scrape: {', '.join(countries_to_scrape)}")
        
        for code in countries_to_scrape:
            print(f"\n--- Starting scrape for {available_countries[code]} ({code}) ---")
            try:
                restaurants = scrape_restaurants(driver, code)
                save_to_csv(restaurants, code)
            except Exception as e:
                print(f"Failed to scrape {code}: {e}")
                # Continue with next country
                continue
                
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            print("Browser closed.")

if __name__ == "__main__":
    main()

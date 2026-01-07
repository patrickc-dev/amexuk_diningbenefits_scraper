# American Express Dining Benefit Restaurant Scraper

This script scrapes all restaurants from the American Express UK Dining Benefit page and saves them to a CSV file. It supports scraping for multiple countries.

## Prerequisites

1. **Python 3.7+** installed on your system
2. **Google Chrome** browser installed
3. **ChromeDriver** (will be installed automatically via webdriver-manager)

## Installation

1. Install the required Python packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the scraper script (headless mode by default - scrapes UK 'GB' by default):
```bash
python scrape_restaurants.py
```

### Options

- `--visible`: Run with visible browser window (useful for debugging)
- `--debug`: Enable debug output
- `--country <CODE>`: Country code to scrape (e.g., `GB`, `US`, `FR`) or `ALL` to scrape all available countries.

### Examples

**Scrape a specific country (e.g., United States):**
```bash
python scrape_restaurants.py --country US
```

**Scrape all countries:**
```bash
python scrape_restaurants.py --country ALL
```

**Run in visible mode for debugging:**
```bash
python scrape_restaurants.py --visible --country FR
```

The script will:
1. Open a Chrome browser (headless by default, visible with `--visible` flag)
2. Navigate to the Amex dining benefit page
3. Select the specified country (if not default)
4. Wait for dynamic content to load
5. Scroll through the page to load all restaurant tiles
6. Extract restaurant information
7. Save the data to `amex_restaurants_<COUNTRY_CODE>.csv` (e.g., `amex_restaurants_US.csv`)

## Output

The script creates CSV files (e.g. `amex_restaurants_GB.csv`) with the following columns:
- **Name**: Restaurant name
- **Address**: Full address of the restaurant
- **Cuisine**: Type of cuisine (e.g., French, Italian, etc.)
- **Google_Maps_Link**: Direct link to Google Maps for the restaurant

## Troubleshooting

If the script doesn't find restaurants correctly:
1. **Check the HTML file**: The page HTML is always saved to `page_source_<COUNTRY_CODE>.html` for inspection
2. **Run in visible mode**: Use `python scrape_restaurants.py --visible` to see what the browser is doing
3. **Page structure changes**: The website structure may have changed - inspect the saved HTML to find the correct selectors
4. **JavaScript loading**: The website may require more time to load - you can increase wait times in the script

## Notes

- The script runs in **headless mode by default** (no visible browser window)
- Use the `--visible` flag to see the browser window for debugging
- The script **always saves** the page HTML for inspection
- It includes intelligent filtering to exclude dropdown menus, navigation, and country selectors
- Please respect the website's terms of service and robots.txt when scraping

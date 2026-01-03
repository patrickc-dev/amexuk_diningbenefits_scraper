# American Express Dining Benefit Restaurant Scraper

This script scrapes all restaurants from the American Express UK Dining Benefit page and saves them to a CSV file.

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

Run the scraper script (headless mode by default):
```bash
python scrape_restaurants.py
```

To see the browser window for debugging:
```bash
python scrape_restaurants.py --visible
```

The script will:
1. Open a Chrome browser (headless by default, visible with `--visible` flag)
2. Navigate to the Amex dining benefit page
3. Wait for dynamic content to load
4. Scroll through the page to load all restaurant tiles
5. Extract restaurant information (filtering out dropdown menus and navigation)
6. Save the data to `amex_restaurants.csv`
7. Always save page HTML to `page_source.html` for debugging

## Output

The script creates a CSV file (`amex_restaurants.csv`) with the following columns:
- **Name**: Restaurant name
- **Address**: Full address of the restaurant
- **Cuisine**: Type of cuisine (e.g., French, Italian, etc.)
- **Google_Maps_Link**: Direct link to Google Maps for the restaurant

## Troubleshooting

If the script doesn't find restaurants correctly:
1. **Check the HTML file**: The page HTML is always saved to `page_source.html` for inspection
2. **Run in visible mode**: Use `python scrape_restaurants.py --visible` to see what the browser is doing
3. **Page structure changes**: The website structure may have changed - inspect `page_source.html` to find the correct selectors
4. **JavaScript loading**: The website may require more time to load - you can increase wait times in the script

## Notes

- The script runs in **headless mode by default** (no visible browser window)
- Use the `--visible` flag to see the browser window for debugging
- The script **always saves** the page HTML to `page_source.html` for inspection
- It includes intelligent filtering to exclude dropdown menus, navigation, and country selectors
- It includes delays to allow dynamic content to load
- Please respect the website's terms of service and robots.txt when scraping

## Alternative: Manual Inspection

If automatic scraping doesn't work, you can:
1. Inspect the page HTML saved in `page_source.html`
2. Identify the correct CSS selectors for restaurant elements
3. Update the selectors in `scrape_restaurants.py`


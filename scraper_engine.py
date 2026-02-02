import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

def run_scraper():
    header = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36...",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
    }

    # 1. Scrape Data
    response = requests.get("https://appbrewery.github.io/Zillow-Clone/", headers=header)
    soup = BeautifulSoup(response.text, "html.parser")

    # 2. Extract logic (Your exact selectors)
    all_links = [link["href"] for link in soup.select(".StyledPropertyCardDataWrapper a")]
    all_addresses = [address.get_text().replace(" | ", " ").strip() for address in soup.select(".StyledPropertyCardDataWrapper address")]
    all_prices = [price.get_text().replace("/mo", "").split("+")[0] for price in soup.select(".PropertyCardWrapper span") if "$" in price.text]

    # 3. Create DataFrame and Save to CSV (Replacing Selenium)
    data = {
        "Address": all_addresses,
        "Price": all_prices,
        "Link": all_links
    }
    
    df = pd.DataFrame(data)
    
    # Ensure directory exists
    os.makedirs('results', exist_ok=True)
    file_path = "results/rental_data.csv"
    df.to_csv(file_path, index=False)
    
    return file_path
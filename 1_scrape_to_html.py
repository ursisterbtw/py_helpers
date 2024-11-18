import logging
import os

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Configuration
SCRAPE_URL = "https://docs.scroll.io/en/developers/scroll-contracts/"  # Replace with the actual URL to scrape
OUTPUT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "scRape"))
OUTPUT_HTML_FILE = os.path.join(OUTPUT_DIR, "scroll-contract-addresses.html")


def fetch_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        logging.info(f"Successfully fetched HTML from '{url}'.")
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching the URL '{url}': {e}")
        return None


def save_html(html_content, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    logging.info(f"Saved HTML content to '{output_file}'.")


def main():
    html_content = fetch_html(SCRAPE_URL)
    if html_content:
        save_html(html_content, OUTPUT_HTML_FILE)
    else:
        logging.error("Failed to fetch HTML content. Exiting.")


if __name__ == "__main__":
    main()

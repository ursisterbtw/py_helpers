import os
import re
import json
from bs4 import BeautifulSoup

SC_RAPE_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "scRape"))
OUTPUT_BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "constants"))


def extract_contracts(html_content):
    # Parse the HTML content
    soup = BeautifulSoup(html_content, "lxml")
    contracts = []
    # Regular expression to match Ethereum addresses
    eth_address_regex = re.compile(r"^0x[a-fA-F0-9]{40}$")
    # Find all tables in the HTML
    tables = soup.find_all("table")
    for table in tables:
        headers = [th.text.strip() for th in table.find("thead").find_all("th")]
        try:
            name_idx = headers.index("Name")
            address_idx = headers.index("Address")
        except ValueError:
            # Skip tables without 'Name' and 'Address' columns
            continue
        rows = table.find("tbody").find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= max(name_idx, address_idx) + 1:
                name = cols[name_idx].text.strip()
                address_tag = cols[address_idx].find("code")
                address = address_tag.text.strip() if address_tag else cols[address_idx].text.strip()
                if eth_address_regex.match(address):
                    contracts.append({"name": name, "address": address})
    return contracts


def save_contracts(contracts, output_dir, json_filename):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    contracts_data = {contract["name"]: contract["address"] for contract in contracts}
    output_file = os.path.join(output_dir, json_filename)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(contracts_data, f, indent=4)
    print(f"Saved {len(contracts)} contract addresses to '{output_file}'.")


def main():
    # Check if the scRape directory exists
    if not os.path.isdir(SC_RAPE_DIR):
        print(f"Error: scrape directory does not exist at '{SC_RAPE_DIR}'")
        return
    # Find all .html files in scRape directory
    html_files = [f for f in os.listdir(SC_RAPE_DIR) if f.lower().endswith(".html")]
    if not html_files:
        print(f"No .html files found in '{SC_RAPE_DIR}'")
        return
    for html_file in html_files:
        html_path = os.path.join(SC_RAPE_DIR, html_file)
        print(f"\nProcessing file: '{html_path}'")
        # Check if the input file exists
        if not os.path.isfile(html_path):
            print(f"Error: input file does not exist at '{html_path}'")
            continue
        try:
            # Read the HTML content
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            # Extract contracts
            contracts = extract_contracts(html_content)
            if not contracts:
                print(f"No valid contract addresses found in '{html_path}'.")
                continue
            # Dynamically name the output directory based on the HTML file name
            base_name = os.path.splitext(html_file)[0]
            output_dir = os.path.join(OUTPUT_BASE_DIR, base_name)
            # Define the JSON filename
            json_filename = f"{base_name}.json"
            # Save the contracts to JSON
            save_contracts(contracts, output_dir, json_filename)
        except FileNotFoundError as fnf_error:
            print(f"File not found: {fnf_error.filename}")
        except json.JSONDecodeError as json_error:
            print(f"JSON decode error: {json_error.msg}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()

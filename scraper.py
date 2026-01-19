import requests
from bs4 import BeautifulSoup
import pdfplumber
import io
import json
import re
import os
from datetime import datetime
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Grid-India URL
URL = "https://grid-india.in/reports/daily-reports/psp-report/"
# We use a standard browser User-Agent to avoid being blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def save_json(data):
    with open("latest_psp.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Successfully saved latest_psp.json")

def scrape_data():
    print("--- Starting Scraper ---")
    
    # Default data structure in case of failure
    output_data = {
        "status": "failed",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "energy_met": "N/A",
        "peak_shortage": "N/A",
        "pdf_url": URL,
        "error_message": ""
    }

    try:
        print(f"Connecting to {URL}...")
        response = requests.get(URL, headers=HEADERS, verify=False, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Website returned status code: {response.status_code}")

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Find the PDF link
        # Looking for any link ending in .pdf
        link_tag = soup.find('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        
        if not link_tag:
            output_data["error_message"] = "No PDF link found on the page."
            print("Error: No PDF link found.")
            save_json(output_data)
            return

        pdf_url = link_tag['href']
        print(f"Found PDF Link: {pdf_url}")
        output_data["pdf_url"] = pdf_url

        # 2. Download the PDF
        pdf_response = requests.get(pdf_url, headers=HEADERS, verify=False, timeout=30)
        
        # 3. Extract Data
        with pdfplumber.open(io.BytesIO(pdf_response.content)) as pdf:
            if len(pdf.pages) > 0:
                text = pdf.pages[0].extract_text()
                # print(text) # Uncomment for debugging if needed
                
                # Regex to find "Energy Met" (handles variations like "Energy Met (MU)")
                energy_met = re.search(r'Energy Met.*?(\d+[\.,]?\d*)', text, re.IGNORECASE)
                if energy_met:
                    output_data["energy_met"] = energy_met.group(1)
                
                # Regex to find "Peak Shortage" (handles "Peak Shortage (MW)")
                peak_shortage = re.search(r'Peak Shortage.*?(\d+[\.,]?\d*)', text, re.IGNORECASE)
                if peak_shortage:
                    output_data["peak_shortage"] = peak_shortage.group(1)

                output_data["status"] = "success"
                print("Extraction successful.")
            else:
                output_data["error_message"] = "PDF was empty."

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        output_data["error_message"] = str(e)

    # Always save the file, even if empty/failed, so GitHub doesn't error out
    save_json(output_data)

if __name__ == "__main__":
    scrape_data()

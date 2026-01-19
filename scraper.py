import requests
from bs4 import BeautifulSoup
import pdfplumber
import io
import json
import re
from datetime import datetime
import urllib3

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URL of the reports page
URL = "https://grid-india.in/reports/daily-reports/psp-report/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def scrape_data():
    print("Fetching Grid-India Reports page...")
    try:
        # verify=False is needed because Grid-India's SSL cert often has issues with bots
        response = requests.get(URL, headers=HEADERS, verify=False) 
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. Find the first PDF link
        link_tag = soup.find('a', href=re.compile(r'\.pdf$'))

        if not link_tag:
            print("No PDF link found.")
            return

        pdf_url = link_tag['href']
        print(f"Found PDF URL: {pdf_url}")

        # 2. Download the PDF
        pdf_response = requests.get(pdf_url, headers=HEADERS, verify=False)

        # 3. Extract Data
        data = {}
        with pdfplumber.open(io.BytesIO(pdf_response.content)) as pdf:
            first_page_text = pdf.pages[0].extract_text()

            data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data['pdf_url'] = pdf_url

            # Regex to find numbers
            energy_met = re.search(r'Energy Met.*?(\d+[\.,]?\d*)', first_page_text, re.IGNORECASE)
            data['energy_met'] = energy_met.group(1) if energy_met else "--"

            peak_shortage = re.search(r'Peak Shortage.*?(\d+[\.,]?\d*)', first_page_text, re.IGNORECASE)
            data['peak_shortage'] = peak_shortage.group(1) if peak_shortage else "--"

        # 4. Save to JSON
        with open("latest_psp.json", "w") as f:
            json.dump(data, f, indent=4)

        print("Data saved to latest_psp.json")

    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    scrape_data()

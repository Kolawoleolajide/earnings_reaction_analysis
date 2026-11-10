
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("FMP_API_KEY")

if not API_KEY:
    print("API key not found. Check your .env file.")
    sys.exit(1)

# API endpoint
url = "https://financialmodelingprep.com/stable/historical-price-eod/full"

# Request parameters
params = {
    "symbol": "AAPL",
    "from": "2026-09-01",
    "to": "2026-10-30",
    "apikey": API_KEY
}

try:
    response = requests.get(url, params=params, timeout=30)

    print("Status code:", response.status_code)

    response.raise_for_status()

    data = response.json()

    if isinstance(data, dict):
        print("API returned an error:", data)
    elif not data:
        print("No records returned.")
    else:
        print("Records retrieved:", len(data))
        print("\nFirst three records:")
        for record in data[:3]:
            print(record)

except requests.exceptions.RequestException:
    print("Request failed. Check your internet connection or API access.")
    sys.exit(1)
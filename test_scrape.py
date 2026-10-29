import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

url = 'https://mmadecisions.com/decisions-by-event/'
resp = requests.get(url, headers=headers, timeout=15)
print(f"Status code for {url}: {resp.status_code}")

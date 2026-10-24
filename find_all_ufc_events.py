import requests
from bs4 import BeautifulSoup
import re
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

url = 'https://mmadecisions.com/decisions-by-event/'
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

years = []
for a in soup.find_all('a', href=True):
    m = re.search(r'decisions-by-event/(\d{4})/', a['href'])
    if m:
        years.append(m.group(1))

years = sorted(list(set(years)), reverse=True)
print(f"Found {len(years)} years: {years}")

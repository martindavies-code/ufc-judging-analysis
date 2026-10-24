import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

url = 'https://mmadecisions.com/decision/15158/Shavkat-Rakhmonov-vs-Ian-Garry'
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

# Find tables that have round data
for idx, table in enumerate(soup.find_all('table')):
    headers_th = [th.get_text(strip=True) for th in table.find_all(['th', 'td'])]
    if 'ROUND' in headers_th:
        print(f"\n--- Found Round Table {idx} ---")
        # Check parent or preceding element to see where judge name is stored
        parent = table.find_parent('table')
        print("Table snippet:")
        print(table.prettify()[:1000])

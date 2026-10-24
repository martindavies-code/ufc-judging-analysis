import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

url = 'https://mmadecisions.com/decision/15158/Shavkat-Rakhmonov-vs-Ian-Garry'
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

tables = soup.find_all('table')
for i in range(min(9, len(tables))):
    print(f"\n=== Table {i} ===")
    for r in tables[i].find_all('tr'):
        cells = [c.get_text(strip=True) for c in r.find_all(['th', 'td'])]
        if cells and any(cells):
            print("  ", cells)

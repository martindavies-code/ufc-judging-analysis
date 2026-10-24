import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

url = 'https://mmadecisions.com/decision/15158/Shavkat-Rakhmonov-vs-Ian-Garry'
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

print("Title:", soup.title.string if soup.title else "")

tables = soup.find_all('table')
print(f"Total tables: {len(tables)}")
for i, t in enumerate(tables):
    rows = t.find_all('tr')
    print(f"\nTable {i}: {len(rows)} rows")
    for r in rows:
        cells = [c.get_text(strip=True) for c in r.find_all(['th', 'td'])]
        if cells and any(cells):
            print("  ", cells)

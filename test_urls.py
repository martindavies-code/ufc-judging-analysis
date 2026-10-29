import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

test_urls = [
    'https://mmadecisions.com/decision/15158/Shavkat-Rakhmonov-vs-Ian-Garry',
    'https://mmadecisions.com/decision/15158/',
    'https://mmadecisions.com/decision/15158',
    'http://mmadecisions.com/decision/15158/Shavkat-Rakhmonov-vs-Ian-Garry',
]

for u in test_urls:
    try:
        r = requests.get(u, headers=headers, timeout=15)
        print(f"{u} -> {r.status_code}")
    except Exception as e:
        print(f"{u} -> {e}")

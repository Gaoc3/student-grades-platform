import sys
from bs4 import BeautifulSoup
from curl_cffi import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

url = "https://web53112x.faselhdx.bid/seasons/%d9%85%d8%b3%d9%84%d8%b3%d9%84-the-punisher"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

r = requests.get(url, headers=headers, impersonate="chrome120", timeout=12)
soup = BeautifulSoup(r.text, 'html.parser')

print("=== Checking season loop containers ===")
loops = soup.find_all(class_=lambda x: x and 'season' in x.lower())
for l in loops:
    print(f"Tag: {l.name}, Class: {' '.join(l['class'])}")
    # Print some inner HTML snippet
    snippet = l.prettify()[:300]
    print("Snippet:")
    print(snippet)
    print("-" * 50)

print("\n=== Checking episode containers ===")
ep_elements = soup.find_all(class_=lambda x: x and 'ep' in x.lower())
for ep in ep_elements[:5]:
    print(f"Tag: {ep.name}, Class: {' '.join(ep['class'])}")
    print(ep.get_text(strip=True)[:100])

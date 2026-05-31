import sys
import os
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

url = "https://cinemana.cc/watch=2809688/" # Ultimate Spider-Man Season 2 Ep 13 watch URL

r = requests.get(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

soup = BeautifulSoup(r.text, 'html.parser')

print("--- Printing season-wrapper structures and all their child a tags ---")
season_wrappers = soup.find_all(class_='season-wrapper')
for idx, wrapper in enumerate(season_wrappers):
    print(f"\n================= WRAPPER {idx} =================")
    print(f"Wrapper class: {wrapper.get('class')}")
    anchors = wrapper.find_all('a', href=True)
    print(f"Found {len(anchors)} anchors in this wrapper:")
    for a_idx, a in enumerate(anchors):
        print(f"  [{a_idx}] text='{a.get_text(strip=True)}' href='{a['href']}'")

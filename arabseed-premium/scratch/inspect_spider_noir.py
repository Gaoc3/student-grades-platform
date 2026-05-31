import sys
import os
import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect Spider-Noir Season 1 Ep 1 Dubbed watch page
url = "https://cinemana.cc/watch=3021008/"

r = requests.get(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

soup = BeautifulSoup(r.text, 'html.parser')

print("--- Inspecting Season Triggers ---")
season_triggers = soup.find_all(class_='season-trigger')
for idx, trigger in enumerate(season_triggers):
    print(f"Trigger {idx}: text='{trigger.get_text(strip=True)}'")

print("\n--- Inspecting Season Wrappers ---")
season_wrappers = soup.find_all(class_='season-wrapper')
for idx, wrapper in enumerate(season_wrappers):
    print(f"Wrapper {idx}: episodes count={len(wrapper.find_all('a'))}")
    ep_anchors = wrapper.find_all('a', href=True)
    for a_idx, a in enumerate(ep_anchors):
        print(f"  [{a_idx}] text='{a.get_text(strip=True)}' href='{a['href']}'")

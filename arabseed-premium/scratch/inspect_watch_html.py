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

print("--- Searching for ALL elements with watch= in href ---")
all_anchors = soup.find_all('a', href=True)
watch_anchors = [a for a in all_anchors if 'watch=' in a['href']]

print(f"Total watch anchors: {len(watch_anchors)}")

for idx, a in enumerate(watch_anchors):
    href = a['href']
    text = a.get_text(strip=True)
    parent_classes = []
    p = a.parent
    while p and p.name != 'body':
        if p.get('class'):
            parent_classes.append(f"{p.name}.{'.'.join(p.get('class'))}")
        else:
            parent_classes.append(p.name)
        p = p.parent
        if len(parent_classes) > 4:
            break
    print(f"[{idx}] href='{href}' text='{text}' | Parents: {' -> '.join(parent_classes)}")

print("\n--- Let's look at the pagination/navigation on the page ---")
pagination_container = soup.find(class_=lambda x: x and any(y in x for y in ['pagination', 'page-numbers', 'nav-links']))
if pagination_container:
    print(f"Found pagination container: {pagination_container}")
else:
    print("No standard pagination container found.")

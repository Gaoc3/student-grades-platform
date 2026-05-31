import sys
import os
import requests
import re

sys.stdout.reconfigure(encoding='utf-8')

url = "https://cinemana.cc/watch=3021008/"

r = requests.get(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

print("Length of HTML:", len(r.text))

# Search for the post IDs in the HTML to see where they appear
post_ids = ['3021008', '3021010', '3021012', '3021014']
for pid in post_ids:
    print(f"\n--- Occurrences of '{pid}' in HTML ---")
    matches = [m.start() for m in re.finditer(pid, r.text)]
    print(f"Found {len(matches)} occurrences.")
    for idx, pos in enumerate(matches[:5]):
        start = max(0, pos - 150)
        end = min(len(r.text), pos + 150)
        snippet = r.text[start:end].replace('\n', ' ')
        print(f"  [{idx}] ... {snippet} ...")

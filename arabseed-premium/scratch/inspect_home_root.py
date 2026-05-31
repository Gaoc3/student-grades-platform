import sys
from bs4 import BeautifulSoup
from curl_cffi import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

url = "https://web53112x.faselhdx.bid/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

r = requests.get(url, headers=headers, impersonate="chrome120", timeout=12)
print("Status Code:", r.status_code)
print("Text length:", len(r.text))
if r.status_code != 200:
    print("Headers:", r.headers)
    print("Preview:", r.text[:200])
soup = BeautifulSoup(r.text, 'html.parser')

print("=== Checking container elements on Root Homepage ===")
for div in soup.find_all('div', id=True):
    print(f"Div ID: {div['id']}, Class: {' '.join(div.get('class', []))}")

print("\n=== Checking postList elements ===")
post_list = soup.find(id="postList")
if post_list:
    print("Found postList!")
    cards = post_list.find_all(class_="postDiv")
    print(f"Contains {len(cards)} postDiv cards")
else:
    print("postList not found by ID!")

rows = soup.find_all(class_="form-row")
for i, row in enumerate(rows[:5]):
    print(f"Row {i+1} parent ID: {row.parent.get('id') if row.parent else 'None'}, Parent Class: {' '.join(row.parent.get('class', [])) if row.parent else 'None'}")
    cards = row.find_all(class_="postDiv")
    print(f"  Contains {len(cards)} postDiv cards")

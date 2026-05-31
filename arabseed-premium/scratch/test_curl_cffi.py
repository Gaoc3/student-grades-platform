from curl_cffi import requests
from bs4 import BeautifulSoup

url = "https://web53112x.faselhdx.bid/seasons/%d9%85%d8%b3%d9%84%d8%b3%d9%84-the-punisher"
url_season = "https://web53112x.faselhdx.bid/?p=40476"

print("--- Fetching main page using curl_cffi ---")
try:
    r = requests.get(url, impersonate="chrome120", timeout=12)
    print("Status Code:", r.status_code)
    print("HTML Length:", len(r.text))
    soup = BeautifulSoup(r.text, 'html.parser')
    title_el = soup.find('h1') or soup.find('h2') or soup.title
    print("Title text parsed:", title_el.get_text(strip=True) if title_el else "None")
except Exception as e:
    print("Error:", e)

print("\n--- Fetching season page using curl_cffi ---")
try:
    r = requests.get(url_season, impersonate="chrome120", timeout=12)
    print("Status Code:", r.status_code)
    print("HTML Length:", len(r.text))
    soup = BeautifulSoup(r.text, 'html.parser')
    ep_all = soup.find(class_="epAll")
    print("Found epAll:", ep_all is not None)
    if ep_all:
        print("Episodes count:", len(ep_all.find_all('a')))
except Exception as e:
    print("Error:", e)

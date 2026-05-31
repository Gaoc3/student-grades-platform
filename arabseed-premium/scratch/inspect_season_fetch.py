import requests
from bs4 import BeautifulSoup

url = "https://web53112x.faselhdx.bid/?p=40476"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Referer": "https://web53112x.faselhdx.bid/"
}

r = requests.get(url, headers=headers, timeout=10)
print("Status Code:", r.status_code)
print("Content Length:", len(r.text))
soup = BeautifulSoup(r.text, 'html.parser')
ep_all = soup.find(class_="epAll")
print("Found epAll:", ep_all is not None)
if ep_all:
    links = ep_all.find_all('a')
    print("Links count in epAll:", len(links))
    if links:
        print("First link text:", links[0].get_text(strip=True))
        print("First link href:", links[0].get('href'))
else:
    print("HTML Snippet around where epAll should be:")
    print(r.text[:1000])

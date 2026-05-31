import urllib.parse
from curl_cffi import requests

# Unquote the URL to see if it makes a difference
quoted_url = "https://web53112x.faselhdx.bid/episodes/%d9%85%d8%b3%d9%84%d8%b3%d9%84-punisher-%d8%a7%d9%84%d9%85%d9%88%d8%b3%d9%85-%d8%a7%d9%84%d8%a3%d9%88%d9%84-%d8%a7%d9%84%d8%ad%d9%84%d9%82%d9%87-1"
unquoted_url = urllib.parse.unquote(quoted_url)

print("Quoted URL:", quoted_url)
print("Unquoted URL:", unquoted_url)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Referer": "https://web53112x.faselhdx.bid/seasons/%d9%85%d8%b3%d9%84%d8%b3%d9%84-the-punisher",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1"
}

print("\n--- Trying Quoted URL ---")
r1 = requests.get(quoted_url, headers=headers, impersonate="chrome120", timeout=12)
print("Quoted Status:", r1.status_code)

print("\n--- Trying Unquoted URL ---")
r2 = requests.get(unquoted_url, headers=headers, impersonate="chrome120", timeout=12)
print("Unquoted Status:", r2.status_code)

# Try with a different mirror domain
print("\n--- Testing alternative domain ---")
alt_url = quoted_url.replace("web53112x.faselhdx.bid", "faselhd.online")
print("Alternative URL:", alt_url)
try:
    r3 = requests.get(alt_url, headers=headers, impersonate="chrome120", timeout=12)
    print("Alt Status:", r3.status_code)
except Exception as e:
    print("Alt failed:", e)

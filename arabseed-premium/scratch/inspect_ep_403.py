import sys
import os
from curl_cffi import requests

url = "https://web53112x.faselhdx.bid/episodes/%d9%85%d8%b3%d9%84%d8%b3%d9%84-punisher-%d8%a7%d9%84%d9%85%d9%88%d8%b3%d9%85-%d8%a7%d9%84%d8%a3%d9%88%d9%84-%d8%a7%d9%84%d8%ad%d9%84%d9%82%d9%87-1"

print("--- Fetching Episode URL with curl_cffi ---")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Upgrade-Insecure-Requests": "1"
}

r = requests.get(url, headers=headers, impersonate="chrome120", timeout=12)
print("Status Code:", r.status_code)
print("Response text length:", len(r.text))
if r.status_code != 200:
    print("Headers:", r.headers)
    print("Preview of body:", r.text[:500])

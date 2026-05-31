import sys
import urllib.parse
from curl_cffi import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# We construct a clean session
session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1"
}

# 1. Lowercase percent encoding
lowercase_url = "https://web53112x.faselhdx.bid/episodes/%d9%85%d8%b3%d9%84%d8%b3%d9%84-punisher-%d8%a7%d9%84%d9%85%d9%88%d8%b3%d9%85-%d8%a7%d9%84%d8%a3%d9%88%d9%84-%d8%a7%d9%84%d8%ad%d9%84%d9%82%d9%87-1"
print("1. Trying lowercase percent-encoded URL in clean session...")
try:
    r1 = session.get(lowercase_url, headers=headers, impersonate="chrome120", timeout=10)
    print("Status:", r1.status_code)
except Exception as e:
    print("Error:", e)

# 2. Uppercase percent encoding in a clean session
session2 = requests.Session()
uppercase_url = "https://web53112x.faselhdx.bid/episodes/%D9%85%D8%B3%D9%84%D8%B3%D9%84-punisher-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%85-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%A7%D9%84%D8%AD%D9%84%D9%82%D9%87-1"
print("\n2. Trying uppercase percent-encoded URL in clean session...")
try:
    r2 = session2.get(uppercase_url, headers=headers, impersonate="chrome120", timeout=10)
    print("Status:", r2.status_code)
except Exception as e:
    print("Error:", e)

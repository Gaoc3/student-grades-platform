import sys
import os
import urllib.parse
from curl_cffi import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# The resolved master m3u8 URL from our last test
target_m3u8 = "https://master.c.scdns.io/stream/v2/SmnzJCS10W5C6wGw4EQytw/1780261110/normal/0/169.224.21.2/yes/15e442867d0ab581192c857fb04846ea/web53112x.faselhdx.bid/master.m3u8"

print("--- Testing direct fetch of CDN master m3u8 ---")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://asd.ink/'
}

try:
    r = requests.get(target_m3u8, headers=headers, impersonate="chrome120", timeout=12)
    print("Status Code:", r.status_code)
    print("Headers:", r.headers)
    print("Content preview:")
    print(r.text[:500])
except Exception as e:
    print("Direct fetch failed:", e)

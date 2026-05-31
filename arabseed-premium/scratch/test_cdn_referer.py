import requests

url = "https://master.c.scdns.io/stream/v2/AOXrnB5sFS_RhZ2DOqAuEw/1780260303/normal/0/169.224.21.2/yes/15e442867d0ab581192c857fb04846ea/web53112x.faselhdx.bid/master.m3u8"

headers_asd = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://asd.ink/"
}

headers_fasel = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://web53112x.faselhdx.bid/"
}

print("Testing with Referer: https://asd.ink/")
try:
    r = requests.get(url, headers=headers_asd, timeout=10)
    print("Status Code:", r.status_code)
    print("Content Preview:", r.text[:200] if r.status_code == 200 else "Blocked")
except Exception as e:
    print("Error:", e)

print("\nTesting with Referer: https://web53112x.faselhdx.bid/")
try:
    r = requests.get(url, headers=headers_fasel, timeout=10)
    print("Status Code:", r.status_code)
    print("Content Preview:", r.text[:200] if r.status_code == 200 else "Blocked")
except Exception as e:
    print("Error:", e)

import sys
import os
import urllib.parse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

# Target HLS playlist URL from FaselHD scdns CDN
target_m3u8 = "https://master.c.scdns.io/stream/v2/SmnzJCS10W5C6wGw4EQytw/1780261110/normal/0/169.224.21.2/yes/15e442867d0ab581192c857fb04846ea/web53112x.faselhdx.bid/master.m3u8"

client = app.test_client()

print("--- Testing /api/stream with Flask test client ---")
url = f"/api/stream?url={urllib.parse.quote(target_m3u8)}"
print("Requesting URL:", url)

r = client.get(url)
print("Status Code:", r.status_code)
print("Content-Type:", r.headers.get('Content-Type'))
print("Access-Control-Allow-Origin:", r.headers.get('Access-Control-Allow-Origin'))
print("\n--- Rewritten HLS Content ---")
print(r.data.decode('utf-8', errors='ignore')[:800])

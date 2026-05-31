import sys
import os
import urllib.parse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

# Target segment URL
segment_url = "https://r467--8katnn5p.c.scdns.io/stream/v1/hls/eBBfGzV-Xdgbz7hcM4esJA/1780261131/web53112x.faselhdx.bid/all/169.224.21.2/yes/IQ/0/08-02/1/15e442867d0ab581192c857fb04846ea/160_hd1080b_segment_1.ts"

client = app.test_client()

print("--- Testing /api/stream with a segment ---")
url = f"/api/stream?url={urllib.parse.quote(segment_url)}"
print("Requesting URL:", url)

r = client.get(url)
print("Status Code:", r.status_code)
print("Content-Type:", r.headers.get('Content-Type'))
print("Content-Length:", r.headers.get('Content-Length'))
print("Response data length:", len(r.data))

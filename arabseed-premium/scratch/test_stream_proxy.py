import sys
import os
import requests

sys.stdout.reconfigure(encoding='utf-8')

# Let's test the /api/stream proxy endpoint locally!
# We will construct a real Cinemana stream URL from our previous test:
cinemana_stream_url = "https://cinemana.cc/stream.php?session=3021008&url=https%3A//r467--8katnn5p.c.scdns.io/stream/v1/hls/2Rn4rq6ox1KSiYKNzxm47Q/1780232682/www.fasel-hd.cam/all/185.244.36.179/yes/T1/0/08-02/2/e0a9077491e6a1fe67806e19f91b4742/160_hd1080b_playlist.m3u8"

local_api_url = f"http://127.0.0.1:5000/api/stream?url={requests.utils.quote(cinemana_stream_url)}"

print(f"📡 Requesting local stream proxy at: {local_api_url}")

try:
    r = requests.get(local_api_url, timeout=15)
    print("Response status code:", r.status_code)
    print("Response headers:")
    for k, v in r.headers.items():
        print(f"  {k}: {v}")
        
    print("\n--- Response Body Snippet (First 500 chars) ---")
    print(r.text[:500])
except Exception as e:
    print("Error calling stream proxy:", e)

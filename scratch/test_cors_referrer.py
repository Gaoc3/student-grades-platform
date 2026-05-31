import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

base_url = "https://cinemana.cc"
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

print("Fetching main page to get a live watch URL...")
r = session.get(f"{base_url}/main/", timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')
watch_a = None
for a in soup.find_all('a', href=True):
    if 'watch=' in a['href'] and re.search(r'watch=\d+', a['href']):
        watch_a = a
        break

post_id = re.search(r'watch=(\d+)', watch_a['href']).group(1) if watch_a else '3062248'
print(f"Post ID: {post_id}")

watch_url = f"https://cinemana.cc/watch={post_id}/"
ajax_url = "https://cinemana.cc/wp-content/themes/EEE/Inc/Ajax/Single/Server.php"
data = {'post_id': post_id, 'server': '0'}

session.headers['Referer'] = watch_url
session.get(watch_url, timeout=10)
r = session.post(ajax_url, data=data, timeout=10)

stream_url = None
if r.status_code == 200:
    match = re.search(r'const\s+originalUrls\s*=\s*({[^}]+})', r.text)
    if match:
        urls_str = match.group(1)
        url_matches = re.findall(r'["\']?(\w+)["\']?\s*:\s*["\']([^"\']+)["\']', urls_str)
        if url_matches:
            orig_url = url_matches[0][1]
            stream_url = f"https://cinemana.cc/stream.php?session={post_id}&url={urllib.parse.quote(orig_url)}"

if not stream_url:
    print("Failed to resolve stream URL.")
    exit(1)

# Get the first segment URL
r_playlist = session.get(stream_url, timeout=10)
segment_line = None
for line in r_playlist.text.split('\n'):
    if line.strip() and not line.strip().startswith('#'):
        segment_line = line.strip()
        break

if not segment_line:
    print("No segment found in playlist.")
    exit(1)

segment_url = "https://cinemana.cc/" + segment_line if segment_line.startswith('stream.php') else segment_line
print(f"\nLive segment URL: {segment_url}")

# Test referrers
referrers = {
    "Direct (No Referer)": None,
    "Google Referer": "https://google.com/",
    "Own Platform Referer": "https://reaches-featured-streets-delivering.trycloudflare.com/",
    "Official Cinemana Referer": "https://cinemana.cc/"
}

for desc, ref in referrers.items():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    if ref:
        headers['Referer'] = ref
        
    print(f"\nTesting {desc} with Referer: {ref}")
    try:
        r_test = requests.head(segment_url, headers=headers, timeout=8)
        print(f"  HEAD Status: {r_test.status_code}")
        # Try GET too
        r_get = requests.get(segment_url, headers=headers, stream=True, timeout=8)
        print(f"  GET Status: {r_get.status_code}")
        print(f"  CORS header: {r_get.headers.get('Access-Control-Allow-Origin')}")
    except Exception as e:
        print(f"  Error: {e}")

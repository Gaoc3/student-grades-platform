import requests

# Fetch the master playlist to get a valid active sub-playlist
master_url = "https://master.c.scdns.io/stream/v2/AOXrnB5sFS_RhZ2DOqAuEw/1780260303/normal/0/169.224.21.2/yes/15e442867d0ab581192c857fb04846ea/web53112x.faselhdx.bid/master.m3u8"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://web53112x.faselhdx.bid/"
}

r = requests.get(master_url, headers=headers, timeout=10)
print("Master Playlist status:", r.status_code)
if r.status_code == 200:
    lines = r.text.split('\n')
    sub_url = None
    for line in lines:
        if line.strip() and not line.startswith('#'):
            sub_url = line.strip()
            break
            
    print("Sub-playlist URL:", sub_url)
    if sub_url:
        r_sub = requests.get(sub_url, headers=headers, timeout=10)
        print("Sub-playlist status:", r_sub.status_code)
        if r_sub.status_code == 200:
            sub_lines = r_sub.text.split('\n')
            segment_rel = None
            for s_line in sub_lines:
                if s_line.strip() and not s_line.startswith('#'):
                    segment_rel = s_line.strip()
                    break
            
            import urllib.parse
            segment_url = urllib.parse.urljoin(sub_url, segment_rel)
            print("Segment URL:", segment_url)
            
            # Request segment with OPTIONS preflight or standard GET to check CORS headers
            r_seg = requests.get(segment_url, headers=headers, timeout=10)
            print("\nSegment response headers:")
            for k, v in r_seg.headers.items():
                if 'access-control' in k.lower():
                    print(f"{k}: {v}")
                else:
                    # just print other relevant ones
                    if k.lower() in ['server', 'content-type', 'content-length']:
                        print(f"{k}: {v}")

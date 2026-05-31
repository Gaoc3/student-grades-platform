# -*- coding: utf-8 -*-
import sys
import os
import json
sys.stdout.reconfigure(encoding='utf-8')

# Configure paths
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.abspath('.'))

from app import app

# Create a test client
client = app.test_client()
url = "https://cinemana.cc/watch=3021048/"
print(f"Requesting /api/details for: {url}")
response = client.get(f"/api/details?url={url}")
data = json.loads(response.data)

print(f"Status Code: {response.status_code}")
print(f"Title: {data.get('title')}")
print(f"Is Series: {data.get('is_series')}")
seasons = data.get('seasons', [])
print(f"Total Seasons: {len(seasons)}")

for idx, s in enumerate(seasons):
    print(f"\n[Season {idx}] Title: {s['title']} | Active: {s.get('active')}")
    episodes = s.get('episodes', [])
    print(f"    Total Episodes: {len(episodes)}")
    for ep in episodes:
        print(f"      - {ep['title']} | URL: {ep['url']} | Active: {ep.get('active')}")

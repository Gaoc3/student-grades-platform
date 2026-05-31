import sys
import os
import requests
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import resolve_cinemana_stream, resolve_arabseed_stream

sys.stdout.reconfigure(encoding='utf-8')

print("🔍 Testing Cinemana HLS stream resolution for post 3021008 (Spider-Noir Season 1 Ep 1)...")
cinemana_servers = resolve_cinemana_stream("https://cinemana.cc/watch=3021008/")
print(f"Cinemana resolved {len(cinemana_servers)} servers:")
for s in cinemana_servers:
    print(f"- Server name: {s['server']}")
    print(f"  URL: {s['url']}")
    print(f"  Original URL: {s.get('original_url')}")

print("\n🔍 Testing ArabSeed hybrid stream resolution for Spider-Noir Season 1 Ep 1...")
arabseed_servers = resolve_arabseed_stream("مسلسل Spider-Noir", True, "موسم 1", "الحلقة 1")
print(f"ArabSeed resolved {len(arabseed_servers)} servers:")
for s in arabseed_servers:
    print(f"- Server name: {s['server']}")
    print(f"  URL: {s['url']}")

import sys
import os
import json
import urllib.parse
from curl_cffi import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import resolve_fasel_stream
from fasel_scraper import FaselAPI

api = FaselAPI()
ep_url = "https://web53112x.faselhdx.bid/episodes/%D9%85%D8%B3%D9%84%D8%B3%D9%84-punisher-%D8%A7%D9%84%D9%85%D9%85%D9%88%D8%B3%D9%85-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%A7%D9%84%D8%AD%D9%84%D9%82%D9%87-1"

# Make sure the URL is properly quoted (using upper-case hex characters to avoid CF 403)
quoted_ep_url = "https://web53112x.faselhdx.bid/episodes/%D9%85%D8%B3%D9%84%D8%B3%D9%84-punisher-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%85-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%A7%D9%84%D8%AD%D9%84%D9%82%D9%87-1"

print("--- Resolving streams for episode ---")
servers = resolve_fasel_stream(quoted_ep_url)
print("Resolved streams:")
print(json.dumps(servers, indent=2, ensure_ascii=False))

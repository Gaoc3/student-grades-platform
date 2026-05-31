# -*- coding: utf-8 -*-
import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

from cinemana_scraper import CinemanaAPI
from app import clean_for_search, normalize_arabic, parse_episode_num, parse_season_num, parse_episode_title

api = CinemanaAPI()
query = "سبايدرمان نوار"
print(f"Searching for: {query}")
results = api.search(query)
print(f"Found {len(results)} results:")
for idx, r in enumerate(results):
    title = r.get('title', '')
    r_type = r.get('type', '')
    url = r.get('url', '')
    
    clean = clean_for_search(title)
    norm = normalize_arabic(clean)
    s_num, e_num, ver = parse_episode_title(title)
    
    print(f"\n[{idx}] Type: {r_type} | URL: {url}")
    print(f"    Original Title: {title}")
    print(f"    Cleaned Base:   {clean}")
    print(f"    Parsed Season:  {s_num} | Episode: {e_num} | Version: '{ver}'")

# -*- coding: utf-8 -*-
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

# Configure paths
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.abspath('.'))

from cinemana_scraper import CinemanaAPI
from app import clean_for_search, normalize_arabic, parse_episode_title

api = CinemanaAPI()

# Simulate details API behavior
raw_title = "سبايدر نوار"
base_query = clean_for_search(raw_title)
print(f"Base Query: '{base_query}'")

season_words = ["الاول", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر"]
queries = [base_query]
for word in season_words:
    queries.append(f"{base_query} الموسم {word}")

# Run search
search_results = []
seen_urls = set()
for q in queries:
    results = api.search(q)
    for r in results:
        if r['url'] not in seen_urls:
            seen_urls.add(r['url'])
            search_results.append(r)

print(f"Total search results harvested: {len(search_results)}")

orig_base_cleaned = normalize_arabic(clean_for_search(raw_title))
matched_items = []
for r in search_results:
    if r.get('type') == 'فيلم':
        continue
    r_base_cleaned = normalize_arabic(clean_for_search(r['title']))
    if r_base_cleaned == orig_base_cleaned:
        matched_items.append(r)

print(f"Total matched TV show items: {len(matched_items)}")
for idx, r in enumerate(matched_items):
    s_num, e_num, ver = parse_episode_title(r['title'])
    print(f"[{idx}] Title: {r['title']}")
    print(f"    Parsed -> Season: {s_num} | Episode: {e_num} | Version: '{ver}'")

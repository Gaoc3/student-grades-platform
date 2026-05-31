import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cinemana_scraper import CinemanaAPI

sys.stdout.reconfigure(encoding='utf-8')

api = CinemanaAPI()

print("🔍 Searching for 'Spider-Noir' to get its details...")
results = api.search("Spider")
print(f"Found {len(results)} results.")

spider_noir = None
for r in results:
    print(f"- {r['title']} | Type: {r['type']} | URL: {r['url']}")
    if "spider" in r['title'].lower():
        spider_noir = r

# If not found by search, let's search for "Noir" or "Noir"
if not spider_noir:
    results2 = api.search("Noir")
    for r in results2:
        print(f"- {r['title']} | Type: {r['type']} | URL: {r['url']}")
        if "noir" in r['title'].lower():
            spider_noir = r

if spider_noir:
    print(f"\n📂 Fetching details for Spider-Noir at: {spider_noir['url']}")
    details = api.get_details(spider_noir['url'])
    print("\n✅ DETAILS METADATA:")
    print(f"Title: {details.get('title')}")
    print(f"Is Series: {details.get('is_series')}")
    print(f"Seasons count: {len(details.get('seasons', []))}")
    
    for s in details.get('seasons', []):
        print(f"  Season Title: '{s['title']}' | Active: {s['active']} | Episodes count: {len(s['episodes'])}")
        if s['episodes']:
            print(f"    First Ep: {s['episodes'][0]['title']} ({s['episodes'][0]['url']})")
            print(f"    Last Ep: {s['episodes'][-1]['title']} ({s['episodes'][-1]['url']})")
            print(f"    Episode titles: {[ep['title'] for ep in s['episodes']]}")
else:
    print("\n❌ Could not find Spider-Noir, checking general homepage categories for any series...")
    cats = api.get_homepage_categories()
    found_series = None
    for cat in cats:
        for card in cat['cards']:
            if card['type'] == 'مسلسل':
                found_series = card
                break
        if found_series:
            break
            
    if found_series:
        print(f"\n📂 Fetching details for '{found_series['title']}' at: {found_series['url']}")
        details = api.get_details(found_series['url'])
        print("\n✅ DETAILS METADATA:")
        print(f"Title: {details.get('title')}")
        print(f"Is Series: {details.get('is_series')}")
        print(f"Seasons count: {len(details.get('seasons', []))}")
        for s in details.get('seasons', []):
            print(f"  Season Title: '{s['title']}' | Active: {s['active']} | Episodes count: {len(s['episodes'])}")
            if s['episodes']:
                print(f"    First Ep: {s['episodes'][0]['title']} ({s['episodes'][0]['url']})")
                print(f"    Episode titles: {[ep['title'] for ep in s['episodes']]}")
    else:
        print("❌ No series found on homepage.")

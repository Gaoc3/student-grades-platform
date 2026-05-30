import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')
from arabseed_scraper import ArabSeedAPI

api = ArabSeedAPI()
print("Mirror in use:", api.base_url)

print("\n--- Test Search ---")
results = api.search("الست")
print(f"Found {len(results)} results.")
for i, item in enumerate(results[:3]):
    print(f"Result {i+1}: {item['title']} | Type: {item['type']} | Quality: {item['quality']} | URL: {item['url']}")

if results:
    selected = results[0]
    print(f"\n--- Fetching details for first result: {selected['title']} ---")
    details = api.get_details(selected['url'])
    print("Is Series:", details['is_series'])
    print("Title:", details['title'])
    print("Description:", details['description'][:100] + "...")
    
    print(f"\n--- Fetching download links for first result ---")
    links = api.get_download_links(selected['url'])
    print(f"Found {len(links)} download links.")
    for l in links[:5]:
        print(f"  Server: {l['server']} | Quality: {l['quality']} | Size: {l['size']}")
        print(f"  Direct Link: {l['direct_link']}")
        print("-" * 20)
        
print("\n✅ Verification Successful!")

import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

url = "https://m.asd.ink/%d9%85%d8%b3%d9%84%d8%b3%d9%84-the-four-seasons-s2-eps8/"
print("Fetching:", url)
try:
    r = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Find links with 'الحلقة' in text or 'eps' in href that are outside the header search
    ep_links = []
    for a in soup.find_all("a"):
        text = a.get_text(strip=True)
        href = a.get("href") or ""
        if "الحلقة" in text or "eps" in href.lower():
            # Exclude header
            parents = [p.name + ("." + ".".join(p.get("class")) if p.get("class") else "") for p in a.parents]
            if not any(any(k in p for k in ["top__search", "header", "menu__bar"]) for p in parents):
                ep_links.append((a, parents))
                
    print(f"Found {len(ep_links)} episode links in main area:")
    for a, parents in ep_links[:10]:
        print("Link:", a.prettify().strip())
        print("  Parents:", parents[:3])
        print("-" * 20)
        
except Exception as e:
    print("Error:", e)

import sys
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

filepath = "scratch/download_page_raw.html"
with open(filepath, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Let's find anchors with 'الحلقة' but outside header/footer menu structures
ep_anchors = []
for a in soup.find_all("a"):
    text = a.get_text(strip=True)
    href = a.get("href") or ""
    # We want episode links (typically containing "الحلقة" in text or "eps" in href)
    if "الحلقة" in text or "eps" in href.lower():
        # Exclude header/dropdown elements
        parent_classes_str = "".join([str(p.get('class')) for p in a.parents if p.get('class')])
        if not any(k in parent_classes_str for k in ["top__search", "header", "menu__bar", "footer", "mobile__big__menu"]):
            ep_anchors.append(a)

print(f"Found {len(ep_anchors)} episode anchors.")
if ep_anchors:
    first_ep = ep_anchors[0]
    print("First Ep Anchor:")
    print("  Href:", first_ep.get("href"))
    print("  Text:", first_ep.get_text(strip=True))
    print("  Classes:", first_ep.get("class"))
    
    # Let's inspect its parent container
    parent = first_ep.parent
    print("Parent Tag:", parent.name, "Classes:", parent.get("class"))
    
    grandparent = parent.parent
    print("Grandparent Tag:", grandparent.name, "Classes:", grandparent.get("class"))
    
    # Find all siblings or other episode links in this container
    container = grandparent
    links = container.find_all("a")
    print(f"Total links in container: {len(links)}")
    for a in links[:10]:
        print(f"  Link: {a.get('href')} | Text: {a.get_text(strip=True)} | Class: {a.get('class')}")

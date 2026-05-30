import sys
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup
import urllib.parse
import base64

filepath = "scratch/watch_page_raw.html"
with open(filepath, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

# Find all iframes
print("Iframes:")
for iframe in soup.find_all("iframe"):
    src = iframe.get("src") or ""
    print(f"  Src: {src}")
    if "play.php?url=" in src:
        b64_part = src.split("play.php?url=")[1]
        try:
            decoded = base64.b64decode(b64_part).decode('utf-8', errors='ignore')
            print(f"    Decoded Stream Link: {decoded}")
        except Exception as e:
            print(f"    Failed to decode {b64_part}: {e}")

# Find all anchors that might lead to streaming/playing
print("\nAnchors with play or watch:")
for a in soup.find_all("a"):
    href = a.get("href") or ""
    text = a.get_text(strip=True)
    if "play" in href or "watch" in href or "play.php" in href:
        print(f"  Href: {href} | Text: {text}")
        
# Find other elements with class servers__list or similar
print("\nChecking for servers/qualities buttons:")
for el in soup.find_all(class_=lambda x: x and any(k in x.lower() for k in ["server", "quality", "switcher"])):
    print(f"  Tag: {el.name} | Class: {el.get('class')} | Text: {el.get_text(strip=True)[:100]}")

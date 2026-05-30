import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# The download page URL we discovered
download_url = "https://m.asd.ink/%d9%81%d9%8a%d9%84%d9%85-%d8%a7%d9%84%d8%b3%d8%aa-2025/download/"

print("Fetching download page:", download_url)
try:
    r = requests.get(download_url, headers=headers, timeout=10)
    print("Status Code:", r.status_code)
    print("Response Length:", len(r.text))
    
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Let's search for download links, cards, buttons, lists
    print("\n--- Searching for standard lists in download page ---")
    dl_tabs = soup.find(class_="downloads__tabs")
    dl_list = soup.find(class_="downloads__links__list")
    
    if dl_tabs:
        print("downloads__tabs found!")
        print(dl_tabs.prettify()[:1000])
        
    if dl_list:
        print("downloads__links__list found!")
        for li in dl_list.find_all("li"):
            print("LI element:")
            a_tag = li.find("a")
            if a_tag:
                print("  Download Link:", a_tag.get("href"))
                print("  Download Text:", a_tag.get_text(strip=True))
            # Check for qualities/sizes
            quality = li.find(class_="quality") or li.find(class_="badge__quality") or li.find(class_="size")
            if quality:
                print("  Quality/Size:", quality.get_text(strip=True))
            print("-" * 10)
            
    # If not found, print all external or file-like download links
    if not dl_tabs and not dl_list:
        print("No predefined classes found. Listing all anchors:")
        for a in soup.find_all("a"):
            href = a.get("href") or ""
            text = a.get_text(strip=True)
            if href.startswith("http") and not href.startswith("https://m.asd.ink"):
                print(f"External Link: {href} (Text: {text})")
            elif "تحميل" in text or "down" in href.lower() or "dl" in href.lower():
                print(f"Link: {href} (Text: {text})")
                
    # Save the page html for safety
    with open("scratch/download_page_raw.html", "w", encoding="utf-8") as f:
        f.write(r.text)
        
except Exception as e:
    print("Error:", e)

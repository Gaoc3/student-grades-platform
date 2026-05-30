import requests
import sys
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

# Let's request the main search page first to see if it works and what it returns
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Try searching for a film (e.g., "الست" or something else)
search_url = "https://m.asd.ink/find/"
params = {"word": "الست"}

print(f"Requesting search: {search_url} with params {params}")
try:
    r = requests.get(search_url, params=params, headers=headers, timeout=10)
    print("Response Status:", r.status_code)
    print("Response Length:", len(r.text))
    
    soup = BeautifulSoup(r.text, "html.parser")
    movie_blocks = soup.find_all(class_="movie__block")
    print(f"Found {len(movie_blocks)} movie blocks in live search.")
    for i, block in enumerate(movie_blocks[:3]):
        print(f"Block {i+1}:")
        print("Href:", block.get("href"))
        title_el = block.find(class_="post__name") or block.find("h3")
        if title_el:
            print("Title:", title_el.get_text(strip=True))
            
        # Try fetching this block's detail page to inspect its HTML!
        detail_url = block.get("href")
        if detail_url:
            print(f"Requesting detail page: {detail_url}")
            detail_r = requests.get(detail_url, headers=headers, timeout=10)
            print("Detail Status:", detail_r.status_code)
            
            detail_soup = BeautifulSoup(detail_r.text, "html.parser")
            
            # Check for download links
            print("\n--- Download Section ---")
            dl_section = detail_soup.find(class_="downloads__links__list") or detail_soup.find(class_="downloads__tabs")
            if dl_section:
                print("Download Section Found!")
                # Print all anchors inside it
                for a in dl_section.find_all("a"):
                    print("DL Link:", a.get("href"), "Text:", a.get_text(strip=True))
            else:
                print("No standard downloads section found by class.")
                # Search for all anchors with 'download' or 'تحميل' or pointing to external server
                for a in detail_soup.find_all("a"):
                    href = a.get("href") or ""
                    text = a.get_text(strip=True)
                    if "تحميل" in text or "download" in href or "download" in text.lower():
                        print("Found potential DL link:", href, "Text:", text)
            
            # Check for watch / player area
            print("\n--- Watch / Player Section ---")
            watch_area = detail_soup.find(class_="watch__area") or detail_soup.find(class_="player__iframe")
            if watch_area:
                print("Watch Section Found!")
                iframe = watch_area.find("iframe")
                if iframe:
                    print("Watch Iframe:", iframe.get("src"))
            else:
                print("No standard watch section found by class.")
                # Search for iframes
                for iframe in detail_soup.find_all("iframe"):
                    print("Iframe source:", iframe.get("src"))
                    
            # Let's save a part of the HTML to inspect if nothing was found
            if not dl_section and not watch_area:
                print("\nSaving raw HTML of detail page for inspection...")
                with open("scratch/detail_raw.html", "w", encoding="utf-8") as f:
                    f.write(detail_r.text)
                    
            break # Just test the first one
except Exception as e:
    print("Error:", e)

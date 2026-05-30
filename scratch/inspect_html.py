import re
import sys
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

def inspect_file(filepath):
    print(f"=== Inspecting {filepath} ===")
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Search form
    search_form = soup.find("form")
    if search_form:
        print("Search Form found:")
        print("Action:", search_form.get("action"))
        print("Inputs:", [inp.get("name") for inp in search_form.find_all("input")])
    
    # 2. Movie block items
    movie_blocks = soup.find_all(class_=re.compile("movie__block"))
    print(f"\nFound {len(movie_blocks)} movie blocks.")
    for i, block in enumerate(movie_blocks[:5]):
        print(f"Block {i+1}:")
        print("Tag:", block.name)
        print("Classes:", block.get("class"))
        print("Href:", block.get("href"))
        
        # Inner poster
        poster_img = block.find("img")
        if poster_img:
            print("Poster img sources:", {attr: poster_img.get(attr) for attr in ["src", "data-src", "data-lazy-src"] if poster_img.has_attr(attr)})
        
        # Title
        title_el = block.find(class_=re.compile("post__name")) or block.find("h3") or block.find(class_=re.compile("title"))
        if title_el:
            print("Title text:", title_el.get_text(strip=True))
            
        print("-" * 20)

inspect_file("c:\\Users\\secon\\.openclaw\\workspace\\student-grades-platform\\arabseed-clone\\raw_movies.html")
inspect_file("c:\\Users\\secon\\.openclaw\\workspace\\student-grades-platform\\arabseed-clone\\raw_source.html")

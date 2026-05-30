# -*- coding: utf-8 -*-
"""
Aura Cinema - Premium Ad-Free Web Portal Backend
------------------------------------------------
A Flask server that integrates the ArabSeed scraping engine and acts as a transparent
HTTP Range-compliant video stream proxy to bypass 403 blocks and popups.
"""

import os
import sys
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, Response, render_template, jsonify

# Force UTF-8 output to support Arabic characters in all terminals
sys.stdout.reconfigure(encoding='utf-8')

# Append parent directory to path to import arabseed_scraper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from arabseed_scraper import ArabSeedAPI
except ImportError:
    # Fallback if path structure differs
    sys.path.append(os.getcwd())
    from arabseed_scraper import ArabSeedAPI

app = Flask(__name__, template_folder='templates', static_folder='static')

# Initialize ArabSeed Scraper API
api = ArabSeedAPI()

def extract_direct_mp4(embed_url: str) -> str:
    """
    Fetches the reviewrate.net embed page and extracts the direct .mp4 CDN source URL.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://m.asd.ink/'
    }
    try:
        r = requests.get(embed_url, headers=headers, timeout=10)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 1. Look for <source> tag with type="video/mp4"
        source_tag = soup.find('source', type='video/mp4')
        if source_tag and source_tag.get('src'):
            return source_tag.get('src')
            
        # 2. Regex fallback for source src containing video.mp4
        match = re.search(r'src=["\']([^"\']+\.mp4[^"\']*)["\']', r.text)
        if match:
            return match.group(1)
            
        # 3. Search for any URL ending in .mp4 inside javascript blocks
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                mp4_matches = re.findall(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', script.string)
                if mp4_matches:
                    return mp4_matches[0]
                    
    except Exception as e:
        print(f"Error extracting direct MP4 from {embed_url}: {e}")
        
    return ""

def scrape_listing_page(url: str) -> list:
    """
    Scrapes any standard listing page (like category pages or homepages) on ArabSeed
    and returns standard structured catalog items, resolving relative URLs correctly.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': api.base_url + '/'
    }
    try:
        r = requests.get(url, headers=headers, timeout=12)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        blocks = soup.find_all(class_="movie__block")
        
        results = []
        for block in blocks:
            href = block.get("href")
            if not href:
                continue
                
            url_item = href
            if url_item.startswith('/'):
                url_item = api.base_url + url_item
                
            img_tag = block.find("img")
            poster = ""
            if img_tag:
                poster = img_tag.get("data-src") or img_tag.get("src") or ""
                
            title_tag = block.find(class_="post__name") or block.find("h3")
            title = title_tag.get_text(strip=True) if title_tag else "غير معروف"
            
            rating_tag = block.find(class_="post__ratings") or block.find(class_="rating")
            rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"
            
            quality_tag = block.find(class_="badge__quality") or block.find(class_="quality")
            quality = quality_tag.get_text(strip=True) if quality_tag else "FHD"
            
            # Detect Media Type from title/URL
            media_type = "فيلم"
            if "مسلسل" in title or "s1" in url_item.lower() or "s2" in url_item.lower() or "season" in url_item.lower() or "eps" in url_item.lower():
                media_type = "مسلسل"
            elif "اغنية" in title.lower() or "أغنية" in title or "track" in url_item.lower():
                media_type = "موسيقى"
                
            results.append({
                "title": title,
                "url": url_item,
                "poster": poster,
                "rating": rating,
                "quality": quality,
                "type": media_type
            })
            
        return results
    except Exception as e:
        print(f"Error scraping listing page {url}: {e}")
        return []

def clean_series_title(title: str) -> str:
    """
    Cleans series titles by stripping episode numbers, spelled-out feminine numbers,
    translation suffixes, and quality badges while fully preserving season words and masculine numbers.
    """
    t = title
    
    # 1. Remove "الحلقة XX" or "حلقة XX"
    t = re.sub(r'(?:الحلقة|حلقة)\s+\d+', '', t)
    
    # 2. Remove ONLY feminine spelled-out Arabic numbers and words like "الأولى", "الاخيرة", etc.
    # These feminine forms refer to "الحلقة" (episode), whereas masculine forms refer to "الموسم" (season).
    feminine_arabic_numbers = [
        "الاولى", "الأولى", "الاولي", "الثانية", "الثالثة", "الرابعة", "الخامسة", "السادسة", 
        "السابعة", "الثامنة", "التاسعة", "العاشرة", "الاخيرة", "الأخيرة", "والاخيرة", "والأخيرة",
        "الاخير", "الأخير"
    ]
    # Build regex to match these words as full words
    words_pattern = r'\b(?:' + '|'.join(feminine_arabic_numbers) + r')\b'
    t = re.sub(words_pattern, '', t)
    
    # 3. Remove "الحلقة" or "حلقة" if it remains
    t = re.sub(r'\b(?:الحلقة|حلقة)\b', '', t)
    
    # 4. Remove common quality and translation badges (including feminine versions)
    badges = [
        "مترجم", "مترجمة", "مدبلج", "مدبلجة", "بلوراي", "كامل", "كاملة", "HD", "FHD", "WEB-DL", "وب-دل", "وب ديل"
    ]
    badges_pattern = r'\b(?:' + '|'.join(badges) + r')\b'
    t = re.sub(badges_pattern, '', t, flags=re.IGNORECASE)
    
    # Clean up any leftover punctuation like trailing dashes, slashes, or extra spaces
    t = re.sub(r'[-\s/|]+', ' ', t).strip()
    return t

def group_results(results: list) -> list:
    """
    Groups scattered series episodes under a single series card.
    Updates the card title to the clean series name and retains only one card per series/season.
    """
    grouped = {}
    for item in results:
        title = item.get('title', '')
        media_type = item.get('type', 'فيلم')
        
        # We only group series (type is "مسلسل" or contains "مسلسل" or "حلقة" or "الموسم" in title)
        is_series = "مسلسل" in title or "حلقة" in title or media_type == "مسلسل" or "الموسم" in title
        
        if is_series:
            clean_title = clean_series_title(title)
            # If we haven't seen this series before, add it
            if clean_title not in grouped:
                item['title'] = clean_title
                item['type'] = 'مسلسل'
                grouped[clean_title] = item
            else:
                # Retain the one we found first (which is usually the latest episode link)
                pass
        else:
            # Keep movie entries as unique by title
            grouped[title] = item
            
    return list(grouped.values())

@app.route('/')
def home():
    """Renders the main single page web interface."""
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    """
    Searches ArabSeed for movies/series or routes directly to category pages
    if special navigation query flags are present, and groups scattered episodes.
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Search query is required.'}), 400
        
    try:
        # Check connection/fallback to working mirror
        api.auto_fallback_mirror()
        
        # Route to direct category pages if special flags are sent
        if query == '__home__':
            target_url = f"{api.base_url}/main10/"
            results = scrape_listing_page(target_url)
            category_title = "الرئيسية"
        elif query == '__movies__':
            target_url = f"{api.base_url}/movies-3/"
            results = scrape_listing_page(target_url)
            category_title = "أحدث الأفلام"
        elif query == '__series__':
            urls = [
                f"{api.base_url}/category/foreign-series-7/",
                f"{api.base_url}/category/arabic-series-14/",
                f"{api.base_url}/category/turkish-series-2/",
                f"{api.base_url}/category/cartoon-series/"
            ]
            from concurrent.futures import ThreadPoolExecutor
            all_results = []
            
            def scrape_and_assign_type(url):
                res = scrape_listing_page(url)
                for item in res:
                    item['type'] = 'مسلسل'
                return res
                
            with ThreadPoolExecutor(max_workers=len(urls)) as executor:
                futures = [executor.submit(scrape_and_assign_type, url) for url in urls]
                for f in futures:
                    try:
                        all_results.extend(f.result())
                    except Exception as exc:
                        print(f"Error executing task for series scraping: {exc}")
                        
            results = all_results
            category_title = "أحدث المسلسلات المضافة"
        else:
            # Standard search
            results = api.search(query)
            category_title = f"البحث عن: {query}"
            
        # Group scattered series episodes into unified series/season cards
        results = group_results(results)
        
        return jsonify({
            'results': results, 
            'mirror': api.base_url,
            'category': category_title
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/details')
def api_details():
    """Fetches details and episode list for a specific movie/series URL."""
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL is required.'}), 400
        
    try:
        details = api.get_details(url)
        return jsonify(details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watch')
def api_watch():
    """
    Fetches streaming links, automatically extracts raw CDN streams from preferred servers,
    and formats them for Plyr.js or sandboxed fallback.
    """
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL is required.'}), 400
        
    try:
        watch_links = api.get_watch_links(url)
        formatted_players = []
        
        for idx, wl in enumerate(watch_links):
            direct_link = wl.get('direct_link', '')
            server_name = wl.get('server', f'سيرفر {idx+1}')
            
            # Detect preferred server (reviewrate.net)
            if 'reviewrate.net' in direct_link or 'play.php' in direct_link:
                # Attempt to extract direct MP4 CDN source
                cdn_url = extract_direct_mp4(direct_link)
                if cdn_url:
                    # Encode URL to pass to our range proxy
                    encoded_cdn = urllib.parse.quote(cdn_url)
                    formatted_players.append({
                        'type': 'direct',
                        'server': f'✨ {server_name} (خالٍ من الإعلانات)',
                        'url': f'/api/stream?url={encoded_cdn}',
                        'original_url': cdn_url
                    })
                    continue
            
            # Fallback to sandboxed iframe for external servers
            formatted_players.append({
                'type': 'iframe',
                'server': server_name,
                'url': direct_link
            })
            
        return jsonify({'servers': formatted_players})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream')
def api_stream_proxy():
    """
    Transparent chunked-streaming proxy supporting HTTP Range requests.
    Intercepts video player stream queries, appends valid headers (Referer, User-Agent),
    and pipes data directly to bypass Nginx hotlink protections.
    """
    video_url = request.args.get('url', '').strip()
    if not video_url:
        return "Video URL parameter is required", 400
        
    # Unquote URL if double-encoded
    video_url = urllib.parse.unquote(video_url)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://m.reviewrate.net/'
    }
    
    # Forward the client's Range header if requested
    range_header = request.headers.get('Range')
    if range_header:
        headers['Range'] = range_header
        
    try:
        # Stream connection to CDN
        r = requests.get(video_url, headers=headers, stream=True, timeout=20)
        
        # Response chunk generator
        def generate():
            try:
                # Use a larger chunk size for high-speed buffering
                for chunk in r.iter_content(chunk_size=131072):
                    if chunk:
                        yield chunk
            except Exception as e:
                # Log errors in streaming without breaking the app
                print(f"Streaming Interrupted: {e}")
                
        # Exclude connection-negotiation headers
        excluded_headers = ['connection', 'transfer-encoding', 'keep-alive', 'content-encoding']
        resp_headers = []
        for name, value in r.headers.items():
            if name.lower() not in excluded_headers:
                resp_headers.append((name, value))
                
        return Response(generate(), status=r.status_code, headers=resp_headers)
    except Exception as e:
        return f"Streaming Proxy Error: {e}", 502

if __name__ == '__main__':
    print("=" * 60)
    print(" 🚀 AURA CINEMA - PREMIUM AD-FREE PORTAL STARTING...")
    print(" Running at http://0.0.0.0:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)

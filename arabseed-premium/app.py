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

def extract_mp4_from_download(download_url: str) -> str:
    """
    Simulates the two-stage POST filesharing flow on reviewrate.net
    to extract the raw high-quality 1080p .mp4 CDN URL.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://m.asd.ink/'
    }
    try:
        parts = download_url.rstrip('/').split('/')
        file_id = parts[-1]
        
        # 1. GET page to find fname
        r = requests.get(download_url, headers=headers, timeout=10)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'html.parser')
        fname_input = soup.find('input', {'name': 'fname'})
        fname = fname_input.get('value') if fname_input else ""
        if not fname:
            match = re.search(r'name=["\']fname["\']\s+value=["\']([^"\']+)["\']', r.text)
            if match:
                fname = match.group(1)
                
        if not fname:
            return ""
            
        # 2. First POST (op = download1)
        data1 = {
            'op': 'download1',
            'usr_login': '',
            'id': file_id,
            'fname': fname,
            'referer': 'https://m.asd.ink/',
            'method_free': 'Free Download'
        }
        r1 = requests.post(download_url, headers=headers, data=data1, timeout=12)
        r1.raise_for_status()
        
        # 3. Second POST (op = download2)
        data2 = {
            'op': 'download2',
            'id': file_id,
            'rand': '',
            'referer': 'https://m.asd.ink/',
            'method_free': 'Free Download',
            'method_premium': ''
        }
        r2 = requests.post(download_url, headers=headers, data=data2, timeout=12)
        r2.raise_for_status()
        
        mp4_matches = re.findall(r'(https?://[^\s"\'>]+\.mp4[^\s"\']*)', r2.text)
        if mp4_matches:
            return mp4_matches[0]
            
    except Exception as e:
        print(f"Error extracting direct MP4 from download link {download_url}: {e}")
        
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

def parse_series_info(title: str):
    """
    Parses base series title and season name from any ArabSeed title.
    """
    t = title
    
    # Extract season if present
    season_name = "الموسم الأول" # Default
    season_match = re.search(r'(الموسم\s+(?:\d+|[\u0600-\u06FF]+))', t)
    
    if season_match:
        season_name = season_match.group(1)
        base_title = t[:season_match.start()].strip()
    else:
        ep_match = re.search(r'\s+(?:الحلقة|حلقة)\b', t)
        if ep_match:
            base_title = t[:ep_match.start()].strip()
        else:
            base_title = t
            
    # Clean base title from quality/translation badges
    badges = [
        "مترجم", "مترجمة", "مدبلج", "مدبلجة", "بلوراي", "كامل", "كاملة", "HD", "FHD", "WEB-DL", "وب-دل", "وب ديل"
    ]
    badges_pattern = r'\b(?:' + '|'.join(badges) + r')\b'
    base_title = re.sub(badges_pattern, '', base_title, flags=re.IGNORECASE)
    base_title = re.sub(r'[-\s/|]+', ' ', base_title).strip()
    
    return base_title, season_name

def clean_series_title(title: str) -> str:
    """
    Cleans series titles by stripping episode numbers, quality badges, and season names.
    """
    base_title, _ = parse_series_info(title)
    return base_title

def group_results(results: list) -> list:
    """
    Groups scattered series episodes and seasons under a single series card.
    Every grouped series card contains a 'seasons' list mapping season names to URLs.
    """
    grouped = {}
    for item in results:
        title = item.get('title', '')
        media_type = item.get('type', 'فيلم')
        
        is_series = "مسلسل" in title or "حلقة" in title or media_type == "مسلسل" or "الموسم" in title
        
        if is_series:
            base_title, season_name = parse_series_info(title)
            
            # If we haven't seen this series base title before, create its group
            if base_title not in grouped:
                item['title_original'] = title
                item['title'] = base_title
                item['type'] = 'مسلسل'
                item['seasons'] = [{'title': season_name, 'url': item.get('url'), 'quality': item.get('quality')}]
                grouped[base_title] = item
            else:
                existing_item = grouped[base_title]
                
                # Check if this season already exists in the seasons list
                season_exists = False
                for s in existing_item['seasons']:
                    if s['title'] == season_name:
                        season_exists = True
                        
                        # Prioritize higher quality URLs for the same season
                        def get_quality_score(q_str):
                            score = 0
                            q_lower = q_str.lower()
                            if '1080' in q_lower or 'fhd' in q_lower:
                                score = 3
                            elif '720' in q_lower or 'hd' in q_lower:
                                score = 2
                            elif '480' in q_lower or 'sd' in q_lower:
                                score = 1
                            return score
                            
                        if get_quality_score(item.get('quality', '')) > get_quality_score(s.get('quality', '')):
                            s['url'] = item.get('url')
                            s['quality'] = item.get('quality')
                        break
                        
                if not season_exists:
                    existing_item['seasons'].append({
                        'title': season_name,
                        'url': item.get('url'),
                        'quality': item.get('quality')
                    })
        else:
            grouped[title] = item
            
    # For all grouped series, sort their seasons in a clean logical order (newest season first)
    for base_title, item in grouped.items():
        if 'seasons' in item:
            def extract_season_num(s_title):
                s_name = s_title.replace("الموسم", "").strip()
                mapping = {
                    "الاول": 1, "الأول": 1, "الأولى": 1, "الاولى": 1, "الاولي": 1,
                    "الثاني": 2, "الثانية": 2, "الثالث": 3, "الثالثة": 3,
                    "الرابع": 4, "الرابعة": 4, "الخامس": 5, "الخامسة": 5,
                    "السادس": 6, "السادسة": 6, "السابع": 7, "السابعة": 7,
                    "الثامن": 8, "الثامنة": 8, "التاسع": 9, "التاسعة": 9,
                    "العاشر": 10, "العاشرة": 10
                }
                if s_name in mapping:
                    return mapping[s_name]
                num_match = re.search(r'\d+', s_name)
                if num_match:
                    return int(num_match.group())
                return 0
                
            item['seasons'] = sorted(item['seasons'], key=lambda s: extract_season_num(s['title']), reverse=True)
            
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
    Fetches streaming and download links, automatically extracts raw CDN streams from preferred servers 
    (prioritizing direct 1080p download links and watch servers), and formats them for Plyr.js.
    """
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL is required.'}), 400
        
    try:
        formatted_players = []
        
        # 1. Fetch download links to search for high-speed direct 1080p reviewrate streams
        try:
            download_links = api.get_download_links(url)
            for dl in download_links:
                direct_link = dl.get('direct_link', '')
                quality = dl.get('quality', '')
                # We specifically look for reviewrate.net or direct download links with 1080p quality
                if 'reviewrate.net' in direct_link and '1080' in quality:
                    cdn_url = extract_mp4_from_download(direct_link)
                    if cdn_url:
                        encoded_cdn = urllib.parse.quote(cdn_url)
                        formatted_players.append({
                            'type': 'direct',
                            'server': f'✨ سيرفر مباشر فائق الجودة 1080p (خالٍ من الإعلانات)',
                            'url': f'/api/stream?url={encoded_cdn}',
                            'original_url': cdn_url
                        })
                        # Stop after adding the best 1080p link to keep it clean
                        break
        except Exception as dl_err:
            print(f"Error fetching download links for streaming extraction: {dl_err}")
            
        # 2. Fetch standard watch links
        watch_links = api.get_watch_links(url)
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

# -*- coding: utf-8 -*-
"""
AleX CINEMA - Premium Ad-Free Web Portal Backend
------------------------------------------------
A Flask server that integrates the Shabakaty Cinemana scraping engine and resolves
high-quality, ad-free video streams transparently via ArabSeed search matching.
Acts as a transparent Range-compliant video stream proxy to bypass 403 blocks and popups.
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
    sys.path.append(os.getcwd())
    from arabseed_scraper import ArabSeedAPI

# Import Cinemana Scraper
from cinemana_scraper import CinemanaAPI

app = Flask(__name__, template_folder='templates', static_folder='static')

# Initialize Scrapers
api = ArabSeedAPI()
cinemana_api = CinemanaAPI()

# Arabic numbers mapping to digits for robust season/episode matching
ARABIC_NUMBERS = {
    "الاول": 1, "الأول": 1, "الأولى": 1, "الاولى": 1, "الاولي": 1, "اول": 1, "أول": 1,
    "الثاني": 2, "الثانية": 2, "ثاني": 2, "ثانية": 2,
    "الثالث": 3, "الثالثة": 3, "ثالث": 3, "ثالثة": 3,
    "الرابع": 4, "الرابعة": 4, "رابع": 4, "رابعة": 4,
    "الخامس": 5, "الخامسة": 5, "خامس": 5, "خامسة": 5,
    "السادس": 6, "السادسة": 6, "سادس": 6, "سادسة": 6,
    "السابع": 7, "السابعة": 7, "سابع": 7, "سابعة": 7,
    "الثامن": 8, "الثامنة": 8, "ثامن": 8, "ثامنة": 8,
    "التاسع": 9, "التاسعة": 9, "تاسع": 9, "تاسعة": 9,
    "العاشر": 10, "العاشرة": 10, "عاشر": 10, "عاشرة": 10,
    "الحادي عشر": 11, "الثاني عشر": 12, "الثالث عشر": 13, "الرابع عشر": 14, "الخامس عشر": 15
}

def parse_season_num(title: str) -> int:
    """Parses season number from Arabic/English title string."""
    m = re.search(r'(?:موسم|الموسم)\s+([\u0600-\u06FF\w\d]+)', title)
    if m:
        val = m.group(1).strip()
        if val.isdigit():
            return int(val)
        if val in ARABIC_NUMBERS:
            return ARABIC_NUMBERS[val]
            
    m = re.search(r'(\d+)(?:st|nd|rd|th)?\s+Season', title, re.IGNORECASE)
    if m:
        return int(m.group(1))
        
    m = re.search(r'Season\s+(\d+)', title, re.IGNORECASE)
    if m:
        return int(m.group(1))
        
    return 1 # Default to Season 1

def parse_episode_num(title: str) -> int:
    """Parses episode number from Arabic title string."""
    m = re.search(r'(?:الحلقة|حلقة)\s+(\d+)', title)
    if m:
        return int(m.group(1))
        
    m = re.search(r'(?:الحلقة|حلقة)\s+([\u0600-\u06FF]+)', title)
    if m:
        val = m.group(1).strip()
        if val in ARABIC_NUMBERS:
            return ARABIC_NUMBERS[val]
            
    m = re.search(r'الحلقة\s+(\d+)\s+والاخيرة', title)
    if m:
        return int(m.group(1))
        
    # General last resort: look for lonely digits
    m = re.search(r'\b(\d+)\b', title)
    if m:
        return int(m.group(1))
        
    return 1 # Default to Episode 1

def clean_for_search(title: str) -> str:
    """Cleans up Cinemana title to base name for ArabSeed searches and dynamic grouping."""
    t = title
    
    # 1. Lowercase to normalize English titles
    t = t.lower()
    
    # 2. Remove year inside parentheses or brackets, e.g., (2017) or [2020]
    t = re.sub(r'[\(\[\{]\s*\d{4}\s*[\)\]\}]', '', t)
    # Also bare year at the end, e.g., " 2017"
    t = re.sub(r'\b\d{4}\b', '', t)
    
    # 3. Remove Season patterns in English and Arabic:
    # Arabic: الموسم الاول, الموسم الثاني, الموسم 2, موسم 02
    t = re.sub(r'(?:الموسم|موسم)\s+(?:الاول|الأول|الأولى|الاولى|الاولي|اول|أول|الثاني|الثانية|ثاني|ثانية|الثالث|الثالثة|ثالث|ثالثة|الرابع|الرابعة|رابع|رابعة|الخامس|الخامسة|خامس|خامسة|السادس|السادسة|سادس|سادسة|السابع|السابعة|سابع|سابعة|الثامن|الثامنة|ثامن|ثامنة|التاسع|التاسعة|تاسع|تاسعة|العاشر|العاشرة|عاشر|عاشرة|[\u0600-\u06FF\w\d]+)', '', t)
    # English: Season 1, Season 02, S1, S02, S 2, 4th Season, etc.
    t = re.sub(r'\b(?:season|seasons)\s+\d+\b', '', t)
    t = re.sub(r'\b\d+(?:st|nd|rd|th)\s+season\b', '', t)
    t = re.sub(r'\bs\d+\b', '', t)
    
    # 4. Remove Episode patterns in Arabic and English:
    # Arabic: الحلقة 10, حلقة 5, الحلقة العاشرة, الاخيرة, والأخيرة (supporting both teh marbuta and heh)
    t = re.sub(r'(?:الحلقة|الحلقه|حلقة|حلقه)\s+(?:[\u0600-\u06FF\d]+)', '', t)
    t = re.sub(r'\b(?:والاخيرة|والأخيرة|والأخيره|والاخيره|الأخيرة|الاخيرة|الأخيره|الاخيره|اخيرة|أخيرة|أخيره|اخيره)\b', '', t)
    # English: Episode 10, Ep 5, Ep05, E10, E 10, etc.
    t = re.sub(r'\b(?:episode|episodes|ep|e)\s*\d+\b', '', t)
    
    # 5. Remove standard badges/quality/translation words (supporting teh marbuta and heh)
    t = re.sub(r'\b(?:مترجم|مترجمه|مترجمة|مدبلج|مدبلجه|مدبلجة|بلوراي|كامل|كامله|كاملة|HD|FHD|WEB-DL|وب-دل|وب\s+دل|برابط\s+واحد|نسخة|تحميل|مشاهدة|اون\s+لاين|اونلاين)\b', '', t)
    
    # 6. Remove leading prefixes (loop to strip nested prefixes like "مسلسل حلقة")
    while True:
        new_t = re.sub(r'^(?:فيلم|مسلسل|أنمي|انمي|اونا|كرتون|برنامج|مسرحية|حلقة|حلقه)\s+', '', t)
        if new_t == t:
            break
        t = new_t
    
    # 7. Clean up non-word characters and punctuation
    t = re.sub(r'[-\s/|–\.,:\?!\(\)\[\]\{\}_]+', ' ', t)
    
    # 8. Strip spaces and multiple spaces
    t = re.sub(r'\s+', ' ', t).strip()
    
    return t

def clean_display_title(title: str, r_type: str) -> str:
    """Creates a beautiful clean title for series/movies on their display cards."""
    if r_type == 'فيلم':
        return title
        
    cleaned = clean_for_search(title)
    
    # Capitalize English words nicely
    words = cleaned.split(' ')
    capitalized_words = []
    for w in words:
        if w.isascii() and w.isalpha():
            capitalized_words.append(w.capitalize())
        else:
            capitalized_words.append(w)
    base_title = ' '.join(capitalized_words)
    
    # Prepend 'مسلسل' if not already present
    if r_type == 'مسلسل' and not base_title.startswith('مسلسل'):
        return f"مسلسل {base_title}"
    return base_title

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

def resolve_cinemana_stream(cinemana_url: str) -> list:
    """
    Scrapes the Cinemana watch page, calls their Server.php AJAX endpoint,
    and returns their direct HLS stream proxied via stream.php.
    """
    try:
        post_id = cinemana_url
        if 'watch=' in cinemana_url:
            m = re.search(r'watch=(\d+)', cinemana_url)
            if m:
                post_id = m.group(1)
                
        ajax_url = "https://cinemana.cc/wp-content/themes/EEE/Inc/Ajax/Single/Server.php"
        data = {
            'post_id': post_id,
            'server': '0'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': f"https://cinemana.cc/watch={post_id}/"
        }
        
        print(f"Direct Cinemana stream resolution for post {post_id}...")
        r = requests.post(ajax_url, data=data, headers=headers, timeout=15)
        if r.status_code == 200:
            match = re.search(r'const\s+originalUrls\s*=\s*({[^}]+})', r.text)
            if match:
                urls_str = match.group(1)
                parsed_urls = {}
                url_matches = re.findall(r'["\']?(\w+)["\']?\s*:\s*["\']([^"\']+)["\']', urls_str)
                for k, v in url_matches:
                    parsed_urls[k] = v
                    
                formatted_players = []
                # Sort qualities so highest (e.g. 1080) appears first
                sorted_qualities = sorted(parsed_urls.keys(), key=lambda x: int(x) if x.isdigit() else 0, reverse=True)
                for q in sorted_qualities:
                    orig_url = parsed_urls[q]
                    # Route via root stream.php which is the working Cinemana endpoint
                    cinemana_stream_url = f"https://cinemana.cc/stream.php?session={post_id}&url={urllib.parse.quote(orig_url)}"
                    # Wrap in our own /api/stream proxy to solve CORS and segment rewrite
                    proxied_url = f"/api/stream?url={urllib.parse.quote(cinemana_stream_url)}"
                    
                    formatted_players.append({
                        'type': 'direct',
                        'server': f'✨ سيرفر مباشر {q}p (خالٍ من الإعلانات)',
                        'url': proxied_url,
                        'original_url': orig_url
                    })
                return formatted_players
        else:
            print(f"Cinemana Server.php returned status {r.status_code}")
            
    except Exception as e:
        print(f"Error resolving direct Cinemana stream: {e}")
        
    return []

@app.route('/')
def home():
    """Renders the main single page web interface."""
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    """
    Searches Cinemana for movies/series or routes directly to homepage categories
    and specific movies/series grids, with dynamic deduplication for series.
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Search query is required.'}), 400
        
    try:
        if query == '__home__':
            # Retrieve beautiful horizontal categorized carousels directly from Cinemana
            categories = cinemana_api.get_homepage_categories()
            # Deduplicate series episodes in home carousels
            for cat in categories:
                deduped_cards = []
                seen_bases = set()
                for r in cat.get('cards', []):
                    title = r.get('title', '')
                    r_type = r.get('type', 'فيلم')
                    is_special = "special" in title.lower() or "سبيشال" in title or "خاص" in title or "فيلم" in title
                    if not is_special and (r_type == 'مسلسل' or any(x in title for x in ["مسلسل", "الحلقة", "الحلقه", "حلقة", "حلقه", "الموسم"])):
                        base = clean_for_search(title).lower().strip()
                        if base in seen_bases:
                            continue
                        seen_bases.add(base)
                        r['title'] = clean_display_title(title, 'مسلسل')
                        r['type'] = 'مسلسل'
                    deduped_cards.append(r)
                cat['cards'] = deduped_cards
            return jsonify({
                'categories': categories,
                'category': 'الرئيسية'
            })
        elif query == '__movies__':
            results = cinemana_api.scrape_listing_page("https://cinemana.cc/movies/")
            return jsonify({
                'results': results,
                'category': 'الأفلام'
            })
        elif query == '__series__':
            results = cinemana_api.scrape_listing_page("https://cinemana.cc/series/")
            # Deduplicate episodes in series catalog
            deduped_results = []
            seen_bases = set()
            for r in results:
                title = r.get('title', '')
                base = clean_for_search(title).lower().strip()
                if base in seen_bases:
                    continue
                seen_bases.add(base)
                r['title'] = clean_display_title(title, 'مسلسل')
                r['type'] = 'مسلسل'
                deduped_results.append(r)
            return jsonify({
                'results': deduped_results,
                'category': 'المسلسلات'
            })
        elif query == '__anime__':
            # Scrape عالم الأنمي by pulling its categorised results
            results = cinemana_api.scrape_listing_page("https://cinemana.cc/watch=category/%D8%A3%D9%86%D9%85%D9%8I-%D9%88%D8%A3%D9%83%D8%B4%D9%86/")
            # Deduplicate episodes in anime catalog
            deduped_results = []
            seen_bases = set()
            for r in results:
                title = r.get('title', '')
                base = clean_for_search(title).lower().strip()
                if base in seen_bases:
                    continue
                seen_bases.add(base)
                r['title'] = clean_display_title(title, 'مسلسل')
                r['type'] = 'مسلسل'
                deduped_results.append(r)
            return jsonify({
                'results': deduped_results,
                'category': 'عالم الأنمي'
            })
        else:
            # Standard search directly from Cinemana.cc
            results = cinemana_api.search(query)
            # Deduplicate episodes in search results
            deduped_results = []
            seen_bases = set()
            for r in results:
                title = r.get('title', '')
                r_type = r.get('type', 'فيلم')
                is_special = "special" in title.lower() or "سبيشال" in title or "خاص" in title or "فيلم" in title
                if not is_special and (r_type == 'مسلسل' or any(x in title for x in ["مسلسل", "الحلقة", "الحلقه", "حلقة", "حلقه", "الموسم"])):
                    base = clean_for_search(title).lower().strip()
                    if base in seen_bases:
                        continue
                    seen_bases.add(base)
                    r['title'] = clean_display_title(title, 'مسلسل')
                    r['type'] = 'مسلسل'
                deduped_results.append(r)
            return jsonify({
                'results': deduped_results,
                'category': f"البحث عن: {query}"
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/details')
def api_details():
    """Fetches stories, seasons, and episodes from Cinemana's details page."""
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL is required.'}), 400
        
    try:
        details = cinemana_api.get_details(url)
        return jsonify(details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watch')
def api_watch():
    """
    Direct Cinemana stream playback. Resolves Cinemana watch URL
    directly to HLS streams and returns them.
    """
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL is required.'}), 400
        
    try:
        servers = resolve_cinemana_stream(url)
        if not servers:
            return jsonify({
                'servers': [{
                    'type': 'direct',
                    'server': '⚠️ عذراً، هذا العرض غير متوفر حالياً للبث المباشر',
                    'url': 'about:blank'
                }]
            })
        return jsonify({'servers': servers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream', methods=['GET', 'OPTIONS'])
def api_stream_proxy():
    """
    Transparent chunked-streaming proxy supporting HTTP Range requests, CORS,
    and recursive HLS (.m3u8) playlist URL rewriting to force all segment loads through proxy.
    """
    # Gracefully handle CORS preflight requests
    if request.method == 'OPTIONS':
        resp = Response()
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Headers'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        return resp
        
    video_url = request.args.get('url', '').strip()
    if not video_url:
        return "Video URL parameter is required", 400
        
    video_url = urllib.parse.unquote(video_url)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://cinemana.cc/'
    }
    
    range_header = request.headers.get('Range')
    if range_header:
        headers['Range'] = range_header
        
    try:
        # We fetch stream.php or direct ts segment using stream=True
        r = requests.get(video_url, headers=headers, stream=True, timeout=20)
        
        # Check if the resource is an HLS playlist (.m3u8) by checking headers or content structure
        content_type = r.headers.get('Content-Type', '').lower()
        is_m3u8 = 'mpegurl' in content_type or 'm3u8' in video_url.lower() or 'playlist.m3u8' in video_url.lower()
        
        # Read the small playlist body in memory to rewrite it
        if is_m3u8 or 'application/octet-stream' in content_type:
            content = r.content
            try:
                # Decode to string (taking care of UTF-8 BOM)
                text_content = content.decode('utf-8-sig')
                if text_content.strip().startswith('#EXTM3U'):
                    lines = text_content.split('\n')
                    rewritten_lines = []
                    scheme = request.scheme
                    host = request.host
                    
                    for line in lines:
                        line_stripped = line.strip()
                        if not line_stripped:
                            rewritten_lines.append('')
                            continue
                        if line_stripped.startswith('#'):
                            # Rewrite URI paths in EXT-X-KEY encryption tags if they point to stream.php
                            if 'URI=' in line_stripped:
                                m = re.search(r'URI=["\']([^"\']+)["\']', line_stripped)
                                if m:
                                    key_uri = m.group(1)
                                    if key_uri.startswith('stream.php'):
                                        abs_key_url = "https://cinemana.cc/" + key_uri
                                    else:
                                        abs_key_url = key_uri
                                    proxied_key_url = f"{scheme}://{host}/api/stream?url={urllib.parse.quote(abs_key_url)}"
                                    line_stripped = line_stripped.replace(key_uri, proxied_key_url)
                            rewritten_lines.append(line_stripped)
                        else:
                            # It's a segment or sub-playlist URL
                            if line_stripped.startswith('stream.php'):
                                abs_segment_url = "https://cinemana.cc/" + line_stripped
                            else:
                                abs_segment_url = line_stripped
                            
                            proxied_segment_url = f"{scheme}://{host}/api/stream?url={urllib.parse.quote(abs_segment_url)}"
                            rewritten_lines.append(proxied_segment_url)
                            
                    rewritten_content = '\n'.join(rewritten_lines)
                    
                    resp = Response(rewritten_content, status=200, content_type='application/vnd.apple.mpegurl')
                    resp.headers['Access-Control-Allow-Origin'] = '*'
                    resp.headers['Access-Control-Allow-Headers'] = '*'
                    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
                    return resp
            except Exception as decode_err:
                print(f"Decoding HLS playlist failed, falling back to direct stream: {decode_err}")
                
        # Pipe binary .ts segment or standard file chunk streaming
        def generate():
            try:
                for chunk in r.iter_content(chunk_size=131072):
                    if chunk:
                        yield chunk
            except Exception as e:
                print(f"Streaming Proxy Interrupted: {e}")
                
        excluded_headers = ['connection', 'transfer-encoding', 'keep-alive', 'content-encoding']
        resp_headers = []
        for name, value in r.headers.items():
            if name.lower() not in excluded_headers:
                resp_headers.append((name, value))
                
        # Inject CORS headers for dynamic web clients
        resp_headers.append(('Access-Control-Allow-Origin', '*'))
        resp_headers.append(('Access-Control-Allow-Headers', '*'))
        resp_headers.append(('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'))
        
        return Response(generate(), status=r.status_code, headers=resp_headers)
    except Exception as e:
        return f"Streaming Proxy Error: {e}", 502

if __name__ == '__main__':
    print("=" * 65)
    print(" 🚀 AleX CINEMA - PREMIUM AD-FREE PORTAL STARTING...")
    print(" Scrape source: cinemana.cc (Main)")
    print(" Running at http://127.0.0.1:5000")
    print("=" * 65)
    app.run(host='0.0.0.0', port=5000, debug=True)

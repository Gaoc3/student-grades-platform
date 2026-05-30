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
    """Cleans up Cinemana title to base name for ArabSeed searches."""
    t = title
    # Remove Season and Episode details
    t = re.sub(r'الموسم\s+[\u0600-\u06FF\w\d]+', '', t)
    t = re.sub(r'(?:الحلقة|حلقة)\s+[\u0600-\u06FF\d]+', '', t)
    t = re.sub(r'والاخيرة', '', t)
    t = re.sub(r'والأخيرة', '', t)
    # Remove standard quality/translation badges
    t = re.sub(r'\b(?:مترجم|مترجمة|مدبلج|مدبلجة|بلوراي|كامل|كاملة|HD|FHD|WEB-DL|وب-دل|4th Season)\b', '', t, flags=re.IGNORECASE)
    # Remove leading prefixes
    t = re.sub(r'^(?:فيلم|مسلسل|أنمي|انمي|اونا)\s+', '', t).strip()
    # Clean punctuation
    t = re.sub(r'[-\s/|–]+', ' ', t).strip()
    return t

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

def resolve_hybrid_stream(cinemana_url: str) -> list:
    """
    Takes a Cinemana watch page URL, scrapes its details/title,
    searches ArabSeed for the matching item, resolves the correct
    season/episode, and extracts the direct 1080p ad-free stream.
    """
    try:
        # 1. Scrape details from Cinemana
        details = cinemana_api.get_details(cinemana_url)
        cinemana_title = details.get('title', '')
        is_series = details.get('is_series', False)
        
        print(f"Hybrid Resolving: '{cinemana_title}' (Series: {is_series})")
        
        # 2. Clean title for searching ArabSeed
        season_num = 1
        ep_num = 1
        
        if is_series and details.get('seasons'):
            for s in details['seasons']:
                for ep in s.get('episodes', []):
                    if ep.get('active'):
                        season_num = parse_season_num(s.get('title', ''))
                        ep_num = parse_episode_num(ep.get('title', ''))
                        break
        else:
            season_num = parse_season_num(cinemana_title)
            ep_num = parse_episode_num(cinemana_title)
        
        # Clean title to base name
        base_title = clean_for_search(cinemana_title)
        print(f"Cleaned search keyword: '{base_title}', Season: {season_num}, Episode: {ep_num}")
        
        # 3. Search ArabSeed
        api.auto_fallback_mirror()
        results = api.search(base_title)
        if not results and len(base_title.split()) > 2:
            # Fallback: search just first 2 words
            short_title = " ".join(base_title.split()[:2])
            print(f"No results. Retrying with shorter keyword: '{short_title}'")
            results = api.search(short_title)
            
        if not results:
            print("No matching title found on ArabSeed.")
            return []
            
        target_url = ""
        
        if is_series:
            # Look for the matching season page on ArabSeed
            matched_season_url = ""
            for r in results:
                r_title = r.get('title', '')
                r_type = r.get('type', 'فيلم')
                
                is_r_series = "مسلسل" in r_title or "حلقة" in r_title or "الموسم" in r_title or "مسلسل" in r_type.lower()
                if not is_r_series:
                    continue
                    
                r_season = parse_season_num(r_title)
                if r_season == season_num:
                    matched_season_url = r.get('url', '')
                    print(f"Matched ArabSeed Season {season_num} page: {r_title} -> {matched_season_url}")
                    break
                    
            if not matched_season_url:
                # Fallback to first available series page in results
                for r in results:
                    if "مسلسل" in r.get('title', '') or "حلقة" in r.get('title', ''):
                        matched_season_url = r.get('url', '')
                        print(f"Fallback to first available ArabSeed series page: {r.get('title')} -> {matched_season_url}")
                        break
                        
            if matched_season_url:
                as_details = api.get_details(matched_season_url)
                if as_details.get('is_series') and as_details.get('episodes'):
                    # Match the exact episode
                    matched_ep_url = ""
                    for ep in as_details['episodes']:
                        ep_title = ep.get('title', '')
                        as_ep_num = parse_episode_num(ep_title)
                        if as_ep_num == ep_num:
                            matched_ep_url = ep.get('url', '')
                            print(f"Matched ArabSeed Episode {ep_num} URL: {ep_title} -> {matched_ep_url}")
                            break
                            
                    if not matched_ep_url:
                        # Fallback to the active or first episode
                        for ep in as_details['episodes']:
                            if ep.get('active') or not matched_ep_url:
                                matched_ep_url = ep.get('url', '')
                                
                    if matched_ep_url:
                        target_url = matched_ep_url
        else:
            # Movie: look for the closest movie title match on ArabSeed
            for r in results:
                r_type = r.get('type', 'فيلم')
                if "مسلسل" not in r.get('title', '') and "حلقة" not in r.get('title', '') and "مسلسل" not in r_type:
                    target_url = r.get('url', '')
                    print(f"Matched ArabSeed Movie URL: {r.get('title')} -> {target_url}")
                    break
            if not target_url:
                # Fallback to first result
                target_url = results[0].get('url', '')
                print(f"Movie fallback to first result: {results[0].get('title')} -> {target_url}")
                
        if not target_url:
            return []
            
        # 4. Extract direct player streams from the matched ArabSeed URL
        formatted_players = []
        
        # 4.1 Download links extraction (1080p direct reviewsrate)
        try:
            download_links = api.get_download_links(target_url)
            for dl in download_links:
                direct_link = dl.get('direct_link', '')
                quality = dl.get('quality', '')
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
                        break
        except Exception as dl_err:
            print(f"Error fetching download links in hybrid resolution: {dl_err}")
            
        # 4.2 Watch links extraction
        try:
            watch_links = api.get_watch_links(target_url)
            for idx, wl in enumerate(watch_links):
                direct_link = wl.get('direct_link', '')
                server_name = wl.get('server', f'سيرفر {idx+1}')
                
                if 'reviewrate.net' in direct_link or 'play.php' in direct_link:
                    cdn_url = extract_direct_mp4(direct_link)
                    if cdn_url:
                        encoded_cdn = urllib.parse.quote(cdn_url)
                        formatted_players.append({
                            'type': 'direct',
                            'server': f'✨ {server_name} (خالٍ من الإعلانات)',
                            'url': f'/api/stream?url={encoded_cdn}',
                            'original_url': cdn_url
                        })
                        continue
                
                formatted_players.append({
                    'type': 'iframe',
                    'server': server_name,
                    'url': direct_link
                })
        except Exception as wl_err:
            print(f"Error fetching watch links in hybrid resolution: {wl_err}")
            
        return formatted_players
        
    except Exception as e:
        print(f"Error resolving hybrid stream for {cinemana_url}: {e}")
        return []

@app.route('/')
def home():
    """Renders the main single page web interface."""
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    """
    Searches Cinemana for movies/series or routes directly to homepage categories
    and specific movies/series grids.
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Search query is required.'}), 400
        
    try:
        if query == '__home__':
            # Retrieve beautiful horizontal categorized carousels directly from Cinemana
            categories = cinemana_api.get_homepage_categories()
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
            return jsonify({
                'results': results,
                'category': 'المسلسلات'
            })
        elif query == '__anime__':
            # Scrape عالم الأنمي by pulling its categorised results
            results = cinemana_api.scrape_listing_page("https://cinemana.cc/watch=category/%D8%A3%D9%86%D9%85%D9%8A-%D9%88%D8%A3%D9%83%D8%B4%D9%86/")
            return jsonify({
                'results': results,
                'category': 'عالم الأنمي'
            })
        else:
            # Standard search directly from Cinemana.cc
            results = cinemana_api.search(query)
            return jsonify({
                'results': results,
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
    Transparent Hybrid stream playback matching. Resolves Cinemana
    title to Arabseed servers and returns direct streams.
    """
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL is required.'}), 400
        
    try:
        servers = resolve_hybrid_stream(url)
        if not servers:
            return jsonify({
                'servers': [{
                    'type': 'iframe',
                    'server': '⚠️ عذراً، لم نجد مصادر بث مطابقة حالياً (العرض في وضع الصيانة)',
                    'url': 'about:blank'
                }]
            })
        return jsonify({'servers': servers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream')
def api_stream_proxy():
    """
    Transparent chunked-streaming proxy supporting HTTP Range requests.
    Pipes video chunks directly to bypass Nginx hotlink protections.
    """
    video_url = request.args.get('url', '').strip()
    if not video_url:
        return "Video URL parameter is required", 400
        
    video_url = urllib.parse.unquote(video_url)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://m.reviewrate.net/'
    }
    
    range_header = request.headers.get('Range')
    if range_header:
        headers['Range'] = range_header
        
    try:
        r = requests.get(video_url, headers=headers, stream=True, timeout=20)
        
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
                
        return Response(generate(), status=r.status_code, headers=resp_headers)
    except Exception as e:
        return f"Streaming Proxy Error: {e}", 502

if __name__ == '__main__':
    print("=" * 65)
    print(" 🚀 AleX CINEMA - PREMIUM AD-FREE PORTAL STARTING...")
    print(" Scrape sources: cinemana.cc (Main) | arabseed.show (Hybrid Match)")
    print(" Running at http://0.0.0.0:5000")
    print("=" * 65)
    app.run(host='0.0.0.0', port=5000, debug=True)

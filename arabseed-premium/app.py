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

@app.route('/')
def index():
    return render_template('index.html')

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
        r = requests.get(embed_url, headers=headers, timeout=15)
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
                
        watch_url = f"https://cinemana.cc/watch={post_id}/"
        ajax_url = "https://cinemana.cc/wp-content/themes/EEE/Inc/Ajax/Single/Server.php"
        data = {
            'post_id': post_id,
            'server': '0'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': watch_url
        }
        
        print(f"Direct Cinemana stream resolution for post {post_id}...")
        
        # Use persistent Session to hit watch page first (establishes Cinemana session/cookies)
        session = requests.Session()
        session.headers.update(headers)
        
        # Hit watch page
        session.get(watch_url, timeout=10)
        
        # POST to Server.php
        r = session.post(ajax_url, data=data, timeout=15)
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

def resolve_arabseed_stream(title: str, is_series: bool, season_str: str, episode_str: str) -> list:
    """
    Searches ArabSeed for the matching movie or series episode,
    extracts high-speed watch servers, and decodes direct MP4 links if possible.
    """
    if not title:
        return []
        
    print(f"🔄 Hybrid Resolver: Searching ArabSeed for title='{title}', is_series={is_series}, season='{season_str}', episode='{episode_str}'...")
    
    try:
        # Initialize ArabSeedAPI client dynamically to use updated mirror logic
        from arabseed_scraper import ArabSeedAPI
        arabseed_api = ArabSeedAPI()
        
        # Check connectivity and get working mirror
        if not arabseed_api.auto_fallback_mirror():
            print("❌ Hybrid Resolver: Failed to connect to any ArabSeed mirrors.")
            return []
            
        base_title = clean_for_search(title)
        results = arabseed_api.search(base_title)
        if not results:
            print(f"⚠️ Hybrid Resolver: No search results found on ArabSeed for '{base_title}'.")
            return []
            
        target_url = ""
        
        if is_series:
            target_season = parse_season_num(season_str)
            target_episode = parse_episode_num(episode_str)
            
            for r in results:
                r_title = r.get('title', '')
                r_type = r.get('type', '')
                
                # Verify if this is a series or anime
                is_r_series = "مسلسل" in r_title or "انمي" in r_title or "مسلسل" in r_type.lower() or "أنمي" in r_type.lower()
                if not is_r_series:
                    continue
                    
                r_season = parse_season_num(r_title)
                if r_season == target_season:
                    # Found matching series season! Fetch episodes list
                    try:
                        details = arabseed_api.get_details(r['url'])
                        if details.get('is_series'):
                            for ep in details.get('episodes', []):
                                ep_num = parse_episode_num(ep['title'])
                                if ep_num == target_episode:
                                    target_url = ep['url']
                                    print(f"✅ Hybrid Resolver: Matched episode page -> {target_url}")
                                    break
                        if target_url:
                            break
                    except Exception as details_err:
                        print(f"❌ Hybrid Resolver: Error fetching series details for {r_title}: {details_err}")
        else:
            # Movie match
            for r in results:
                r_title = r.get('title', '')
                r_type = r.get('type', '')
                is_r_series = "مسلسل" in r_title or "حلقة" in r_title or "مسلسل" in r_type.lower() or "أنمي" in r_type.lower()
                if is_r_series:
                    continue
                
                target_url = r['url']
                print(f"✅ Hybrid Resolver: Matched movie page -> {target_url}")
                break
                
        if not target_url:
            print("⚠️ Hybrid Resolver: Failed to match any items on ArabSeed.")
            return []
            
        # Get watch links from ArabSeed target watch page
        watch_servers = arabseed_api.get_watch_links(target_url)
        formatted_servers = []
        
        for idx, w in enumerate(watch_servers):
            server_name = w.get('server', f'سيرفر مشاهدة {idx+1}')
            direct_link = w.get('direct_link', '')
            if not direct_link or direct_link == 'about:blank':
                continue
                
            # If it's a reviewrate embed, try to extract the direct MP4
            if "reviewrate.net" in direct_link:
                try:
                    print(f"🔓 Hybrid Resolver: Attempting to extract direct MP4 from {direct_link}...")
                    mp4_url = extract_direct_mp4(direct_link)
                    if mp4_url:
                        print(f"🚀 Hybrid Resolver: Successfully extracted direct MP4 URL -> {mp4_url}")
                        proxied_mp4_url = f"/api/stream?url={urllib.parse.quote(mp4_url)}"
                        formatted_servers.append({
                            'type': 'direct',
                            'server': f'🚀 سيرفر عرب سيد السريع 1080p (خالٍ من التقطيع)',
                            'url': proxied_mp4_url,
                            'original_url': direct_link
                        })
                        continue
                except Exception as extract_err:
                    print(f"❌ Hybrid Resolver: Error extracting direct MP4: {extract_err}")
            
            # Fallback as embed iframe player
            formatted_servers.append({
                'type': 'embed',
                'server': f'🚀 سيرفر عرب سيد البديل {server_name} (جودة عالية)',
                'url': direct_link,
                'original_url': direct_link
            })
            
        return formatted_servers
        
    except Exception as e:
        print(f"❌ Hybrid Resolver Error: {e}")
        return []

# ============================================================================
# Caching System (Thread-Safe Memory Cache)
# ============================================================================
import time
import threading
from threading import Lock
import concurrent.futures

class SimpleCache:
    def __init__(self, default_ttl=300):
        self.cache = {}
        self.default_ttl = default_ttl
        self.lock = Lock()
        
    def get(self, key):
        with self.lock:
            if key in self.cache:
                val, expiry = self.cache[key]
                if time.time() < expiry:
                    return val
                else:
                    del self.cache[key]
            return None
            
    def set(self, key, value, ttl=None):
        with self.lock:
            t = ttl if ttl is not None else self.default_ttl
            self.cache[key] = (value, time.time() + t)

    def clear(self):
        """Flushes all cached entries from memory."""
        with self.lock:
            self.cache.clear()

app_cache = SimpleCache()

def normalize_arabic(text: str) -> str:
    """Normalizes Arabic letters to standard forms for robust searching."""
    t = text.lower()
    t = re.sub(r'[أإآ]', 'ا', t)
    t = re.sub(r'[ة]', 'ه', t)
    t = re.sub(r'[ى]', 'ي', t)
    t = re.sub(r'[\u064B-\u065F]', '', t)  # Remove diacritics
    t = re.sub(r'[-\s/|–\.,:\?!\(\)\[\]\{\}_]+', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def calculate_match_score(item_title: str, query: str) -> int:
    """Calculates a relevance matching score between search query and item title."""
    norm_query = normalize_arabic(query)
    norm_title = normalize_arabic(item_title)
    norm_base = normalize_arabic(clean_for_search(item_title))
    
    if norm_base == norm_query:
        return 100
    if norm_title == norm_query:
        return 95
    if norm_base.startswith(norm_query):
        return 85
    if norm_title.startswith(norm_query):
        return 80
    if norm_query in norm_base:
        return 70
    if norm_query in norm_title:
        return 65
        
    query_words = set(norm_query.split())
    title_words = set(norm_title.split())
    matching_words = query_words.intersection(title_words)
    if matching_words:
        return 10 + len(matching_words) * 10
        
    return 0

def fetch_slide_title(slide, session):
    """Fetches the watch page to extract the actual title of the slide.
    For series, cleans the title and resolves the base series URL (first episode)
    so the detail modal opens the full series view with all seasons/episodes."""
    try:
        r = session.get(slide['url'], timeout=6)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            title_el = soup.find('h1') or soup.find('h2') or soup.title
            if title_el:
                title = title_el.get_text(strip=True)
                title = title.replace("– افلام ومسلسلات | قنوات بث", "").replace("سينمانا شبكتي ⭐️", "").strip()
                
                is_special = "special" in title.lower() or "سبيشال" in title or "خاص" in title or "فيلم" in title
                is_series = False
                if not is_special:
                    if any(x in title for x in ["مسلسل", "حلقة", "حلقه", "الحلقة", "الحلقه", "الموسم"]) or "انمي" in title.lower() or "أنمي" in title:
                        is_series = True
                
                if is_series:
                    slide['type'] = "مسلسل"
                    # Clean the title: remove episode/season info for a beautiful base series name
                    slide['title'] = clean_display_title(title, 'مسلسل')
                    
                    # Smart resolution: find the first episode of the first season
                    # so the modal opens the full series view instead of a single episode
                    try:
                        season_triggers = soup.find_all(class_='season-trigger')
                        season_wrappers = soup.find_all(class_='season-wrapper')
                        if season_triggers and len(season_triggers) == len(season_wrappers):
                            # Find the first episode of the first season
                            first_wrapper = season_wrappers[0]
                            ep_anchors = first_wrapper.find_all('a', href=True)
                            first_ep_url = None
                            first_ep_num = float('inf')
                            for a in ep_anchors:
                                if 'watch=' in a['href']:
                                    ep_text = a.get_text(strip=True)
                                    ep_match = re.search(r'\d+', ep_text)
                                    ep_num = int(ep_match.group()) if ep_match else 9999
                                    if ep_num < first_ep_num:
                                        first_ep_num = ep_num
                                        ep_href = a['href']
                                        if ep_href.startswith('/'):
                                            ep_href = "https://cinemana.cc" + ep_href
                                        first_ep_url = ep_href
                            if first_ep_url:
                                slide['url'] = first_ep_url
                    except Exception as base_err:
                        print(f"Error resolving base series URL: {base_err}")
                else:
                    slide['title'] = title
    except Exception as e:
        print(f"Error fetching slide title: {e}")

@app.route('/api/cache/clear')
def api_cache_clear():
    """Manually flushes and triggers background pre-warming of the cache."""
    app_cache.clear()
    # Trigger an immediate background warm thread without blocking the response!
    threading.Thread(target=trigger_single_warm, daemon=True).start()
    return jsonify({
        'status': 'success',
        'message': 'تم تحديث وتطهير ذاكرة التخزين المؤقت (Cache) بالكامل بنجاح! جاري جلب البيانات بالخلفية...'
    })

def get_home_data_fresh():
    """Fetch home categories and slides synchronously."""
    try:
        categories = cinemana_api.get_homepage_categories()
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
            
        slides = []
        try:
            r_main = cinemana_api.session.get("https://cinemana.cc/main/", timeout=8)
            if r_main.status_code == 200:
                soup_main = BeautifulSoup(r_main.text, 'html.parser')
                carousel = soup_main.find('div', class_='HeroCarousel')
                if carousel:
                    slide_items = carousel.find_all('div', class_='HeroSlideItem')
                    for s in slide_items[:5]:
                        a = s.find('a', href=True)
                        href = a['href'] if a else ""
                        if href.startswith('/'):
                            href = "https://cinemana.cc" + href
                        bg_image = ""
                        bg_div = s.find('div', style=True)
                        if bg_div:
                            style = bg_div.get('style', '')
                            m = re.search(r"url\(['\"]?([^'\")]+)['\"]?\)", style)
                            if m:
                                bg_image = m.group(1)
                        
                        slides.append({
                            "url": href,
                            "poster": bg_image,
                            "title": "عرض حصري مميز",
                            "type": "فيلم",
                            "rating": "8.5",
                            "quality": "1080p FHD"
                        })
                        
                    if slides:
                        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                            executor.map(lambda s: fetch_slide_title(s, cinemana_api.session), slides)
        except Exception as slide_err:
            print(f"Error scraping hero slides: {slide_err}")
            
        res = {
            'categories': categories,
            'slides': slides,
            'category': 'الرئيسية'
        }
        
        if categories or slides:
            app_cache.set("home_data", res, ttl=1800)
        return res
    except Exception as e:
        print(f"Error getting fresh home data: {e}")
        return {'categories': [], 'slides': [], 'category': 'الرئيسية'}

def get_movies_data_fresh():
    """Fetch pages 1-4 in parallel for movies listing."""
    try:
        urls = [f"https://cinemana.cc/movies/page/{p}/" for p in [1, 2, 3, 4]]
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(cinemana_api.scrape_listing_page, url): url for url in urls}
            for f in concurrent.futures.as_completed(futures):
                try:
                    page_results = f.result()
                    for r in page_results:
                        if not any(x['url'] == r['url'] for x in results):
                            results.append(r)
                except Exception as e:
                    print(f"Error parallel scraping movies: {e}")
                    
        res = {
            'results': results,
            'category': 'الأفلام'
        }
        if results:
            app_cache.set("movies_data", res, ttl=1200)
        return res
    except Exception as e:
        print(f"Error getting fresh movies data: {e}")
        return {'results': [], 'category': 'الأفلام'}

def get_series_data_fresh():
    """Fetch pages 1-4 in parallel and deduplicate for series listing."""
    try:
        urls = [f"https://cinemana.cc/series/page/{p}/" for p in [1, 2, 3, 4]]
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(cinemana_api.scrape_listing_page, url): url for url in urls}
            for f in concurrent.futures.as_completed(futures):
                try:
                    page_results = f.result()
                    for r in page_results:
                        if not any(x['url'] == r['url'] for x in results):
                            results.append(r)
                except Exception as e:
                    print(f"Error parallel scraping series: {e}")
                    
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
            
        res = {
            'results': deduped_results,
            'category': 'المسلسلات'
        }
        if deduped_results:
            app_cache.set("series_data", res, ttl=1200)
        return res
    except Exception as e:
        print(f"Error getting fresh series data: {e}")
        return {'results': [], 'category': 'المسلسلات'}

def get_anime_data_fresh():
    """Fetch pages 1-4 in parallel and deduplicate for anime listing."""
    try:
        urls = [f"https://cinemana.cc/watch=category/أنمي/page/{p}/" for p in [1, 2, 3, 4]]
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(cinemana_api.scrape_listing_page, url): url for url in urls}
            for f in concurrent.futures.as_completed(futures):
                try:
                    page_results = f.result()
                    for r in page_results:
                        if not any(x['url'] == r['url'] for x in results):
                            results.append(r)
                except Exception as e:
                    print(f"Error parallel scraping anime: {e}")
                    
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
            
        res = {
            'results': deduped_results,
            'category': 'عالم الأنمي'
        }
        if deduped_results:
            app_cache.set("anime_data", res, ttl=1200)
        return res
    except Exception as e:
        print(f"Error getting fresh anime data: {e}")
        return {'results': [], 'category': 'عالم الأنمي'}

def warm_caching_worker():
    """Continuous daemon background cache warmer executing every 10 minutes."""
    print("✨ Starting Background Cache Warmer...")
    # Warm immediately on startup!
    trigger_single_warm()
    while True:
        time.sleep(600)
        print("🔄 Pre-fetching and warming backend caches in background...")
        trigger_single_warm()

def trigger_single_warm():
    """Executes a single pre-warming pass across all dynamic cache elements."""
    try:
        get_home_data_fresh()
        get_movies_data_fresh()
        get_series_data_fresh()
        get_anime_data_fresh()
        print("✅ Background cache warming completed successfully!")
    except Exception as e:
        print(f"❌ Error during background cache warming: {e}")

@app.route('/api/home')
def api_home():
    """Retrieve beautiful horizontal categorized carousels and sliding featured Hero items."""
    cached_val = app_cache.get("home_data")
    if cached_val:
        return jsonify(cached_val)
    return jsonify(get_home_data_fresh())

@app.route('/api/movies')
def api_movies():
    """Scrapes pages 1-4 in parallel to expand movies library."""
    cached_val = app_cache.get("movies_data")
    if cached_val:
        return jsonify(cached_val)
    return jsonify(get_movies_data_fresh())

@app.route('/api/series')
def api_series():
    """Scrapes pages 1-4 in parallel and deduplicates series episodes."""
    cached_val = app_cache.get("series_data")
    if cached_val:
        return jsonify(cached_val)
    return jsonify(get_series_data_fresh())

@app.route('/api/anime')
def api_anime():
    """Scrapes pages 1-4 in parallel and deduplicates anime episodes."""
    cached_val = app_cache.get("anime_data")
    if cached_val:
        return jsonify(cached_val)
    return jsonify(get_anime_data_fresh())

@app.route('/api/search')
def api_search():
    """Searches Cinemana for query and ranks results intelligently using Arabic letter relevance."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Search query is required.'}), 400
        
    try:
        # Fallback for old endpoints if main.js is cached on client
        if query == '__home__':
            return api_home()
        elif query == '__movies__':
            return api_movies()
        elif query == '__series__':
            return api_series()
        elif query == '__anime__':
            return api_anime()
            
        cache_key = f"search_{query}"
        cached_val = app_cache.get(cache_key)
        if cached_val:
            return jsonify(cached_val)
            
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
            
        # Rank results intelligently based on relevance score
        scored_results = []
        for r in deduped_results:
            score = calculate_match_score(r['title'], query)
            scored_results.append((score, r))
            
        # Sort descending by score, maintaining stable order for equal scores
        scored_results.sort(key=lambda x: x[0], reverse=True)
        final_results = [item for score, item in scored_results]
        
        res = {
            'results': final_results,
            'category': f"البحث عن: {query}"
        }
        
        if final_results:
            app_cache.set(cache_key, res, ttl=300)
            
        return jsonify(res)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



def parse_episode_title(title):
    # Extract season number
    season_num = 1
    # Match "الموسم الأول", "الموسم 1", "الموسم الثاني", etc.
    season_match = re.search(r'(?:الموسم|موسم)\s+([^\s–]+|\d+)', title)
    if season_match:
        s_val = season_match.group(1).strip()
        arabic_numbers = {
            "الأول": 1, "الاول": 1, "الاولى": 1, "الأولى": 1,
            "الثاني": 2, "الثانية": 2,
            "الثالث": 3, "الثالثة": 3,
            "الرابع": 4, "الرابعة": 4,
            "الخامس": 5, "الخامسة": 5,
            "السادس": 6, "السادسة": 6,
            "السابع": 7, "السابعة": 7,
            "الثامن": 8, "الثامنة": 8,
            "التاسع": 9, "التاسعة": 9,
            "العاشر": 10, "العاشرة": 10
        }
        if s_val.isdigit():
            season_num = int(s_val)
        elif s_val in arabic_numbers:
            season_num = arabic_numbers[s_val]
            
    # Extract episode number
    ep_num = 1
    ep_match = re.search(r'الحلقة\s+(\d+)', title)
    if ep_match:
        ep_num = int(ep_match.group(1))
    else:
        # Fallback to search for any digit after الحلقة or EP
        ep_match_alt = re.search(r'(?:الحلقة|الحلقه|EP)\s*(\d+)', title, re.IGNORECASE)
        if ep_match_alt:
            ep_num = int(ep_match_alt.group(1))
            
    # Extract version/tags
    tags = []
    if "مدبلج" in title or "مدبلجة" in title:
        tags.append("مدبلج")
    if "الأبيض والاسود" in title or "الأبيض والأسود" in title or "الابيض والاسود" in title:
        tags.append("نسخة الأبيض والأسود")
    if "خاصة" in title or "خاصه" in title or "سبيشال" in title:
        tags.append("حلقة خاصة")
        
    version = " - ".join(tags) if tags else ""
    return season_num, ep_num, version

@app.route('/api/details')
def api_details():
    """Fetches stories, seasons, and episodes from Cinemana's details page.
    For series, dynamically aggregates and deduplicates all episodes across
    all matching seasons/versions via a fast parallelized/unified Cinemana search."""
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL is required.'}), 400
        
    try:
        cache_key = f"details_{url}"
        cached_val = app_cache.get(cache_key)
        if cached_val:
            return jsonify(cached_val)
            
        details = cinemana_api.get_details(url)
        
        # Smart Search-Based Series Aggregation
        if details.get('is_series') and details.get('title'):
            try:
                base_query = clean_for_search(details['title'])
                if base_query:
                    search_results = cinemana_api.search(base_query)
                    
                    matched_items = []
                    for r in search_results:
                        score = calculate_match_score(r['title'], base_query)
                        if score >= 50:
                            matched_items.append(r)
                            
                    if matched_items:
                        # Combine search results and original scraped episodes
                        all_episodes_data = []
                        seen_urls = set()
                        
                        for item in matched_items:
                            if item['url'] not in seen_urls:
                                seen_urls.add(item['url'])
                                all_episodes_data.append((item['title'], item['url']))
                                
                        for s in details.get('seasons', []):
                            for ep in s.get('episodes', []):
                                if ep['url'] not in seen_urls:
                                    seen_urls.add(ep['url'])
                                    all_episodes_data.append((f"{details['title']} - {s['title']} - {ep['title']}", ep['url']))
                                    
                        # Group by Season Number and Version
                        seasons_map = {}
                        for ep_title, ep_url in all_episodes_data:
                            s_num, e_num, ver = parse_episode_title(ep_title)
                            
                            ver_suffix = f" ({ver})" if ver else ""
                            season_display_title = f"موسم {s_num}{ver_suffix}"
                            
                            season_key = (s_num, ver)
                            if season_key not in seasons_map:
                                seasons_map[season_key] = {
                                    "title": season_display_title,
                                    "season_num": s_num,
                                    "version": ver,
                                    "episodes": []
                                }
                                
                            display_ep_title = f"الحلقة {e_num}"
                            active = ep_url.rstrip('/') == url.rstrip('/')
                            
                            seasons_map[season_key]["episodes"].append({
                                "title": display_ep_title,
                                "url": ep_url,
                                "active": active,
                                "ep_num": e_num
                            })
                            
                        # Sort episodes within seasons, and sort seasons
                        sorted_seasons = []
                        sorted_keys = sorted(seasons_map.keys(), key=lambda x: (x[0], x[1]))
                        
                        for key in sorted_keys:
                            s_data = seasons_map[key]
                            # Deduplicate episodes by ep_num (keep active one or first one)
                            unique_eps = {}
                            for ep in s_data["episodes"]:
                                num = ep["ep_num"]
                                if num not in unique_eps or ep["active"]:
                                    unique_eps[num] = ep
                                    
                            sorted_eps = sorted(unique_eps.values(), key=lambda x: x["ep_num"])
                            
                            cleaned_eps = []
                            for ep in sorted_eps:
                                cleaned_eps.append({
                                    "title": ep["title"],
                                    "url": ep["url"],
                                    "active": ep["active"]
                                })
                                
                            sorted_seasons.append({
                                "title": s_data["title"],
                                "active": any(ep["active"] for ep in cleaned_eps),
                                "episodes": cleaned_eps
                            })
                            
                        # Mark active season
                        if sorted_seasons:
                            has_active = any(s["active"] for s in sorted_seasons)
                            if not has_active:
                                sorted_seasons[0]["active"] = True
                            details['seasons'] = sorted_seasons
            except Exception as agg_err:
                print(f"⚠️ Search-based series aggregation failed: {agg_err}")
                
        app_cache.set(cache_key, details, ttl=3600) # Cache details for 1 hour
        return jsonify(details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watch')
def api_watch():
    """
    Direct Cinemana stream playback. Resolves Cinemana watch URL
    directly to HLS streams and returns them.
    Supports hybrid ArabSeed watch resolution for blazing-fast buffer-free streaming.
    """
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL is required.'}), 400
        
    title = request.args.get('title', '').strip()
    is_series = request.args.get('is_series', 'false').lower() == 'true'
    season = request.args.get('season', '').strip()
    episode = request.args.get('episode', '').strip()
    
    try:
        cache_key = f"watch_{url}_{title}_{is_series}_{season}_{episode}"
        cached_val = app_cache.get(cache_key)
        if cached_val:
            return jsonify(cached_val)
            
        # 1. Resolve Cinemana HLS stream options
        cinemana_servers = resolve_cinemana_stream(url)
        
        # 2. Resolve ArabSeed high-speed premium stream options (if title is provided)
        arabseed_servers = []
        if title:
            try:
                arabseed_servers = resolve_arabseed_stream(title, is_series, season, episode)
            except Exception as hybrid_err:
                print(f"❌ Error in hybrid resolver: {hybrid_err}")
                
        # 3. Merge servers (ArabSeed high-speed premium options first)
        merged_servers = arabseed_servers + cinemana_servers
        
        if not merged_servers:
            merged_servers = [{
                'type': 'direct',
                'server': '⚠️ عذراً، هذا العرض غير متوفر حالياً للبث المباشر',
                'url': 'about:blank'
            }]
            
        res = {'servers': merged_servers}
        app_cache.set(cache_key, res, ttl=300) # Cache watch streams for 5 minutes
        return jsonify(res)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Shared persistent Session with connection pooling for high-performance HLS proxying
stream_proxy_session = requests.Session()
stream_adapter = requests.adapters.HTTPAdapter(
    pool_connections=50,       # Number of connection pools to cache
    pool_maxsize=50,           # Max number of connections in each pool
    max_retries=3,             # Automatically retry failed requests up to 3 times!
    pool_block=False
)
stream_proxy_session.mount('https://', stream_adapter)
stream_proxy_session.mount('http://', stream_adapter)

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
        # Fetch HLS playlist or ts segment utilizing the high-performance persistent connection pool session!
        r = stream_proxy_session.get(video_url, headers=headers, stream=True, timeout=30)
        
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
                                    proxied_key_url = f"/api/stream?url={urllib.parse.quote(abs_key_url)}"
                                    line_stripped = line_stripped.replace(key_uri, proxied_key_url)
                            rewritten_lines.append(line_stripped)
                        else:
                            # It's a segment or sub-playlist URL
                            if line_stripped.startswith('stream.php'):
                                abs_segment_url = "https://cinemana.cc/" + line_stripped
                            else:
                                abs_segment_url = line_stripped
                            
                            proxied_segment_url = f"/api/stream?url={urllib.parse.quote(abs_segment_url)}"
                            rewritten_lines.append(proxied_segment_url)
                            
                    rewritten_content = '\n'.join(rewritten_lines)
                    
                    resp = Response(rewritten_content, status=200, content_type='application/vnd.apple.mpegurl')
                    resp.headers['Access-Control-Allow-Origin'] = '*'
                    resp.headers['Access-Control-Allow-Headers'] = '*'
                    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
                    return resp
            except Exception as decode_err:
                print(f"Decoding HLS playlist failed, falling back to direct stream: {decode_err}")
                
        # Force strip content-disposition to prevent browsers forcing a download dialog
        excluded_headers = ['connection', 'transfer-encoding', 'keep-alive', 'content-encoding', 'content-disposition']
        resp_headers = []
        has_content_type = False
        for name, value in r.headers.items():
            if name.lower() not in excluded_headers:
                if name.lower() == 'content-type':
                    has_content_type = True
                    # Force video/mp4 for video/audio streams marked as octet-stream
                    if 'octet-stream' in value.lower() or not value:
                        resp_headers.append((name, 'video/mp4'))
                    else:
                        resp_headers.append((name, value))
                else:
                    resp_headers.append((name, value))
                    
        if not has_content_type:
            resp_headers.append(('Content-Type', 'video/mp4'))
            
        # Inject CORS headers for dynamic web clients
        resp_headers.append(('Access-Control-Allow-Origin', '*'))
        resp_headers.append(('Access-Control-Allow-Headers', '*'))
        resp_headers.append(('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'))
        
        return Response(r.iter_content(chunk_size=262144), status=r.status_code, headers=resp_headers)
    except Exception as e:
        return f"Streaming Proxy Error: {e}", 502

if __name__ == '__main__':
    print("=" * 65)
    print(" 🚀 AleX CINEMA - PREMIUM AD-FREE PORTAL STARTING...")
    print(" Scrape source: cinemana.cc (Main)")
    print(" Running at http://127.0.0.1:5000")
    print("=" * 65)
    
    # Start cache warming worker in a background daemon thread
    # WERKZEUG_RUN_MAIN ensures it only runs once in the reloader sub-process
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        warmer_thread = threading.Thread(target=warm_caching_worker, daemon=True)
        warmer_thread.start()
        
    app.run(host='0.0.0.0', port=5000, debug=True)

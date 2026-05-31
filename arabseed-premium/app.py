# -*- coding: utf-8 -*-
"""
AleX CINEMA - Premium Ad-Free Web Portal Backend
------------------------------------------------
A Flask server that integrates the Shabakaty Cinemana scraping engine.
Acts as a transparent Range-compliant HLS/MP4 video stream proxy to bypass 403 blocks and popups.
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

# Import Cinemana Scraper
from cinemana_scraper import CinemanaAPI

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

# Initialize Scrapers
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
    "الحادي عشر": 11, "الحادية عشر": 11, "الثاني عشر": 12, "الثانية عشر": 12, 
    "الثالث عشر": 13, "الثالثة عشر": 13, "الرابع عشر": 14, "الرابعة عشر": 14, 
    "الخامس عشر": 15, "الخامسة عشر": 15, "السادس عشر": 16, "السادسة عشر": 16, 
    "السابع عشر": 17, "السابعة عشر": 17, "الثامن عشر": 18, "الثامنة عشر": 18, 
    "التاسع عشر": 19, "التاسعة عشر": 19, 
    "العشرون": 20, "العشرين": 20, "الحادي والعشرون": 21, "الثاني والعشرون": 22, 
    "الثالث والعشرون": 23, "الرابع والعشرون": 24, "الخامس والعشرون": 25, 
    "السادس والعشرون": 26, "السابع والعشرون": 27, "الثامن والعشرون": 28, 
    "التاسع والعشرون": 29, "الثلاثون": 30, "الثلاثين": 30
}

def parse_season_num(title: str) -> int:
    """Parses season number from Arabic/English title string using context scanning."""
    t_clean = re.sub(r'\s+', ' ', title)
    
    # 1. Search for Season/S in English
    m = re.search(r'\b(?:season|s)\s*(\d+)\b', t_clean, re.IGNORECASE)
    if m:
        return int(m.group(1))
    
    m = re.search(r'\b(\d+)(?:st|nd|rd|th)?\s+season\b', t_clean, re.IGNORECASE)
    if m:
        return int(m.group(1))
        
    # 2. Search for موسم/الموسم in Arabic
    m = re.search(r'(?:موسم|الموسم)\s+([\u0600-\u06FF0-9\s]+)', t_clean)
    if m:
        season_chunk = m.group(1).strip()
        digit_match = re.match(r'^(\d+)', season_chunk)
        if digit_match:
            return int(digit_match.group(1))
        for arabic_word in sorted(ARABIC_NUMBERS.keys(), key=lambda x: len(x), reverse=True):
            if arabic_word in season_chunk:
                return ARABIC_NUMBERS[arabic_word]
                
    # Fallback to checking any Arabic number word strictly preceded by موسم/الموسم
    for arabic_word in sorted(ARABIC_NUMBERS.keys(), key=lambda x: len(x), reverse=True):
        if re.search(r'(?:موسم|الموسم)\s+' + re.escape(arabic_word), t_clean):
            return ARABIC_NUMBERS[arabic_word]
            
    # Last fallback: search for season number anywhere as a plain digit after 'موسم'
    m = re.search(r'(?:موسم|الموسم)\s+(\d+)', t_clean)
    if m:
        return int(m.group(1))
        
    return 1 # Default to Season 1

def parse_episode_num(title: str) -> int:
    """Parses episode number from Arabic/English title string using context scanning."""
    t_clean = re.sub(r'\s+', ' ', title)
    
    # 1. Look for explicit digits in episode context
    m = re.search(r'(?:الحلقة|الحلقه|حلقة|حلقه|ep|episode)\s*(\d+)', t_clean, re.IGNORECASE)
    if m:
        return int(m.group(1))
        
    # 2. Look for Arabic word digits in episode context
    m = re.search(r'(?:الحلقة|الحلقه|حلقة|حلقه)\s+([\u0600-\u06FF\s]+)', t_clean)
    if m:
        ep_chunk = m.group(1).strip()
        for arabic_word in sorted(ARABIC_NUMBERS.keys(), key=lambda x: len(x), reverse=True):
            if arabic_word in ep_chunk:
                return ARABIC_NUMBERS[arabic_word]
                
    # 3. Fallback to check for any Arabic word digit strictly preceded by الحلقة/حلقة
    for arabic_word in sorted(ARABIC_NUMBERS.keys(), key=lambda x: len(x), reverse=True):
        if re.search(r'(?:الحلقة|الحلقه|حلقة|حلقه)\s+' + re.escape(arabic_word), t_clean):
            return ARABIC_NUMBERS[arabic_word]
            
    # 4. Fallback to general last resort: look for lonely digits that are NOT standard release years
    for m in re.finditer(r'\b(\d+)\b', t_clean):
        val = int(m.group(1))
        if not (1900 <= val <= 2030):
            return val
            
    return 1 # Default to Episode 1


def clean_for_search(title: str) -> str:
    """Cleans up Cinemana title to base name for robust search matching and dynamic grouping."""
    t = title
    
    # 1. Lowercase to normalize English titles
    t = t.lower()
    
    # 2. Remove year inside parentheses or brackets, e.g., (2017) or [2020]
    t = re.sub(r'[\(\[\{]\s*\d{4}\s*[\)\]\}]', '', t)
    # Also bare year at the end, e.g., " 2017"
    t = re.sub(r'\b\d{4}\b', '', t)
    
    # 3. Remove Season patterns in English and Arabic:
    # Arabic: الموسم الاول, الموسم الثاني, الموسم 2, موسم 02
    t = re.sub(r'(?:الموسم|موسم)\s+(?:الحادي عشر|الثاني عشر|الثالث عشر|الرابع عشر|الخامس عشر|السادس عشر|السابع عشر|الثامن عشر|التاسع عشر|العشرون|العشرين|الاول|الأول|الأولى|الاولى|الاولي|اول|أول|الثاني|الثانية|ثاني|ثانية|الثالث|الثالثة|ثالث|ثالثة|الرابع|الرابعة|رابع|رابعة|الخامس|الخامسة|خامس|خامسة|السادس|السادسة|سادس|سادسة|السابع|السابعة|سابع|سابعة|الثامن|الثامنة|ثامن|ثامنة|التاسع|التاسعة|تاسع|تاسعة|العاشر|العاشرة|عاشر|عاشرة|[\u0600-\u06FF\w\d]+)', '', t)
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
    season_num = parse_season_num(title)
    ep_num = parse_episode_num(title)
            
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
        
        raw_title = details.get('title', '')
        if raw_title:
            r_type = 'مسلسل' if details.get('is_series') else 'فيلم'
            details['title'] = clean_display_title(raw_title, r_type)
            
        # Smart Search-Based Series Aggregation
        if details.get('is_series') and raw_title:
            try:
                base_query = clean_for_search(raw_title)
                if base_query:
                    # Parallelized season-specific search queries to bypass Cinemana's 120 search results cap!
                    season_words = ["الاول", "الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس", "السابع", "الثامن", "التاسع", "العاشر", "الحادي عشر", "الثاني عشر"]
                    queries = [base_query]
                    for word in season_words:
                        queries.append(f"{base_query} الموسم {word}")
                    
                    search_results = []
                    seen_urls = set()
                    
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=len(queries)) as executor:
                        futures = {executor.submit(cinemana_api.search, q): q for q in queries}
                        for future in concurrent.futures.as_completed(futures):
                            try:
                                page_results = future.result()
                                for r in page_results:
                                    if r['url'] not in seen_urls:
                                        seen_urls.add(r['url'])
                                        search_results.append(r)
                            except Exception as search_err:
                                print(f"Parallel search err: {search_err}")
                    
                    orig_base_cleaned = normalize_arabic(clean_for_search(raw_title))
                    matched_items = []
                    for r in search_results:
                        if r.get('type') == 'فيلم':
                            continue
                        r_base_cleaned = normalize_arabic(clean_for_search(r['title']))
                        if r_base_cleaned == orig_base_cleaned:
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
    Supports high-speed transparent stream proxying for buffer-free playback.
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
            
        # Resolve Cinemana HLS stream options (Rely strictly on Cinemana!)
        merged_servers = resolve_cinemana_stream(url)
        
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
    
    referer = 'https://cinemana.cc/'
    if 'cinemana.cc' not in video_url.lower():
        referer = 'https://asd.ink/'
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': referer
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

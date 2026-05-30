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

@app.route('/')
def home():
    """Renders the main single page web interface."""
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    """Searches ArabSeed for movies/series and returns JSON results."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Search query is required.'}), 400
        
    try:
        # Check connection/fallback to working mirror
        api.auto_fallback_mirror()
        results = api.search(query)
        return jsonify({'results': results, 'mirror': api.base_url})
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

import sys
import os
import re

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cinemana_scraper import CinemanaAPI
from app import clean_for_search, calculate_match_score

sys.stdout.reconfigure(encoding='utf-8')

api = CinemanaAPI()

def parse_episode_title(title):
    # Extract season number
    season_num = 1
    # Match "الموسم الأول", "الموسم الأول", "الموسم 1", "الموسم الثاني", etc.
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

def aggregate_series_details(url):
    print(f"\n================= AGGREGATING FOR URL: {url} =================")
    details = api.get_details(url)
    title = details['title']
    print(f"Scraped Title: {title}")
    
    base_query = clean_for_search(title)
    print(f"Base Search Query: '{base_query}'")
    
    results = api.search(base_query)
    print(f"Search found {len(results)} results.")
    
    # Filter and group search results
    matched_items = []
    for r in results:
        # Check relevance score using calculate_match_score from app.py
        score = calculate_match_score(r['title'], base_query)
        if score >= 50:
            matched_items.append(r)
            
    print(f"Relevance filtered: {len(matched_items)} items matched the series.")
    
    # Combine scraped episodes and search episodes to ensure we don't miss anything
    all_episodes_data = []
    seen_urls = set()
    
    # Add search items
    for item in matched_items:
        if item['url'] not in seen_urls:
            seen_urls.add(item['url'])
            all_episodes_data.append((item['title'], item['url']))
            
    # Add originally scraped episodes
    for s in details.get('seasons', []):
        for ep in s.get('episodes', []):
            if ep['url'] not in seen_urls:
                seen_urls.add(ep['url'])
                # We can construct a display title for the episode from the season/episode info
                all_episodes_data.append((f"{title} - {s['title']} - {ep['title']}", ep['url']))
                
    # Group by Season and Version
    seasons_map = {}
    for ep_title, ep_url in all_episodes_data:
        s_num, e_num, ver = parse_episode_title(ep_title)
        
        # Build season display title
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
    # Sort keys: season_num first, then version alphabetically
    sorted_keys = sorted(seasons_map.keys(), key=lambda x: (x[0], x[1]))
    
    for key in sorted_keys:
        s_data = seasons_map[key]
        # Deduplicate episodes by ep_num (keep active one or first one)
        unique_eps = {}
        for ep in s_data["episodes"]:
            num = ep["ep_num"]
            if num not in unique_eps or ep["active"]:
                unique_eps[num] = ep
                
        # Sort episodes numerically
        sorted_eps = sorted(unique_eps.values(), key=lambda x: x["ep_num"])
        
        # Clean episode objects for frontend (remove ep_num)
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
        
    # Mark the first season as active if none are active
    if sorted_seasons and not any(s["active"] for s in sorted_seasons):
        sorted_seasons[0]["active"] = True
        
    print("\n✅ AGGREGATED SEASONS:")
    for s in sorted_seasons:
        print(f"  Season Title: '{s['title']}' | Active: {s['active']} | Episodes count: {len(s['episodes'])}")
        print(f"    Episodes: {[ep['title'] for ep in s['episodes']]}")
        
    return sorted_seasons

# Test on Spider-Noir Season 1 Ep 1 Dubbed
aggregate_series_details("https://cinemana.cc/watch=3021008/")

# Test on Ultimate Spider-Man Season 2 Ep 13
aggregate_series_details("https://cinemana.cc/watch=2809688/")

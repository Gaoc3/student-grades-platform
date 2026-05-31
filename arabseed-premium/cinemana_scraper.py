#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cinemana Web Scraper
--------------------
A professional Python module for scraping Shabakaty Cinemana (cinemana.cc).
Extracts homepage category carousels, search results, lists, and details.
"""

import sys
import re
import urllib.parse
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

# Ensure UTF-8 output to support Arabic characters in terminal
sys.stdout.reconfigure(encoding='utf-8')

class CinemanaAPI:
    """
    API Scraper client for Shabakaty Cinemana (https://cinemana.cc).
    Provides structured methods to fetch main page slider carousels,
    movies/series listings, search results, and specific post details.
    """
    
    def __init__(self, base_url: str = "https://cinemana.cc"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
            "Referer": self.base_url + "/"
        }
        self.session.headers.update(self.headers)

    def parse_card(self, card_el) -> Dict[str, str]:
        """
        Parses a single Cinemana watch card and returns structured details.
        Handles both <a> tags and elements containing <a> tags.
        """
        # Find the watch anchor
        a_tag = card_el if card_el.name == 'a' else card_el.find('a', href=True)
        if not a_tag or not a_tag.get('href') or 'watch=' not in a_tag.get('href'):
            return {}
            
        href = a_tag.get('href')
        # Ensure it is a valid watch page (watch followed by digits, not watch=category or pagination)
        if not re.search(r'watch=\d+', href):
            return {}
        if href.startswith('/'):
            href = self.base_url + href
            
        # Parse Title
        title = "غير معروف"
        h3 = a_tag.find('h3')
        if h3:
            title = h3.get_text(strip=True)
        else:
            span = a_tag.find('span')
            if span:
                title = span.get_text(strip=True)
            else:
                title = a_tag.get_text(strip=True)
                
        # Clean title from quick search hints
        title = title.replace("بحث سريع ←", "").strip()
        if title == "▶︎  شاهد الآن" or title == "▶︎ شاهد الآن" or not title:
            title_sibling = card_el.find(['span', 'h3', 'h4']) if card_el != a_tag else None
            if title_sibling:
                title = title_sibling.get_text(strip=True)
                
        # Parse Poster
        poster = ""
        bg_el = a_tag.find(style=re.compile(r'background-image')) or card_el.find(style=re.compile(r'background-image'))
        if bg_el:
            style = bg_el.get('style', '')
            m = re.search(r"url\(['\"]?([^'\")]+)['\"]?\)", style)
            if m:
                poster = m.group(1)
                
        # Detect type
        media_type = "فيلم"
        is_special = "special" in title.lower() or "سبيشال" in title or "خاص" in title or "فيلم" in title
        if not is_special:
            if any(x in title for x in ["مسلسل", "حلقة", "حلقه", "الحلقة", "الحلقه", "الموسم"]) or "انمي" in title.lower() or "أنمي" in title:
                media_type = "مسلسل"
            
        return {
            "title": title,
            "url": href,
            "poster": poster,
            "type": media_type,
            "rating": "7.8",
            "quality": "1080p FHD"
        }

    def get_homepage_categories(self) -> List[Dict[str, Any]]:
        """
        Scrapes https://cinemana.cc/main/ and parses all H2 sections and their horizontal cards.
        """
        categories = []
        try:
            r = self.session.get(f"{self.base_url}/main/", timeout=15)
            r.raise_for_status()
            
            soup = BeautifulSoup(r.text, 'html.parser')
            
            for h2 in soup.find_all('h2'):
                cat_name = h2.get_text(strip=True)
                if not cat_name or cat_name in ["قائمة المشاهدة لاحقاً", "استكمل المشاهدة"]:
                    continue
                    
                slider = h2.parent.find_next_sibling()
                if not slider or 'SliderClass' not in slider.get('class', []):
                    slider = h2.find_next_sibling()
                    
                if not slider:
                    continue
                    
                cards = []
                for a in slider.find_all('a', href=True):
                    if 'watch=' in a['href'] and 'cn-mega-item' not in a.get('class', []):
                        parsed = self.parse_card(a)
                        if parsed:
                            cards.append(parsed)
                            
                if cards:
                    categories.append({
                        "category": cat_name,
                        "cards": cards
                    })
                    
            return categories
        except Exception as e:
            print(f"Error scraping homepage categories: {e}")
            return []

    def search(self, query: str, max_pages: int = 1) -> List[Dict[str, Any]]:
        """
        Searches Cinemana by scraping the search results grid page.
        Supports fetching multiple pages for comprehensive series aggregation.
        """
        cards = []
        seen_urls = set()
        
        for page in range(1, max_pages + 1):
            search_url = f"{self.base_url}/"
            params = {"s": query}
            if page > 1:
                params["page"] = page
                
            try:
                print(f"Scraping Cinemana search page {page} for query '{query}'...")
                r = self.session.get(search_url, params=params, timeout=15)
                if r.status_code != 200:
                    print(f"Stop paginating search: Page {page} returned status {r.status_code}")
                    break
                    
                soup = BeautifulSoup(r.text, 'html.parser')
                
                a_tags = soup.find_all('a', class_=re.compile(r'block.*group.*relative'))
                if not a_tags:
                    a_tags = [a for a in soup.find_all('a', href=True) if 'watch=' in a['href'] and 'cn-mega-item' not in a.get('class', [])]
                    
                if not a_tags:
                    print(f"No anchors found on page {page}. Stopping pagination.")
                    break
                    
                page_added = 0
                for a in a_tags:
                    parsed = self.parse_card(a)
                    if parsed and parsed.get('title') and parsed['title'] != "N/A":
                        if parsed['url'] not in seen_urls:
                            seen_urls.add(parsed['url'])
                            cards.append(parsed)
                            page_added += 1
                            
                print(f"Page {page} added {page_added} unique items.")
                if page_added == 0:
                    # No new results added, probably duplicates or end of pagination
                    break
                    
            except Exception as e:
                print(f"Error searching Cinemana for {query} on page {page}: {e}")
                break
                
        return cards

    def scrape_listing_page(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrapes movie or series listing grid pages.
        """
        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            
            soup = BeautifulSoup(r.text, 'html.parser')
            
            cards = []
            a_tags = [a for a in soup.find_all('a', href=True) if 'watch=' in a['href'] and 'cn-mega-item' not in a.get('class', [])]
            for a in a_tags:
                parsed = self.parse_card(a)
                if parsed and parsed.get('title'):
                    if not any(x['url'] == parsed['url'] for x in cards):
                        cards.append(parsed)
            return cards
        except Exception as e:
            print(f"Error scraping listing page {url}: {e}")
            return []

    def get_details(self, watch_url: str) -> Dict[str, Any]:
        """
        Scrapes the Cinemana watch page to retrieve description, seasons, and episodes.
        """
        try:
            r = self.session.get(watch_url, timeout=15)
            r.raise_for_status()
            
            soup = BeautifulSoup(r.text, 'html.parser')
            
            title_el = soup.find('h1') or soup.find('h2') or soup.title
            title = title_el.get_text(strip=True) if title_el else "غير معروف"
            title = title.replace("– افلام ومسلسلات | قنوات بث", "").replace("سينمانا شبكتي ⭐️", "").strip()
            
            # 1. Parse description/story
            description = "لا توجد قصة متوفرة حالياً لهذا العرض."
            story_p = soup.find('p', class_=re.compile(r'text-gray-400|italic|leading-relaxed'))
            if story_p:
                description = story_p.get_text(strip=True)
            else:
                story_div = soup.find(class_=re.compile(r'story|desc|excerpt'))
                if story_div:
                    description = story_div.get_text(strip=True)
                    
            if "صيانة مؤقتة" in description:
                divs = soup.find_all('div')
                for d in divs:
                    text = d.get_text(strip=True)
                    if len(text) > 60 and "القصة" in text and "صيانة" not in text:
                        description = text.replace("القصة", "", 1).strip()
                        break
                        
            # 2. Parse seasons and episodes (highly organized season-wrapper divs)
            seasons = []
            is_series = False
            
            season_triggers = soup.find_all(class_='season-trigger')
            season_wrappers = soup.find_all(class_='season-wrapper')
            
            if season_triggers and season_wrappers:
                is_series = True
                seasons_map = {}
                num_seasons = min(len(season_triggers), len(season_wrappers))
                
                for i in range(num_seasons):
                    trigger = season_triggers[i]
                    s_title = trigger.get_text(strip=True)
                    if not s_title:
                        continue
                        
                    # Check if active
                    active_season = 'bg-red-600' in trigger.get('class', []) or 'block' in season_wrappers[i].get('class', [])
                    
                    # Find episodes inside this season wrapper
                    episodes = []
                    ep_anchors = season_wrappers[i].find_all('a', href=True)
                    for a in ep_anchors:
                        if 'watch=' in a['href']:
                            ep_href = a['href']
                            if ep_href.startswith('/'):
                                ep_href = self.base_url + ep_href
                                
                            ep_text = a.get_text(strip=True)
                            # Convert EP8 -> الحلقة 8
                            ep_match = re.search(r'EP\s*(\d+)', ep_text, re.IGNORECASE)
                            display_title = f"الحلقة {ep_match.group(1)}" if ep_match else ep_text
                            
                            active_ep = ep_href.rstrip('/') == watch_url.rstrip('/')
                            
                            episodes.append({
                                "title": display_title,
                                "url": ep_href,
                                "active": active_ep
                            })
                            
                    if s_title in seasons_map:
                        # Merge episodes and deduplicate them by url or title
                        existing_eps = seasons_map[s_title]['episodes']
                        for ep in episodes:
                            if not any(x['url'] == ep['url'] or x['title'] == ep['title'] for x in existing_eps):
                                existing_eps.append(ep)
                        if active_season:
                            seasons_map[s_title]['active'] = True
                    else:
                        seasons_map[s_title] = {
                            "title": s_title,
                            "active": active_season,
                            "episodes": episodes
                        }
                        
                # Sort episodes logically inside each season
                for s_title, s_data in seasons_map.items():
                    if s_data['episodes']:
                        def extract_ep_num(ep):
                            m = re.search(r'\d+', ep['title'])
                            return int(m.group()) if m else 9999
                        s_data['episodes'] = sorted(s_data['episodes'], key=extract_ep_num)
                        
                seasons = list(seasons_map.values())
            else:
                # Standalone movie/video if there are no season triggers or wrappers
                is_series = False
                seasons = []
                    
            return {
                "title": title,
                "description": description,
                "is_series": is_series,
                "seasons": seasons
            }
        except Exception as e:
            print(f"Error scraping details for {watch_url}: {e}")
            return {
                "title": "غير معروف",
                "description": "فشل تحميل التفاصيل من سينمانا.",
                "is_series": False,
                "seasons": []
            }

if __name__ == '__main__':
    # Simple CLI Test
    api = CinemanaAPI()
    print("Fetching homepage categories...")
    cats = api.get_homepage_categories()
    print("Found categories:", len(cats))

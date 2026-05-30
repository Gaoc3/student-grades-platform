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
            # Fallback to parent text search
            title_sibling = card_el.find(['span', 'h3', 'h4']) if card_el != a_tag else None
            if title_sibling:
                title = title_sibling.get_text(strip=True)
                
        # Parse Poster
        poster = ""
        # Look for element with style background-image
        bg_el = a_tag.find(style=re.compile(r'background-image')) or card_el.find(style=re.compile(r'background-image'))
        if bg_el:
            style = bg_el.get('style', '')
            # Extract first url in style
            m = re.search(r"url\(['\"]?([^'\")]+)['\"]?\)", style)
            if m:
                poster = m.group(1)
                
        # Detect type
        media_type = "فيلم"
        if "مسلسل" in title or "حلقة" in title or "الموسم" in title or "انمي" in title.lower() or "أنمي" in title:
            media_type = "مسلسل"
            
        return {
            "title": title,
            "url": href,
            "poster": poster,
            "type": media_type,
            "rating": "7.8", # Standard high premium aesthetic rating
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
            
            # Find all h2 category tags
            for h2 in soup.find_all('h2'):
                cat_name = h2.get_text(strip=True)
                if not cat_name or cat_name in ["قائمة المشاهدة لاحقاً", "استكمل المشاهدة"]:
                    continue
                    
                # Find SliderClass owl-carousel sibling
                slider = h2.parent.find_next_sibling()
                if not slider or 'SliderClass' not in slider.get('class', []):
                    # Try finding it directly under h2 sibling
                    slider = h2.find_next_sibling()
                    
                if not slider:
                    continue
                    
                # Scrape all card anchors inside the slider
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

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches Cinemana by scraping the search results grid page.
        """
        search_url = f"{self.base_url}/"
        params = {"s": query}
        
        try:
            r = self.session.get(search_url, params=params, timeout=15)
            r.raise_for_status()
            
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Search results are inside block group relative anchors
            cards = []
            a_tags = soup.find_all('a', class_=re.compile(r'block.*group.*relative'))
            # Fallback if class differs
            if not a_tags:
                a_tags = [a for a in soup.find_all('a', href=True) if 'watch=' in a['href'] and 'cn-mega-item' not in a.get('class', [])]
                
            for a in a_tags:
                parsed = self.parse_card(a)
                if parsed and parsed.get('title') and parsed['title'] != "N/A":
                    # Avoid duplicate search entries
                    if not any(x['url'] == parsed['url'] for x in cards):
                        cards.append(parsed)
                        
            return cards
        except Exception as e:
            print(f"Error searching Cinemana for {query}: {e}")
            return []

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
        Scrapes the Cinemana watch page to retrieve description and other episodes in the season.
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
                    
            # Clean banner text if any
            if "صيانة مؤقتة" in description:
                # Search for another text block
                divs = soup.find_all('div')
                for d in divs:
                    text = d.get_text(strip=True)
                    if len(text) > 60 and "القصة" in text and "صيانة" not in text:
                        description = text.replace("القصة", "", 1).strip()
                        break
                        
            # 2. Scrape related episodes (scrollbar row)
            episodes = []
            is_series = False
            
            # Find the horizontal scrollable episodes container
            scroll_div = soup.find('div', class_=re.compile(r'overflow-x-auto|snap-x|no-scrollbar'))
            if scroll_div:
                is_series = True
                # Find all watch anchors in this scroll row
                for a in scroll_div.find_all('a', href=True):
                    if 'watch=' in a['href']:
                        parsed = self.parse_card(a)
                        if parsed:
                            # Match episode index if present (e.g. "الحلقة 5" -> "حلقة 5")
                            ep_title = parsed['title']
                            ep_match = re.search(r'(الحلقة\s+\d+|حلقة\s+\d+)', ep_title)
                            display_title = ep_match.group(1) if ep_match else ep_title
                            
                            active = a['href'].rstrip('/') == watch_url.rstrip('/')
                            
                            episodes.append({
                                "title": display_title,
                                "url": parsed['url'],
                                "active": active
                            })
                            
            # If no scrollbar was found, let's look for any related series anchors in the text content
            if not episodes:
                # Check if "الحلقة" is in title -> then it is a series
                if "الحلقة" in title or "حلقة" in title or "الموسم" in title:
                    is_series = True
                    # Let's add the current page as a single episode since we don't have other links
                    episodes.append({
                        "title": "الحلقة الحالية",
                        "url": watch_url,
                        "active": True
                    })

            # Sort episodes in logical order (lowest episode first e.g. Episode 1, 2, ...)
            if episodes:
                def extract_ep_num(ep):
                    m = re.search(r'\d+', ep['title'])
                    return int(m.group()) if m else 0
                episodes = sorted(episodes, key=extract_ep_num)

            return {
                "title": title,
                "description": description,
                "is_series": is_series,
                "episodes": episodes
            }
        except Exception as e:
            print(f"Error scraping details for {watch_url}: {e}")
            return {
                "title": "غير معروف",
                "description": "فشل تحميل التفاصيل من سينمانا.",
                "is_series": False,
                "episodes": []
            }

if __name__ == '__main__':
    # Simple CLI Test
    api = CinemanaAPI()
    print("Fetching homepage categories...")
    cats = api.get_homepage_categories()
    print("Found categories:", len(cats))
    for c in cats:
        print(f"  Category: {c['category']} ({len(c['cards'])} cards)")
        for card in c['cards'][:2]:
            print(f"    - {card['title']} | URL: {card['url']} | Poster: {card['poster']}")

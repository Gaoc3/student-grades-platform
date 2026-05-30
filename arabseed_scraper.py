#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ArabSeed Professional Web Scraper & API
---------------------------------------
A professional Python module and interactive command-line tool for searching,
browsing, and extracting direct download/streaming links from ArabSeed.

Author: Antigravity Team
Date: 2026-05-30
"""

import sys
import re
import base64
import urllib.parse
from typing import List, Dict, Union, Optional
import requests
from bs4 import BeautifulSoup

# Configure UTF-8 output to support Arabic characters in all terminals
sys.stdout.reconfigure(encoding='utf-8')

# Try importing rich for beautiful terminal styling; fall back gracefully if missing
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, IntPrompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# Default Mirros list for high resilience
MIRRORS = [
    "https://m.asd.ink",
    "https://m.arabseed.show",
    "https://arabseed.show",
    "https://arabseed.live"
]

class ArabSeedAPI:
    """
    A robust, high-performance API client to interact with ArabSeed mirrors,
    scrape search results, series episodes, and decode download links.
    """
    
    def __init__(self, base_url: str = "https://m.asd.ink"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
            "Referer": self.base_url + "/"
        }
        self.session.headers.update(self.headers)
        
    def set_mirror(self, url: str):
        """Changes the active mirror base URL."""
        self.base_url = url.rstrip('/')
        self.session.headers.update({"Referer": self.base_url + "/"})

    def test_connection(self) -> bool:
        """Tests if the mirror is responsive."""
        try:
            r = self.session.get(self.base_url, timeout=6)
            return r.status_code == 200
        except Exception:
            return False

    def auto_fallback_mirror(self) -> bool:
        """Attempts to find a working mirror from the pre-defined list."""
        if self.test_connection():
            return True
            
        for mirror in MIRRORS:
            if mirror == self.base_url:
                continue
            try:
                r = self.session.get(mirror, timeout=5)
                if r.status_code == 200:
                    self.set_mirror(mirror)
                    return True
            except Exception:
                continue
        return False

    def decode_link(self, obfuscated_url: str) -> str:
        """
        Decodes the base64-obfuscated download links used by ArabSeed.
        Example: https://m.asd.ink/l/aHR0cHM6Ly9tLnJldmlld3JhdGUubmV0L2ZxcGM5OGoyNnRydQ==
        returns: https://m.reviewrate.net/fqpc98j26tru
        """
        if not obfuscated_url:
            return ""
            
        if "/l/" in obfuscated_url:
            try:
                # Extract the base64 part
                parts = obfuscated_url.split("/l/")
                if len(parts) > 1:
                    b64_part = parts[1].rstrip('/')
                    b64_part = urllib.parse.unquote(b64_part)
                    
                    # Add missing padding if necessary
                    missing_padding = len(b64_part) % 4
                    if missing_padding:
                        b64_part += '=' * (4 - missing_padding)
                        
                    decoded_bytes = base64.b64decode(b64_part)
                    decoded_url = decoded_bytes.decode('utf-8', errors='ignore')
                    return decoded_url
            except Exception:
                return obfuscated_url
        return obfuscated_url

    def search(self, query: str) -> List[Dict[str, str]]:
        """
        Searches ArabSeed for movies, series, or music.
        Returns a list of structured dictionaries containing item metadata.
        """
        search_url = f"{self.base_url}/find/"
        params = {"word": query}
        
        try:
            r = self.session.get(search_url, params=params, timeout=10)
            r.raise_for_status()
        except Exception as e:
            # Try mirror fallback
            if self.auto_fallback_mirror():
                search_url = f"{self.base_url}/find/"
                r = self.session.get(search_url, params=params, timeout=10)
            else:
                raise Exception(f"Failed to connect to ArabSeed mirrors: {e}")
                
        soup = BeautifulSoup(r.text, "html.parser")
        blocks = soup.find_all(class_="movie__block")
        
        results = []
        for block in blocks:
            href = block.get("href")
            if not href:
                continue
                
            # Direct link to post page
            url = href
            if url.startswith('/'):
                url = self.base_url + url
                
            # Extract poster image
            img_tag = block.find("img")
            poster = ""
            if img_tag:
                poster = img_tag.get("data-src") or img_tag.get("src") or ""
                
            # Extract Title (Arabic)
            title_tag = block.find(class_="post__name") or block.find("h3")
            title = title_tag.get_text(strip=True) if title_tag else "غير معروف"
            
            # Extract Rating
            rating_tag = block.find(class_="post__ratings") or block.find(class_="rating")
            rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"
            
            # Extract Quality Badge (e.g. 1080p, HDCAM, WEB-DL)
            quality_tag = block.find(class_="badge__quality") or block.find(class_="quality")
            quality = quality_tag.get_text(strip=True) if quality_tag else "غير محدد"
            
            # Detect Media Type from title/URL
            media_type = "فيلم"
            if "مسلسل" in title or "s1" in url.lower() or "s2" in url.lower() or "season" in url.lower() or "eps" in url.lower():
                media_type = "مسلسل / حلقة"
            elif "اغنية" in title.lower() or "أغنية" in title or "track" in url.lower() or "song" in url.lower():
                media_type = "موسيقى / أغنية"
            elif "عرض" in title or "wwe" in url.lower() or "مصارعة" in title:
                media_type = "برنامج / مصارعة"
            elif "مسرحية" in title:
                media_type = "مسرحية"
                
            results.append({
                "title": title,
                "url": url,
                "poster": poster,
                "rating": rating,
                "quality": quality,
                "type": media_type
            })
            
        return results

    def get_details(self, item_url: str) -> Dict[str, Union[str, bool, List[Dict[str, str]]]]:
        """
        Fetches the details page of an item.
        Detects if it's a series and extracts all other episodes.
        """
        try:
            r = self.session.get(item_url, timeout=10)
            r.raise_for_status()
        except Exception as e:
            raise Exception(f"Failed to fetch details page: {e}")
            
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Check if it has an episode list
        episodes_list = []
        is_series = False
        
        # Look for the episodes container
        ep_section = soup.find(class_="episodes__list") or soup.find(class_=lambda x: x and "episode" in x.lower())
        if ep_section:
            is_series = True
            anchors = ep_section.find_all("a")
            for a in anchors:
                href = a.get("href")
                if not href:
                    continue
                if href.startswith('/'):
                    href = self.base_url + href
                    
                # Extract episode title
                num_div = a.find(class_="epi__num")
                if num_div:
                    ep_title = num_div.get_text(" ", strip=True)
                else:
                    ep_title = a.get_text(strip=True)
                    
                active = "active" in a.get("class", [])
                
                episodes_list.append({
                    "title": ep_title,
                    "url": href,
                    "active": active
                })
        
        # Parse description
        desc_el = soup.find(class_="story") or soup.find(class_="story__content") or soup.find(class_="inner__data")
        description = desc_el.get_text(strip=True) if desc_el else "لا يوجد وصف متوفر."
        
        # Check for direct download/watch button hrefs as well
        download_btn = soup.find("a", class_=re.compile("download"))
        download_page_url = download_btn.get("href") if download_btn else (item_url.rstrip('/') + "/download/")
        
        watch_btn = soup.find("a", class_=re.compile("watch"))
        watch_page_url = watch_btn.get("href") if watch_btn else (item_url.rstrip('/') + "/watch/")

        return {
            "title": soup.find("h1").get_text(strip=True) if soup.find("h1") else "غير معروف",
            "is_series": is_series,
            "episodes": episodes_list,
            "description": description,
            "download_page": download_page_url,
            "watch_page": watch_page_url
        }

    def get_download_links(self, detail_url: str) -> List[Dict[str, str]]:
        """
        Navigates to the download sub-page, extracts all mirrors,
        decodes them, and returns direct high-speed download links.
        """
        # Formulate download page URL
        if not detail_url.rstrip('/').endswith('/download'):
            download_url = detail_url.rstrip('/') + "/download/"
        else:
            download_url = detail_url
            
        try:
            r = self.session.get(download_url, timeout=10)
            r.raise_for_status()
        except Exception as e:
            raise Exception(f"Failed to fetch download sub-page: {e}")
            
        soup = BeautifulSoup(r.text, "html.parser")
        dl_list = soup.find(class_="downloads__links__list")
        
        links = []
        
        if dl_list:
            items = dl_list.find_all("li")
            for item in items:
                a_tag = item.find("a")
                if not a_tag:
                    continue
                    
                obfuscated_url = a_tag.get("href") or ""
                raw_text = a_tag.get_text(strip=True)
                
                # Decode base64 URL
                decoded_url = self.decode_link(obfuscated_url)
                
                # Parse Host & Quality details from text
                # Typical text: "Frdlالتحميل الان - 1080p" or "سيرفر عرب سيد المباشرالتحميل الان - 720p"
                quality = "غير محدد"
                quality_match = re.search(r'(\d+p)', raw_text)
                if quality_match:
                    quality = quality_match.group(1)
                    
                host = raw_text.split("التحميل")[0].strip()
                if not host:
                    host = "سيرفر مباشر"
                
                # Check for sizes if listed
                size_tag = item.find(class_="size") or item.find(class_="badge__size")
                size = size_tag.get_text(strip=True) if size_tag else "غير معروف"
                
                links.append({
                    "server": host,
                    "quality": quality,
                    "size": size,
                    "direct_link": decoded_url
                })
        else:
            # Fallback if the standard list is not present (scrape all external and download anchors)
            anchors = soup.find_all("a")
            for a in anchors:
                href = a.get("href") or ""
                text = a.get_text(strip=True)
                if "/l/" in href or ("تحميل" in text and href.startswith("http")):
                    decoded = self.decode_link(href)
                    links.append({
                        "server": "سيرفر خارجي" if not "/l/" in href else "سيرفر مباشر مرمز",
                        "quality": "غير محدد",
                        "size": "غير معروف",
                        "direct_link": decoded
                    })
                    
        return links


# -------------------------------------------------------------
# INTERACTIVE TERMINAL INTERFACE (CLI)
# -------------------------------------------------------------

def print_rich_header(console: Console, api: ArabSeedAPI):
    """Draws a premium header panel on terminals that support Rich."""
    header_text = Text()
    header_text.append("عرب سيد ", style="bold red")
    header_text.append("ArabSeed Downloader & Link Extractor 🚀\n", style="bold white")
    header_text.append(f"Mirror API: {api.base_url}", style="dim cyan")
    
    console.print(
        Panel(
            header_text,
            box=box.ROUNDED,
            border_style="red",
            title="[bold white]Antigravity Web Scraper[/bold white]",
            title_align="center"
        )
    )

def run_cli():
    """Main CLI execution loop."""
    # Fallback if Rich is not installed
    if not HAS_RICH:
        print("="*60)
        print(" ArabSeed Downloader & Link Extractor (Antigravity)")
        print("="*60)
        
        query = input("🔍 أدخل اسم الفلم، المسلسل أو الموسيقى للبحث: ")
        api = ArabSeedAPI()
        print("⏳ جاري البحث في عرب سيد...")
        try:
            results = api.search(query)
            if not results:
                print("❌ لم يتم العثور على نتائج.")
                return
                
            for idx, item in enumerate(results):
                print(f"[{idx+1}] {item['title']} | الجودة: {item['quality']} | النوع: {item['type']}")
                
            choice = int(input("\n👉 اختر رقم العنصر لرؤية روابط التحميل: ")) - 1
            if choice < 0 or choice >= len(results):
                print("❌ اختيار غير صحيح.")
                return
                
            selected = results[choice]
            print(f"\n⏳ جاري تحميل تفاصيل: {selected['title']}...")
            details = api.get_details(selected['url'])
            
            target_url = selected['url']
            if details['is_series']:
                print("\n📦 هذا العنصر مسلسل. قائمة الحلقات المتوفرة:")
                for ep_idx, ep in enumerate(details['episodes']):
                    active_indicator = " ⭐" if ep['active'] else ""
                    print(f"  [{ep_idx+1}] {ep['title']}{active_indicator}")
                
                ep_choice = int(input("\n👉 اختر رقم الحلقة للتحميل: ")) - 1
                if ep_choice < 0 or ep_choice >= len(details['episodes']):
                    print("❌ اختيار غير صحيح.")
                    return
                target_url = details['episodes'][ep_choice]['url']
                print(f"⏳ جاري تحميل الحلقة: {details['episodes'][ep_choice]['title']}...")
                
            print("\n⏳ جاري استخراج وفك تشفير روابط التحميل المباشرة...")
            links = api.get_download_links(target_url)
            
            if not links:
                print("❌ لم يتم العثور على روابط تحميل متوفرة لهذا العنصر.")
                return
                
            print("\n✅ تم استخراج روابط التحميل بنجاح:")
            print("="*80)
            for l in links:
                print(f"🖥️ السيرفر: {l['server']} | الجودة: {l['quality']} | الحجم: {l['size']}")
                print(f"🔗 الرابط المباشر: {l['direct_link']}")
                print("-" * 80)
                
        except Exception as e:
            print("❌ حدث خطأ:", e)
        return

    # Rich Enabled Console
    console = Console()
    api = ArabSeedAPI()
    
    # Mirror Check with spinner
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        task = progress.add_task(description="[cyan]جاري الاتصال بسيرفر عرب سيد والتحقق من المرايا...[/cyan]", total=None)
        api.auto_fallback_mirror()
        
    print_rich_header(console, api)
    
    # Get Search Term
    query = Prompt.ask("[bold yellow]🔍 أدخل اسم الفلم، المسلسل، أو الموسيقى للبحث[/bold yellow]")
    if not query.strip():
        console.print("[bold red]❌ لا يمكن للبحث أن يكون فارغاً.[/bold red]")
        return
        
    # Run Search with rich spinner
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        progress.add_task(description="[bold green]🔎 جاري البحث وجلب النتائج من قاعدة البيانات...[/bold green]", total=None)
        try:
            results = api.search(query)
        except Exception as e:
            console.print(f"[bold red]❌ فشل البحث: {e}[/bold red]")
            return
            
    if not results:
        console.print("[bold red]❌ لم يتم العثور على أي نتائج تطابق بحثك.[/bold red]")
        return
        
    # Render Search Table
    table = Table(title=f"📺 نتائج البحث عن: '{query}'", box=box.HEAVY_EDGE, border_style="red")
    table.add_column("الرقم", justify="center", style="cyan", no_wrap=True)
    table.add_column("الاسم (العنوان)", style="white")
    table.add_column("النوع", style="magenta")
    table.add_column("الجودة", style="green")
    table.add_column("التقييم ⭐", style="yellow", justify="center")
    
    for idx, item in enumerate(results):
        table.add_row(
            str(idx + 1),
            item["title"],
            item["type"],
            item["quality"],
            item["rating"]
        )
        
    console.print(table)
    
    # Let user select
    choice = IntPrompt.ask(
        "\n[bold yellow]👉 اختر رقم العنصر لمشاهدة تفاصيله[/bold yellow]",
        choices=[str(x) for x in range(1, len(results) + 1)]
    ) - 1
    
    selected = results[choice]
    
    # Get details with loader
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        progress.add_task(description=f"[bold green]⏳ جاري تحليل صفحة التفاصيل واستخراج الحلقات...[/bold green]", total=None)
        try:
            details = api.get_details(selected["url"])
        except Exception as e:
            console.print(f"[bold red]❌ فشل جلب التفاصيل: {e}[/bold red]")
            return
            
    # Print Item Panel
    console.print(
        Panel(
            f"[bold cyan]القصة / التفاصيل:[/bold cyan]\n{details['description']}",
            title=f"[bold white]{details['title']}[/bold white]",
            border_style="magenta",
            box=box.ROUNDED
        )
    )
    
    target_url = selected["url"]
    
    # Handle Series / Episodes selection
    if details["is_series"]:
        episodes = details["episodes"]
        ep_table = Table(title="📦 حلقات الموسم المتوفرة", box=box.SIMPLE_HEAD, border_style="magenta")
        ep_table.add_column("الرقم", justify="center", style="cyan")
        ep_table.add_column("اسم الحلقة", style="white")
        ep_table.add_column("الحالة", style="yellow")
        
        for ep_idx, ep in enumerate(episodes):
            status = "[bold green]الحلقة الحالية[/bold green]" if ep["active"] else "جاهزة للتحميل"
            ep_table.add_row(str(ep_idx + 1), ep["title"], status)
            
        console.print(ep_table)
        
        ep_choice = IntPrompt.ask(
            "\n[bold yellow]👉 اختر رقم الحلقة التي تريد تحميلها[/bold yellow]",
            choices=[str(x) for x in range(1, len(episodes) + 1)]
        ) - 1
        
        target_url = episodes[ep_choice]["url"]
        selected_ep_title = episodes[ep_choice]["title"]
        console.print(f"[bold green]⏳ تم اختيار: {selected_ep_title}... جاري جلب صفحة التحميل...[/bold green]")
        
    # Get download links with loader
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        progress.add_task(description="[bold green]🔓 جاري فك التشفير وتوليد روابط التحميل المباشرة الحصرية...[/bold green]", total=None)
        try:
            links = api.get_download_links(target_url)
        except Exception as e:
            console.print(f"[bold red]❌ فشل جلب روابط التحميل: {e}[/bold red]")
            return
            
    if not links:
        console.print("[bold red]❌ لم يتم العثور على أي سيرفرات تحميل نشطة لهذا العنصر حالياً.[/bold red]")
        return
        
    # Show Download Links Table
    dl_table = Table(title="📥 روابط التحميل المباشرة والبديلة (مفكوكة التشفير)", box=box.DOUBLE_EDGE, border_style="green")
    dl_table.add_column("الرقم", justify="center", style="cyan")
    dl_table.add_column("اسم السيرفر", style="magenta", bold=True)
    dl_table.add_column("الجودة", style="green", justify="center")
    dl_table.add_column("الحجم", style="yellow", justify="center")
    dl_table.add_column("الرابط المباشر للتحميل الفوري", style="white", overflow="ellipsis")
    
    for l_idx, l in enumerate(links):
        dl_table.add_row(
            str(l_idx + 1),
            l["server"],
            l["quality"],
            l["size"],
            l["direct_link"]
        )
        
    console.print(dl_table)
    
    console.print("\n[bold green]💡 نصيحة: يمكنك نسخ الرابط مباشرة واستخدامه في برنامج التحميل المفضل لديك (مثل IDM أو wget).[/bold green]\n")


if __name__ == "__main__":
    try:
        run_cli()
    except KeyboardInterrupt:
        print("\n👋 تم الإلغاء بواسطة المستخدم. وداعاً!")
        sys.exit(0)

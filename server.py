
import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import ssl
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

PORT = 3000
ssl_context = ssl._create_unverified_context()
news_cache = {}
CACHE_DURATION = 1800

# The generic Google News logo that the user complained about
GENERIC_ICON_IDS = [
    'J6_coFbogxhRI9iM864NL_liGXvsQp2AupsKei7z0cNNfDvGUmWUy20nuUhkREQyrpY4bEeIBuc',
    'DR60l-K8vnyi99NZovm9HlXyZwQ85GMDxiwJWzoasZYCUrPuUM_P_4Rb7ei03j-0nRs0c4F'
]

def get_real_thumbnail(google_link):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        }

        # Follow redirects to reach the actual news site
        req = urllib.request.Request(google_link, headers=headers)
        with urllib.request.urlopen(req, context=ssl_context, timeout=5) as response:
            final_url = response.geturl()

            # If we are stuck on a Google News interstitial/wrapper
            if "news.google.com" in final_url:
                html = response.read().decode('utf-8', errors='ignore')
                # Try to find a direct link to the article in the wrapper's canonical or data
                match = re.search(r'data-url="([^"]+)"', html)
                if match:
                    # Recurse once with the real URL
                    return get_real_thumbnail(match.group(1))

                # Check for canonical
                match = re.search(r'link rel="canonical" href="([^"]+)"', html)
                if match and "news.google.com" not in match.group(1):
                    return get_real_thumbnail(match.group(1))

            # If we are on the target site, extract metadata
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type: return None

            html = response.read().decode('utf-8', errors='ignore')

            patterns = [
                r'property=["\']og:image["\']\s+content=["\']([^"\']+)["\']',
                r'content=["\']([^"\']+)["\']\s+property=["\']og:image["\']',
                r'name=["\']twitter:image["\']\s+content=["\']([^"\']+)["\']'
            ]

            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    img_url = match.group(1).replace('&amp;', '&')
                    if img_url.startswith('//'): img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        parsed_final = urllib.parse.urlparse(final_url)
                        img_url = f"{parsed_final.scheme}://{parsed_final.netloc}{img_url}"

                    # Filter generic icons
                    is_generic = False
                    for g_id in GENERIC_ICON_IDS:
                        if g_id in img_url: is_generic = True; break
                    if is_generic: continue

                    if img_url.lower().split('?')[0].endswith(('.ico', '.svg')): continue

                    return img_url
    except:
        pass
    return None

class NexusHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        if path.startswith('/api/news'):
            self.handle_news_api(parsed_url.query)
            return
        if path in ['/', '', '/Nexus_News.html']:
            self.path = '/index.html'
        elif not os.path.exists(self.path.lstrip('/')):
             if '.' not in os.path.basename(path):
                 self.path = '/index.html'
        return super().do_GET()

    def handle_news_api(self, query_string):
        params = urllib.parse.parse_qs(query_string)
        region = params.get('region', ['WW'])[0]
        now = time.time()

        if region in news_cache:
            data, timestamp = news_cache[region]
            if now - timestamp < CACHE_DURATION:
                self.send_json(data)
                return

        rss_urls = {
            'WW': 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en',
            'DE': 'https://news.google.com/rss?hl=de&gl=DE&ceid=DE:de',
            'UK': 'https://news.google.com/rss?hl=en-GB&gl=GB&ceid=GB:en',
            'FR': 'https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr',
            'JP': 'https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja'
        }

        try:
            url = rss_urls.get(region, rss_urls['WW'])
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                xml_data = response.read().decode('utf-8')
            root = ET.fromstring(xml_data)
            items = []
            links = []
            for item in root.findall('.//item')[:30]:
                link = item.find('link').text if item.find('link') is not None else ''
                items.append({
                    'title': item.find('title').text or '',
                    'link': link,
                    'pubDate': item.find('pubDate').text or '',
                    'source': item.find('source').text or region,
                    'thumbnail': None
                })
                links.append(link)

            # Fetch real thumbs in parallel
            with ThreadPoolExecutor(max_workers=15) as executor:
                thumbs = list(executor.map(get_real_thumbnail, links))

            for i, thumb in enumerate(thumbs):
                if thumb:
                    items[i]['thumbnail'] = f"https://images.weserv.nl/?url={urllib.parse.quote(thumb)}&w=800&fit=cover"

            response_data = {'status': 'ok', 'region': region, 'count': len(items), 'items': items}
            news_cache[region] = (response_data, now)
            self.send_json(response_data)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode())

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), NexusHandler) as httpd:
        print(f"Serving Nexus at http://localhost:{PORT}")
        httpd.serve_forever()

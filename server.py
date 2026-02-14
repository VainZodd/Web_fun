
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

# Create an unverified SSL context for outgoing requests
ssl_context = ssl._create_unverified_context()

# Simple In-Memory Cache
news_cache = {}
CACHE_DURATION = 1800 # 30 minutes

def get_real_thumbnail(item_data):
    """Try to get a real thumbnail for a news item, preferring the one from description or og:image."""
    link = item_data['link']
    desc = item_data['description']

    # 1. Try extracting from description HTML (Google's own thumb)
    match = re.search(r'src="([^"]+lh3\.googleusercontent\.com[^"]+)"', desc)
    if match:
        img_url = match.group(1)
        # Upscale and proxy
        img_url = re.sub(r'=[ws]\d+.*$', '=w800', img_url)
        return f"https://images.weserv.nl/?url={urllib.parse.quote(img_url)}"

    # 2. Try following redirect to get og:image
    try:
        req = urllib.request.Request(link, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        })
        with urllib.request.urlopen(req, context=ssl_context, timeout=4) as response:
            html = response.read().decode('utf-8', errors='ignore')
            patterns = [
                r'property="og:image"\s+content="([^"]+)"',
                r'name="twitter:image"\s+content="([^"]+)"',
                r'rel="image_src"\s+href="([^"]+)"'
            ]
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    img_url = match.group(1)
                    if img_url.startswith('//'): img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        parsed_final = urllib.parse.urlparse(response.geturl())
                        img_url = f"{parsed_final.scheme}://{parsed_final.netloc}{img_url}"

                    # Ignore tiny/generic icons
                    if "favicon" in img_url.lower() or img_url.endswith('.ico'): continue

                    # Proxy the image to bypass CORS/Referer issues
                    return f"https://images.weserv.nl/?url={urllib.parse.quote(img_url)}"
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
            # Using Search RSS for better thumb availability
            if region == 'WW': url = 'https://news.google.com/rss/search?q=top+stories&hl=en-US&gl=US&ceid=US:en'
            elif region == 'DE': url = 'https://news.google.com/rss/search?q=top+themen&hl=de&gl=DE&ceid=DE:de'

            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
            })

            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                xml_data = response.read().decode('utf-8')

            root = ET.fromstring(xml_data)
            items = []

            raw_items = root.findall('.//item')[:30]

            for item in raw_items:
                title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ''
                desc = item.find('description').text if item.find('description') is not None else ''
                source = item.find('source').text if item.find('source') is not None else region

                items.append({
                    'title': title,
                    'link': link,
                    'pubDate': pubDate,
                    'description': desc,
                    'source': source,
                    'thumbnail': None
                })

            with ThreadPoolExecutor(max_workers=20) as executor:
                thumbnails = list(executor.map(get_real_thumbnail, items))

            for i, thumb in enumerate(thumbnails):
                items[i]['thumbnail'] = thumb

            response_data = {'status': 'ok', 'region': region, 'count': len(items), 'items': items}
            news_cache[region] = (response_data, now)
            self.send_json(response_data)
        except Exception as e:
            print(f"API Error [{region}]: {e}")
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

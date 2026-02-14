
import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import ssl
import os

PORT = 3000

# Create an unverified SSL context for outgoing requests to bypass certificate issues
ssl_context = ssl._create_unverified_context()

class NexusHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path.startswith('/api/news'):
            self.handle_news_api(parsed_url.query)
            return
        super().do_GET()

    def translate_path(self, path):
        # path here is the URL path
        parsed = urllib.parse.urlparse(path)
        p = parsed.path

        # Mapping
        if p in ['/', '', '/Nexus_News.html']:
            p = '/index.html'

        # Determine local path
        local_path = super().translate_path(p)

        # SPA routing fallback: if it's not a file and doesn't exist, serve index.html
        if not os.path.exists(local_path):
            basename = os.path.basename(p)
            if not basename or '.' not in basename:
                return super().translate_path('/index.html')

        return local_path

    def handle_news_api(self, query_string):
        params = urllib.parse.parse_qs(query_string)
        region = params.get('region', ['WW'])[0]

        rss_urls = {
            'WW': 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en',
            'DE': 'https://news.google.com/rss?hl=de&gl=DE&ceid=DE:de',
            'UK': 'https://news.google.com/rss?hl=en-GB&gl=GB&ceid=GB:en',
            'FR': 'https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr',
            'JP': 'https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja'
        }

        try:
            url = rss_urls.get(region, rss_urls['WW'])
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })

            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                xml_data = response.read().decode('utf-8')

            root = ET.fromstring(xml_data)
            items = []
            for item in root.findall('.//item'):
                items.append({
                    'title': item.find('title').text if item.find('title') is not None else '',
                    'link': item.find('link').text if item.find('link') is not None else '',
                    'pubDate': item.find('pubDate').text if item.find('pubDate') is not None else '',
                    'description': item.find('description').text if item.find('description') is not None else '',
                    'source': item.find('source').text if item.find('source') is not None else region
                })

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'region': region, 'count': len(items), 'items': items}).encode())
        except Exception as e:
            print(f"API Error [{region}]: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode())

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), NexusHandler) as httpd:
        print(f"Serving Nexus at http://localhost:{PORT}")
        httpd.serve_forever()

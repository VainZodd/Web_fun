
import http.server
import socketserver
import urllib.request
import json
import xml.etree.ElementTree as ET

PORT = 3000

class NexusHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/news'):
            self.handle_news_api()
        else:
            super().do_GET()

    def handle_news_api(self):
        query = self.path.split('?')[-1]
        region = 'WW'
        if 'region=DE' in query:
            region = 'DE'

        rss_urls = {
            'WW': 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en',
            'DE': 'https://news.google.com/rss?hl=de&gl=DE&ceid=DE:de'
        }

        try:
            url = rss_urls.get(region, rss_urls['WW'])
            with urllib.request.urlopen(url) as response:
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
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'items': items}).encode())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

with socketserver.TCPServer(("0.0.0.0", PORT), NexusHandler) as httpd:
    print(f"Serving Nexus at http://localhost:{PORT}")
    httpd.serve_forever()

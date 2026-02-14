# NEXUS // GLOBAL NEWS GRID

A high-performance, cyberpunk-themed news dashboard with real-time global surveillance capabilities.

## Features

- **Real-time News Integration:** Fetches top 30 news reports via Google News RSS proxy.
- **Contextual Intelligence:** Extracts keywords from headlines to fetch relevant images and generate neural analysis.
- **Multi-View Architecture:**
  - **GRID:** Global overview with simulated metrics and environmental monitoring.
  - **TIME:** Chronological archive with temporal density analysis.
  - **DATA:** Deep search vault with sector distribution and entity extraction clouds.
  - **DETAIL:** In-depth signal analysis with source integrity scanning.
- **Snappy UI:** Powered by GSAP for ultra-fast, smooth animations (0.08s - 0.15s durations).
- **Auto-Sync:** Updates every 30 minutes to ensure data freshness.
- **Internationalization:** Full support for English and German.

## Setup & Execution

1. **Start the Proxy Server:**
   The dashboard requires a Python backend to proxy RSS feeds and bypass CORS.
   ```bash
   python3 server.py
   ```
   The server runs on port `3000`.

2. **Access the Dashboard:**
   Open `Nexus_News.html` in any modern web browser.
   Ensure the server is running so news data can be fetched.

## Architecture

- **Frontend:** HTML5, Tailwind-style CSS (custom variables), GSAP, Vanilla JS.
- **Backend:** Python `http.server` with `urllib` and `xml.etree` for RSS parsing.
- **Images:** Dynamic contextual fetching via `loremflickr.com`.

## Development

- **Hue Customization:** The primary interface color can be changed via the System Settings modal, affecting all gradients and shadows.
- **Region Switching:** Supports Worldwide (WW), Germany (DE), UK, France (FR), and Japan (JP) data streams.
- **Breaking News Alerts:** Automated detection and "snappy" modal alerts for critical global signals.

# Domain Extractor

A Python script that launches a headless Chromium browser to visit a webpage, load dynamic content, and capture all network requests. It extracts the third-party domains accessed by the site and outputs them in an AdGuard/Adblock compatible format.

## Features
- **Dynamic Tracking:** Uses Playwright to simulate a real browser session, capturing domains that are lazily loaded or injected by JavaScript.
- **Bot Mitigation Evasion:** Simulates scrolling and clicking to trigger hidden pop-ups, pop-unders, and lazy-loaded ad networks. `--show-browser` can be used to bypass headless detection.
- **Deep Crawling:** Optionally visits subpages on the target site (`--depth`) to capture ads that aren't on the homepage.
- **Built-in Whitelist:** Automatically ignores known good structural domains to avoid breaking sites. Current whitelist: `fonts.googleapis.com`, `fonts.gstatic.com`, `ajax.googleapis.com`, `cdnjs.cloudflare.com`, `cdn.jsdelivr.net`, `stackpath.bootstrapcdn.com`, `code.jquery.com`, `unpkg.com`, `cdn.tailwindcss.com`, `maps.googleapis.com`.
- **Blocklist Compatibility:** Exports to AdGuard (`||domain.com^`), Hosts (`0.0.0.0 domain.com`), or raw text formats using `--format`.

## Requirements
- Python 3.8+
- [Playwright for Python](https://playwright.dev/python/)

## Setup

1. **Create and activate a virtual environment (optional but recommended):**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Install Playwright:**
   ```powershell
   pip install playwright
   playwright install chromium
   ```

## Usage

Basic usage (headless, no deep crawling):
```powershell
.\venv\Scripts\python.exe extract_domains.py "https://example.com"
```

### Advanced Usage

```powershell
.\venv\Scripts\python.exe extract_domains.py [-h] [--depth DEPTH] [--show-browser] [--screenshot] [--format {adguard,hosts,text}] url
```

* `--depth DEPTH`: How many internal links deep to crawl from the main page (default: `0`). For example, `--depth 1` will click and crawl up to 3 links found on the homepage.
* `--show-browser`: Runs the browser visibly (`headless=False`). If a site blocks headless bots, use this to force it to load.
* `--screenshot`: Saves a `screenshot.png` of the executed page out, helping you verify if the site loaded correctly.
* `--format {adguard,hosts,text}`: Set the output format for the `detected_domains.txt` file. Default is `adguard`.

**Example: Deep crawling with a visible browser and Hosts format output:**
```powershell
.\venv\Scripts\python.exe extract_domains.py "https://example.com" --depth 2 --show-browser --format hosts
```

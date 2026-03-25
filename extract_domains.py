import asyncio
import argparse
from playwright.async_api import async_playwright
from urllib.parse import urlparse
import os

# Known good domains (CDNs, structural APIs) to whitelist
DEFAULT_WHITELIST = {
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "ajax.googleapis.com",
    "cdnjs.cloudflare.com",
    "cdn.jsdelivr.net",
    "stackpath.bootstrapcdn.com",
    "code.jquery.com",
    "unpkg.com",
    "cdn.tailwindcss.com",
    "maps.googleapis.com"
}

# Domains tracked globally
extracted_domains = set()
visited_urls = set()

def add_domain(url, main_domain):
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        if not hostname:
            return
            
        # Clean 'www.' prefix
        if hostname.startswith("www."):
            hostname = hostname[4:]
            
        # Ignore main domain and whitelisted structural domains
        if hostname != main_domain and hostname not in DEFAULT_WHITELIST:
            extracted_domains.add(hostname)
    except Exception:
        pass

async def crawl_page(page, url, main_domain, current_depth, max_depth, take_screenshot=False):
    if current_depth > max_depth or url in visited_urls:
        return
        
    visited_urls.add(url)
    print(f"[{current_depth}/{max_depth}] Navigating to {url}...")
    
    try:
        # Wait until network is idle to capture dynamically loaded scripts
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Simulate a click to trigger any pop-up/popunder ads
        await page.mouse.click(200, 200)
        await page.wait_for_timeout(2000)
        
        # Simulate scrolling to trigger lazy-loaded elements
        for _ in range(3):
            await page.mouse.wheel(0, 1000)
            await page.wait_for_timeout(1000)
            
        if take_screenshot and current_depth == 0:
            screenshot_path = "screenshot.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")

        # If we need to go deeper, find same-domain links
        if current_depth < max_depth:
            # Extract internal links
            hrefs = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a'))
                    .map(a => a.href)
                    .filter(href => href.startsWith('http'))
            }''')
            
            # Filter to same domain
            internal_links = []
            for href in hrefs:
                try:
                    h_domain = urlparse(href).hostname
                    h_clean = h_domain[4:] if h_domain and h_domain.startswith("www.") else h_domain
                    if h_clean == main_domain:
                        internal_links.append(href)
                except Exception:
                    pass
                    
            # Follow a few unique internal links (e.g., up to 3 per page) safely
            unique_links = list(set(internal_links))
            for next_url in unique_links[:3]:
                if next_url not in visited_urls:
                    await crawl_page(page, next_url, main_domain, current_depth + 1, max_depth)
                    
    except Exception as e:
        print(f"Notice [{url}]: {e}")


async def main(args):
    target_url = args.url
    
    # Parse the main domain for exclusion
    parsed_target = urlparse(target_url)
    main_domain = parsed_target.hostname
    if main_domain and main_domain.startswith("www."):
        main_domain = main_domain[4:]
        
    async with async_playwright() as p:
        # headless=False shows the browser (useful for evading some bot detection)
        browser = await p.chromium.launch(headless=not args.show_browser)
        context = await browser.new_context()
        page = await context.new_page()

        # Listen to all network requests
        page.on("request", lambda request: add_domain(request.url, main_domain))

        await crawl_page(page, target_url, main_domain, current_depth=0, max_depth=args.depth, take_screenshot=args.screenshot)

        await browser.close()
        
    print(f"\nExtracted {len(extracted_domains)} unique trackers/ads.")
    
    # Save depending on the selected format
    output_file = "detected_domains.txt"
    with open(output_file, "w") as f:
        for domain in sorted(extracted_domains):
            if args.format == "adguard":
                f.write(f"||{domain}^\n")
            elif args.format == "hosts":
                f.write(f"0.0.0.0 {domain}\n")
            else:
                f.write(f"{domain}\n")
                
    print(f"Domains formatted as '{args.format}' and saved to '{output_file}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract loaded third-party domains from a webpage.")
    parser.add_argument("url", help="The full URL to scrape domains from (e.g. https://example.com)")
    parser.add_argument("--depth", type=int, default=0, help="How many links deep to crawl from the homepage (default: 0)")
    parser.add_argument("--show-browser", action="store_true", help="Run browser visibly (headless=False) to bypass some bot checks")
    parser.add_argument("--screenshot", action="store_true", help="Save a screenshot.png of the main page")
    parser.add_argument("--format", choices=["adguard", "hosts", "text"], default="adguard", help="Output format for the blocklist (default: adguard)")
    
    args = parser.parse_args()
    asyncio.run(main(args))

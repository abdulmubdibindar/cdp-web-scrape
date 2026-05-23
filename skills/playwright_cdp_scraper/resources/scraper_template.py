"""
scraper_template.py - Generalized AI-Assisted Web Scraper Template (Playwright CDP)

This template serves as a starting point for building robust scrapers that bypass anti-bot
protections (e.g. Cloudflare) and bypass login forms by hijacking a running Chrome instance.

Usage:
  1. Open Chrome with remote debugging on port 9222:
     chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_profile"
  2. Log in manually to target website in that Chrome browser.
  3. Prepare an input file (e.g. inputs.txt) containing list of IDs, URLs, or search terms (one per line).
  4. Edit the parse logic in `parse_page_content()` below.
  5. Run this script:
     python scraper_template.py
"""

import csv
import json
import time
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

# ==============================================================================
# CONFIGURATION
# ==============================================================================
BASE_URL      = "https://target-website.com/details/{kode}"  # Replace with actual URL pattern
DELAY_SECONDS = 2.0  # Safe delay between page fetches to avoid rate limits

# File Paths
SCRIPT_DIR    = Path(__file__).parent
INPUT_FILE    = SCRIPT_DIR / "inputs.txt"
OUTPUT_FILE   = SCRIPT_DIR / "output.csv"
PROGRESS_FILE = SCRIPT_DIR / "progress.txt"
ERROR_FILE    = SCRIPT_DIR / "errors.txt"

# CSV Output Headers
CSV_HEADERS   = ["ID", "Field_A", "Field_B", "Field_C"]


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def load_inputs(path: Path) -> list:
    """Load target keys/codes from the input file."""
    if not path.exists():
        # Create a sample input file if it doesn't exist
        with open(path, "w", encoding="utf-8") as f:
            f.write("SAMPLE_ID_1\nSAMPLE_ID_2\n")
        print(f"[*] Created placeholder input file at: {path}. Please edit it with your target keys.")
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_progress(path: Path) -> set:
    """Load already successfully processed keys to support resumption."""
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def save_progress(path: Path, kode: str):
    """Mark a key as successfully processed."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(kode + "\n")


def log_error(path: Path, kode: str, reason: str):
    """Log failures for offline analysis or manual retry."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{kode}\t{reason}\n")


def init_output_csv(path: Path, headers: list):
    """Initialize CSV output file with headers if it doesn't exist."""
    if not path.exists():
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)


def save_record_to_csv(path: Path, record: dict):
    """Append a single record row to the CSV file."""
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        row = [record.get(h.replace(" ", "_").lower(), "") for h in CSV_HEADERS]
        # Alternative: manually order values
        # row = [record["id"], record["field_a"], record["field_b"], record["field_c"]]
        writer.writerow(row)


# ==============================================================================
# PLAYWRIGHT & PARSING LOGIC
# ==============================================================================

def wait_for_cloudflare(page: Page, timeout_ms: int = 20000):
    """
    Waits for Cloudflare challenge pages to auto-resolve.
    If it hangs, asks for manual human intervention.
    """
    while True:
        try:
            # Check if the title indicates Cloudflare challenge pages
            page.wait_for_function(
                "() => !document.title.includes('Pemeriksaan') && "
                "!document.title.includes('Checking') && "
                "!document.title.includes('Just a moment')",
                timeout=timeout_ms
            )
        except PlaywrightTimeout:
            pass

        title = page.title()
        content = page.content()
        if not ("Pemeriksaan" in title or "Checking" in title or "Just a moment" in title or "cf-challenge" in content):
            break  # Lolos Cloudflare

        print("\n  [~] Cloudflare challenge detected or browser stuck.")
        print("  [~] 1. Check your open Chrome window and complete any CAPTCHA manually.")
        print("  [~] 2. If browser stays blank, refresh the tab (press F5).")
        print("  [~] 3. Wait until the target page content is visible.")
        print("  [~] Press ENTER in this terminal when the page is fully loaded...")
        input()


def is_login_page(page: Page) -> bool:
    """
    Detect if the session has expired and redirected to a login page.
    Modify keywords based on target website's login page indicators.
    """
    url = page.url.lower()
    title = page.title().lower()
    return "login" in url or "signin" in url or "masuk" in url or "auth" in url


def parse_page_content(html: str, kode: str) -> list:
    """
    CORE PARSER: Parse page HTML with BeautifulSoup and extract data.
    ADAPT THIS FUNCTION to match the HTML structure of your target site.
    
    Returns:
        list[dict]: List of scraped records (e.g. list of dictionaries).
    """
    soup = BeautifulSoup(html, "html.parser")
    records = []

    # --- START CUSTOM PARSING CODE ---
    # Example: Scraping a simple table
    table = soup.find("table")
    if not table:
        print(f"  [!] Table not found on page for: {kode}")
        return []

    # Find rows (ignoring header)
    rows = table.find_all("tr")[1:]
    for row in rows:
        cols = row.find_all(["td", "th"])
        if len(cols) < 3:
            continue
            
        record = {
            "id": kode,
            "field_a": cols[0].get_text(strip=True),
            "field_b": cols[1].get_text(strip=True),
            "field_c": cols[2].get_text(strip=True),
        }
        records.append(record)
    # --- END CUSTOM PARSING CODE ---

    return records


def scrape_item(page: Page, kode: str) -> list | None:
    """
    Navigates to the item page, handles bot challenges, and triggers parsing.
    
    Returns:
        list[dict] : Success, list of record dictionaries
        None       : Session expired (login page detected)
        []         : Page failed to load / structure empty
    """
    url = BASE_URL.format(kode=kode)

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except PlaywrightTimeout:
        print(f"  [!] Timeout loading page.")
        return []

    # Handle Cloudflare if it appears
    title = page.title()
    content = page.content()
    if ("Pemeriksaan" in title or "Checking" in title or "Just a moment" in title or "cf-challenge" in content):
        print("  [~] Cloudflare challenge detected. Waiting for resolution...")
        wait_for_cloudflare(page)

    # Allow page scripts to fully render dynamic elements
    time.sleep(1.5)

    # Detect if session expired
    if is_login_page(page):
        return None

    # Get HTML content and parse
    html_content = page.content()
    return parse_page_content(html_content, kode)


# ==============================================================================
# MAIN ROUTINE
# ==============================================================================

def main():
    print("=" * 60)
    print("  AI-CDP Playwright Scraper Engine Template")
    print("=" * 60)

    # Initialize environment
    init_output_csv(OUTPUT_FILE, CSV_HEADERS)
    inputs = load_inputs(INPUT_FILE)
    progress = load_progress(PROGRESS_FILE)
    remaining = [k for k in inputs if k not in progress]

    print(f"\nTotal tasks      : {len(inputs)}")
    print(f"Completed tasks  : {len(progress)}")
    print(f"Remaining tasks  : {len(remaining)}")

    if not remaining:
        print("\n✅ All items have already been processed!")
        return

    # Start Playwright CDP Connection
    with sync_playwright() as pw:
        print("\nConnecting to running Chrome browser (CDP port 9222)...")
        try:
            browser = pw.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print("\n❌ FAILED TO CONNECT TO CHROME.")
            print("   Please ensure Chrome is running with remote debugging port 9222.")
            print("   Command:")
            print("     chrome.exe --remote-debugging-port=9222 --user-data-dir=\"C:\\chrome_debug_profile\"")
            sys.exit(1)

        # Attach to the default Chrome context
        context = browser.contexts[0]
        page = context.new_page()

        # Initial checks
        print("[*] Validating session...")
        page.goto("https://target-website.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)

        # Check for Cloudflare challenge at startup
        title = page.title()
        content = page.content()
        if "Pemeriksaan" in title or "Checking" in title or "Just a moment" in title or "cf-challenge" in content:
            print("  [~] Cloudflare challenge detected at startup. Resolving...")
            wait_for_cloudflare(page)
            time.sleep(2)

        # Check login state
        if is_login_page(page):
            print("\n⚠️  SESSION EXPIRED OR NOT LOGGED IN!")
            print("   Please log in manually on the opened Chrome window.")
            print("   Press ENTER in this terminal once you are logged in and see the dashboard...")
            input()

        print("[✓] Session verified. Starting scraping loop...\n")

        # Loop items
        for i, kode in enumerate(remaining, 1):
            print(f"[{i:>4}/{len(remaining)}] Processing: {kode}...", end=" ")
            sys.stdout.flush()

            records = scrape_item(page, kode)

            # Sesi login habis
            if records is None:
                print("\n" + "=" * 60)
                print("⚠️  SESSION EXPIRED MID-WAY!")
                print("   Please log in again in the Chrome browser tab.")
                print("   Press ENTER in this terminal once you have completed the login...")
                input()
                # Retry same item
                records = scrape_item(page, kode)
                if records is None:
                    print("❌ Authentication failed again. Terminating script.")
                    break

            # Gagal/Kosong
            if not records:
                print("❌ Failed (Check errors.txt)")
                log_error(ERROR_FILE, kode, "Empty page or element not found")
                save_progress(PROGRESS_FILE, kode)
                time.sleep(DELAY_SECONDS)
                continue

            # Berhasil, simpan data ke file
            for record in records:
                save_record_to_csv(OUTPUT_FILE, record)

            save_progress(PROGRESS_FILE, kode)
            print(f"✓ Success ({len(records)} records saved)")
            time.sleep(DELAY_SECONDS)

        # Close the page tab (keep browser open for other manual use)
        page.close()

    print("\n" + "=" * 60)
    print("  Scraping process finished!")
    print(f"  Check output in: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()

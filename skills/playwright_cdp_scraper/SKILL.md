---
name: playwright-cdp-scraper
description: >-
  A skill for building and adapting robust web scrapers using Playwright over Chrome DevTools Protocol (CDP). 
  Connects to a running instance of Chrome to bypass Cloudflare, CAPTCHAs, and SSO login systems, 
  allowing automated extraction of structured tables and pages.
---

# Playwright Chrome DevTools Protocol (CDP) Scraper Skill

Use this skill to adapt the existing ITERA SIAKAD scraping workflow for other websites, portals, or databases that are heavily protected by bot detection (like Cloudflare, Turnstile, Akamai) or require complex/manual login (Single Sign-On).

## 1. Concept: How CDP Scraping Works

Standard web scraping tools spawn a separate browser profile that has automation flags (e.g. `navigator.webdriver = true`). Security services like Cloudflare easily detect this and present a blocking challenge (hcaptcha, turnstile).

**CDP (Chrome DevTools Protocol)** avoids this by connecting Playwright to a **real, user-launched instance of Google Chrome** that has been opened with a special remote debugging flag.
* The security services see a normal human browser.
* You can login manually in this browser tab first.
* Once logged in, the Playwright python script attaches to the active session and does the heavy-lifting scraping at high speeds.

---

## 2. Chrome Debug Launch Commands

Before running the scraper script, close all regular Chrome windows and run this command in terminal to launch Chrome in debug mode.

* **Windows (PowerShell):**
  ```powershell
  & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_profile"
  ```
* **macOS:**
  ```bash
  /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/chrome_debug_profile"
  ```
* **Linux:**
  ```bash
  google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/chrome_debug_profile"
  ```

---

## 3. Adapting to a New Site: Step-by-Step

To adapt the scraper for a different target site, modify the template code in `resources/scraper_template.py` by applying these steps:

### Step 3.1: Define URL Pattern and Target IDs
Identify the base URL of the pages you want to scrape. Create a list of target parameters (e.g. product IDs, course codes, user handles) in a txt file.
In the python script, update:
```python
BASE_URL = "https://target-website.com/item/{kode}"
INPUT_FILE = "target_ids.txt"
```

### Step 3.2: Customizing the BeautifulSoup Parser
Inspect the HTML structure of the target page on your Chrome debug browser.
In the python script, modify the parser function `scrape_data_from_page(page, kode)`:
1. Locate the main table or list element:
   ```python
   container = soup.find("table", {"id": "data-table"})
   ```
2. Extract the headers (to locate correct columns dynamically):
   ```python
   headers = [th.text.strip().lower() for th in container.find_all("th")]
   ```
3. Iterate over the data rows (`<tr>` or `<div>`):
   ```python
   records = []
   for row in container.find_all("tr")[1:]:  # skip header
       cols = row.find_all("td")
       records.append({
           "field1": cols[0].text.strip(),
           "field2": cols[1].text.strip(),
       })
   return records
   ```

### Step 3.3: Output Destination
Choose whether to write to Google Sheets (using OAuth credentials) or to a local file (like CSV or JSON).
* **Google Sheets:** Ensure `credentials.json` is configured, call `gspread.oauth()` and use `worksheet.update()`.
* **CSV Local (Simple & Robust):**
  ```python
  import csv
  with open("output.csv", "a", newline="", encoding="utf-8") as f:
      writer = csv.writer(f)
      writer.writerow([record["field1"], record["field2"]])
  ```

---

## 4. Troubleshooting and Edge Cases

### 1. Cloudflare/Turnstile Challenge Stuck
If the page gets stuck on a Cloudflare verification page:
* Use the auto-resolve function `wait_for_cloudflare(page)` which waits until the title no longer contains Cloudflare keyword.
* If it requires manual human tick, the script pauses and asks you to tick it manually in the Chrome window and press Enter in the terminal to resume.

### 2. Session Expired / Redirect to Login
Add a session verification helper `is_login_page(page)`:
```python
def is_login_page(page: Page) -> bool:
    return "login" in page.url.lower() or "signin" in page.url.lower()
```
If this returns True, pause the script, alert the user to log in manually in the debug browser, and wait for terminal input to resume.

---

## 5. Starter Template

A generalized, fully commented Python scraper script is available at:
[scraper_template.py](file:///C:/Users/LENOVO/OneDrive%20-%20Institut%20Teknologi%20Sumatera/Reakreditasi%20BANPT%20IAPS%205.0%20(2025)/generate-dna-2022-2023/skills/playwright_cdp_scraper/resources/scraper_template.py)

Refer to it whenever you need to write a scraper from scratch.

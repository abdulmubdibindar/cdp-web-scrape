"""
scrape_dna.py - Scrape DNA (Daftar Nilai Akhir) dari SIAKAD ITERA
Semester Ganjil 2022/2023

Menggunakan Playwright (browser sungguhan) untuk melewati Cloudflare.

Cara install (jalankan sekali):
  pip install playwright gspread beautifulsoup4
  playwright install chromium

Cara pakai:
  python scrape_dna.py
"""

import json
import time
import sys
from pathlib import Path
from bs4 import BeautifulSoup
import gspread
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

# ─── KONFIGURASI ──────────────────────────────────────────────────────────────

SHEET_ID       = "10mBGw9kFtthglDdaFFH5PjKAIQN4HrJX-aGCRPuMA6M"
BASE_URL       = "https://siakad.itera.ac.id/dosen/kelas/lihat/{kode}"
DELAY_SECONDS  = 2.0   # jeda antar request (detik)

# Tabel konversi nilai huruf → angka
NILAI_MAP = {
    "A":  82.00,
    "AB": 71.60,
    "B":  67.05,
    "BC": 62.95,
    "C":  53.15,
    "D":  44.50,
    "E":  17.45,
}

SCRIPT_DIR    = Path(__file__).parent
COOKIES_FILE  = SCRIPT_DIR / "cookies.json"
CREDS_FILE    = SCRIPT_DIR / "credentials.json"
TOKEN_FILE    = SCRIPT_DIR / "token.json"
KODE_FILE     = SCRIPT_DIR / "kode-kelas-batch-3.txt"
PROGRESS_FILE = SCRIPT_DIR / "progress.txt"
ERROR_FILE    = SCRIPT_DIR / "errors.txt"


# ─── FUNGSI UTILITAS ──────────────────────────────────────────────────────────

def load_raw_cookies(path: Path) -> list:
    """Baca cookies.json dari Cookie-Editor sebagai list mentah."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_playwright_cookies(raw_cookies: list) -> list:
    """Konversi format Cookie-Editor → format Playwright."""
    result = []
    for c in raw_cookies:
        pc = {
            "name":     c["name"],
            "value":    c["value"],
            "domain":   c["domain"],
            "path":     c.get("path", "/"),
            "httpOnly": c.get("httpOnly", False),
            "secure":   c.get("secure", False),
        }
        if "expirationDate" in c and c["expirationDate"]:
            pc["expires"] = int(c["expirationDate"])
        result.append(pc)
    return result


def load_kode_kelas(path: Path) -> list:
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_progress(path: Path) -> set:
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def save_progress(path: Path, kode: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(kode + "\n")


def save_error(path: Path, kode: str, alasan: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{kode}\t{alasan}\n")


def connect_gspread() -> gspread.Client:
    print("Menghubungkan ke Google Sheets (OAuth)...")
    print("  → Browser akan terbuka untuk otorisasi jika ini pertama kali.\n")
    gc = gspread.oauth(
        credentials_filename=str(CREDS_FILE),
        authorized_user_filename=str(TOKEN_FILE),
    )
    return gc


# ─── FUNGSI PLAYWRIGHT ────────────────────────────────────────────────────────

def wait_for_cloudflare(page: Page, timeout_ms: int = 20000):
    """
    Tunggu hingga Cloudflare challenge selesai (biasanya auto-resolve
    dalam beberapa detik untuk browser sungguhan).
    Jika nyangkut, akan terus meminta interaksi manual hingga berhasil lewat.
    """
    while True:
        try:
            # Tunggu sampai judul halaman bukan lagi halaman Cloudflare
            page.wait_for_function(
                "() => !document.title.includes('Pemeriksaan') && !document.title.includes('Checking') && !document.title.includes('Just a moment')",
                timeout=timeout_ms
            )
        except PlaywrightTimeout:
            pass  # Timeout, kita akan minta user bertindak

        title = page.title()
        content = page.content()
        if not ("Pemeriksaan" in title or "Checking" in title or "Just a moment" in title or "cf-challenge" in content):
            # Sudah lolos dari Cloudflare
            break

        print("\n  [~] Cloudflare challenge sepertinya macet atau butuh interaksi manual.")
        print("  [~] 1. Cek jendela browser Anda, selesaikan Captcha (Tandai sebagai manusia).")
        print("  [~] 2. Jika sudah dicentang tapi browser diam saja/halaman putih, coba REFRESH (F5) browser Anda.")
        print("  [~] 3. TUNGGU sampai halaman SIAKAD benar-benar terbuka (muncul tabel kelas).")
        print("  [~] Tekan Enter di terminal ini HANYA JIKA TABEL KELAS SUDAH MUNCUL...")
        input()

def is_login_page(page: Page) -> bool:
    url   = page.url.lower()
    title = page.title().lower()
    return "login" in url or "masuk" in url or ("username" in title or "login" in title)


def scrape_dna_from_page(page: Page, kode: str) -> list | None:
    """
    Navigasi ke halaman DNA kelas dan scrape tabelnya.

    Returns:
        list[dict]  : data mahasiswa jika berhasil
        None        : sesi SIAKAD habis (redirect ke login)
        []          : tabel tidak ditemukan / halaman kosong
    """
    url = BASE_URL.format(kode=kode)

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except PlaywrightTimeout:
        print(f"  [!] Timeout saat membuka halaman.")
        return []

    # Tangani Cloudflare challenge jika muncul
    title = page.title()
    content = page.content()
    if ("Pemeriksaan" in title or "Checking" in title or "Just a moment" in title or "cf-challenge" in content):
        print("  [~] Cloudflare challenge terdeteksi, menunggu auto-resolve...")
        wait_for_cloudflare(page)

    # Tunggu sebentar agar halaman selesai render
    time.sleep(1.0)

    # Cek redirect ke login
    if is_login_page(page):
        return None

    # Ambil HTML dan parse
    html  = page.content()
    soup  = BeautifulSoup(html, "html.parser")

    # Cari tabel yang punya kolom Nama + Nilai
    table = None
    for tbl in soup.find_all("table"):
        all_th = tbl.find_all("th")
        if not all_th:
            first_row = tbl.find("tr")
            all_th = first_row.find_all("td") if first_row else []
        header_texts = [c.get_text(strip=True).lower() for c in all_th]
        if any("nilai" in h for h in header_texts) and any("nama" in h for h in header_texts):
            table = tbl
            break

    if table is None:
        # Simpan HTML untuk debug jika gagal
        debug_path = SCRIPT_DIR / f"debug_{kode}.html"
        debug_path.write_text(html, encoding="utf-8")
        print(f"  [!] Tabel tidak ditemukan. HTML disimpan ke debug_{kode}.html")
        return []

    # Deteksi indeks kolom dari header
    header_row  = table.find("tr")
    headers     = [c.get_text(strip=True).lower() for c in header_row.find_all(["th", "td"])]

    def find_col(*keywords):
        for kw in keywords:
            for i, h in enumerate(headers):
                if kw in h:
                    return i
        return None

    idx_nim   = find_col("nim")
    idx_nama  = find_col("nama")
    idx_nilai = find_col("nilai akhir", "nilai huruf", "nilai")

    if idx_nilai is None:
        print(f"  [!] Kolom 'Nilai' tidak ditemukan. Headers: {headers}")
        return []

    records = []
    for row in table.find_all("tr")[1:]:
        cols = row.find_all(["td", "th"])
        if not cols:
            continue
        max_idx = max(x for x in [idx_nim, idx_nama, idx_nilai] if x is not None)
        if len(cols) <= max_idx:
            continue

        nim         = cols[idx_nim].get_text(strip=True)  if idx_nim  is not None else ""
        nama        = cols[idx_nama].get_text(strip=True) if idx_nama is not None else ""
        nilai_huruf = cols[idx_nilai].get_text(strip=True).upper().strip()
        nilai_angka = NILAI_MAP.get(nilai_huruf, "")

        if not nama and not nim:
            continue

        records.append({
            "nim":         nim,
            "nama":        nama,
            "nilai_huruf": nilai_huruf,
            "nilai_angka": nilai_angka,
        })

    return records


# ─── FUNGSI GOOGLE SHEETS ─────────────────────────────────────────────────────

def write_to_sheet(spreadsheet: gspread.Spreadsheet, kode: str, records: list):
    try:
        ws = spreadsheet.add_worksheet(title=kode, rows=max(len(records) + 5, 10), cols=10)
    except gspread.exceptions.APIError:
        ws = spreadsheet.worksheet(kode)
        ws.clear()

    header = ["NIM", "Nama Lengkap", "Nilai Huruf", "Nilai Angka"]
    rows_to_write = [header] + [
        [r["nim"], r["nama"], r["nilai_huruf"], r["nilai_angka"]]
        for r in records
    ]
    ws.update(rows_to_write, "A1")
    print(f"  [✓] {len(records)} mahasiswa ditulis ke tab '{kode}'")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  SIAKAD DNA Scraper — Ganjil 2022/2023")
    print("  (menggunakan Playwright + Chromium)")
    print("=" * 60)

    # Validasi file
    for f, nama in [(COOKIES_FILE, "cookies.json"), (CREDS_FILE, "credentials.json"), (KODE_FILE, "kode-kelas.txt")]:
        if not f.exists():
            print(f"\n❌ File '{nama}' tidak ditemukan di: {f}")
            sys.exit(1)

    # Muat daftar kelas
    kode_list = load_kode_kelas(KODE_FILE)
    progress  = load_progress(PROGRESS_FILE)
    remaining = [k for k in kode_list if k not in progress]

    print(f"\nTotal kelas    : {len(kode_list)}")
    print(f"Sudah selesai  : {len(progress)}")
    print(f"Sisa           : {len(remaining)}")

    if not remaining:
        print("\n✅ Semua kelas sudah diproses!")
        return

    # Koneksi Google Sheets (sebelum buka browser)
    gc          = connect_gspread()
    spreadsheet = gc.open_by_key(SHEET_ID)
    print(f"  [✓] Terhubung ke: \"{spreadsheet.title}\"\n")

    # Karena pakai CDP, cookies.json tidak dipakai lagi
    # raw_cookies        = load_raw_cookies(COOKIES_FILE)
    # playwright_cookies = build_playwright_cookies(raw_cookies)

    error_list = []

    with sync_playwright() as pw:
        print("Menyambungkan ke browser Chrome Anda yang sedang berjalan (CDP port 9222)...")
        try:
            browser = pw.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print("\n❌ Gagal menyambung ke Chrome. Pastikan Anda sudah menjalankan Chrome dengan --remote-debugging-port=9222")
            print("   dan PASTIKAN semua jendela Chrome biasa sudah ditutup sebelum menjalankan perintah debugging.")
            sys.exit(1)
            
        context = browser.contexts[0]
        page = context.new_page()

        # Buka halaman pertama untuk validasi sesi
        print("Membuka SIAKAD untuk verifikasi sesi...")
        page.goto("https://siakad.itera.ac.id/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(2)

        # Cek Cloudflare sebelum cek login
        title = page.title()
        content = page.content()
        if "Pemeriksaan" in title or "Checking" in title or "Just a moment" in title or "cf-challenge" in content:
            print("  [~] Cloudflare challenge terdeteksi di awal...")
            wait_for_cloudflare(page)
            time.sleep(2) # Beri waktu render setelah selesai Cloudflare

        if is_login_page(page):
            print("\n⚠️  Sesi SIAKAD sudah tidak aktif!")
            print("Silakan login manual di browser yang terbuka, lalu tekan Enter di sini...")
            input()

        print("  [✓] Sesi SIAKAD aktif. Mulai scraping...\n")

        # ─── Loop Scraping ──────────────────────────────────────
        for i, kode in enumerate(remaining, 1):
            print(f"[{i:>3}/{len(remaining)}] Kelas {kode}...", end="  ")

            records = scrape_dna_from_page(page, kode)

            # Sesi habis
            if records is None:
                print()
                print("\n" + "=" * 60)
                print("⚠️  SESI SIAKAD HABIS!")
                print("Silakan login ulang di browser yang terbuka,")
                print("lalu tekan Enter di sini untuk melanjutkan...")
                input()
                # Coba ulang kelas yang sama
                records = scrape_dna_from_page(page, kode)
                if records is None:
                    print("Masih gagal. Script dihentikan.")
                    break

            # Tabel tidak ditemukan
            if not records:
                error_list.append(kode)
                save_error(ERROR_FILE, kode, "Tabel tidak ditemukan atau kosong")
                save_progress(PROGRESS_FILE, kode)
                time.sleep(DELAY_SECONDS)
                continue

            # Berhasil
            write_to_sheet(spreadsheet, kode, records)
            save_progress(PROGRESS_FILE, kode)
            time.sleep(DELAY_SECONDS)

        browser.close()

    # ─── Laporan Akhir ──────────────────────────────────────────
    final_progress = load_progress(PROGRESS_FILE)
    print()
    print("=" * 60)
    print(f"  Selesai: {len(final_progress)}/{len(kode_list)} kelas diproses")
    if error_list:
        print(f"  Kelas bermasalah ({len(error_list)}): lihat errors.txt")
    print("=" * 60)


if __name__ == "__main__":
    main()

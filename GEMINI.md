# Panduan Reproduksi & Panduan Agent (GEMINI.md)

Dokumen ini ditujukan untuk Anda (developer) dan **Agent AI** yang membaca repositori ini untuk mereproduksi, memodifikasi, atau memindahkan (*porting*) keberhasilan proyek web scraping berbasis **Chrome DevTools Protocol (CDP)** ini ke target website lain atau repositori baru.

---

## 1. Arsitektur & Metode Proyek

Proyek ini dirancang untuk melakukan scraping data tabel dari portal web yang dilindungi oleh otentikasi login (SSO) dan sistem anti-bot/Cloudflare (seperti portal akademik **SIAKAD ITERA**).

### Mengapa Menggunakan Metode CDP?
1. **Melewati Deteksi Bot (Cloudflare / Turnstile):** Playwright normal (baik *headless* maupun *headed*) menyuntikkan properti browser (`navigator.webdriver`) yang memicu deteksi bot. Metode CDP mengendalikan browser Google Chrome asli Anda yang berjalan di komputer lokal. Browser ini memiliki *fingerprint* normal manusia sehingga lolos dari pemeriksaan keamanan.
2. **Otentikasi Otomatis via Sesi Aktif:** Tidak perlu mengelola token JWT atau file cookies secara manual. Selama Anda sudah login ke akun Anda di browser Chrome debug tersebut, skrip Python dapat langsung mengakses data di balik halaman login.
3. **Resiliensi Tinggi & Interaksi Manual:** Jika sesi habis atau muncul tantangan bot captcha yang tidak terduga, skrip akan menjeda proses dan meminta interaksi manusia di browser Chrome tersebut, lalu melanjutkan scraping setelah tombol Enter ditekan.

---

## 2. Persyaratan & Instalasi

### Prasyarat Sistem
* Python 3.8+
* Google Chrome terinstal di sistem operasi (Windows/macOS/Linux).
* Akses internet dan hak untuk membuat berkas di direktori lokal.

### Instalasi Dependensi
Jalankan perintah berikut di terminal Anda untuk menginstal semua pustaka yang diperlukan:

```bash
pip install playwright gspread beautifulsoup4
playwright install chromium
```

---

## 3. Langkah-Langkah Reproduksi Proyek

### Langkah 1: Siapkan Google Sheets API (Untuk Penyimpanan Data)
Skrip ini menulis hasil scraping langsung ke Google Sheets secara dinamis.
1. Masuk ke [Google Cloud Console](https://console.cloud.google.com/).
2. Buat proyek baru dan aktifkan **Google Sheets API** dan **Google Drive API**.
3. Buat kredensial OAuth 2.0 (Application Type: **Desktop Application**).
4. Unduh file konfigurasi kredensial tersebut, ubah namanya menjadi `credentials.json`, lalu letakkan di root direktori proyek ini.
5. Siapkan spreadsheet kosong di Google Sheets dan salin **Spreadsheet ID** dari URL-nya (contoh URL: `https://docs.google.com/spreadsheets/d/ID_SPREADSHEET_ANDA/edit`). Masukkan ID ini pada variabel `SHEET_ID` di file skrip.

### Langkah 2: Jalankan Google Chrome dalam Mode Debugging
Sebelum menjalankan skrip Python, Anda **wajib** menutup semua jendela Google Chrome biasa, lalu menjalankan satu instance Google Chrome dengan port debugging terbuka.

*   **Untuk Windows (PowerShell):**
    ```powershell
    & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_profile"
    ```
*   **Untuk Windows (Git Bash):**
    ```bash
    "/c/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_profile"
    ```
*   **Untuk macOS:**
    ```bash
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="$HOME/chrome_debug_profile"
    ```
*   **Untuk Linux:**
    ```bash
    google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/chrome_debug_profile"
    ```

*Catatan: Parameter `--user-data-dir` memaksa Chrome membuat profil baru yang terisolasi agar fitur remote-debugging port `9222` aktif dengan sempurna.*

### Langkah 3: Login Manual
Pada jendela Chrome baru yang terbuka tersebut:
1. Akses website target (misalnya `https://siakad.itera.ac.id/`).
2. Lakukan login menggunakan akun Anda secara manual.
3. Pastikan Anda berada di halaman dashboard atau session Anda aktif.

### Langkah 4: Konfigurasi Target Scraping
1. Buat file `kode-kelas.txt` di direktori proyek. Isi file ini dengan daftar kode/ID halaman yang ingin Anda scrape (satu ID per baris).
2. Jalankan skrip scraping:
   ```bash
   python scrape_dna.py
   ```
3. Saat pertama kali dijalankan, terminal akan meminta otentikasi Google Account di browser Anda untuk mengizinkan penulisan ke Google Sheets. Setelah diizinkan, berkas `token.json` akan otomatis terbentuk sehingga proses berikutnya berjalan otomatis tanpa otorisasi ulang.

---

## 4. Struktur File Proyek

Berikut penjelasan singkat mengenai peran berkas-berkas di repositori ini:
*   `scrape_dna.py`: Kode utama scraper yang mengendalikan browser via CDP, melakukan parsing HTML dengan BeautifulSoup, dan menulis data ke Google Sheets.
*   `kode-kelas.txt`: Daftar input berupa ID unik / parameter URL halaman kelas yang akan dikunjungi secara iteratif.
*   `progress.txt`: Menyimpan daftar ID yang **berhasil** diproses. Berguna sebagai penanda *resume* jika koneksi terputus di tengah jalan.
*   `errors.txt`: Menyimpan daftar ID yang gagal diproses beserta alasannya (misal: tabel kosong / tidak ditemukan).
*   `credentials.json`: File rahasia dari Google Cloud Console untuk OAuth2.
*   `token.json`: Token sesi Google OAuth yang dibuat otomatis setelah login pertama.
*   `requirements.txt`: Daftar pustaka Python yang wajib diinstal.

---

## 5. Petunjuk Untuk Agent AI (Instruksi Modifikasi/Adaptasi)

Jika Anda adalah Agent AI yang ditugaskan untuk mengadaptasi proyek ini untuk target scraping baru (misalnya e-commerce, portal data pemerintah, atau sistem internal lainnya), ikuti panduan berikut:

### Bagian 1: Analisis Struktur Halaman Target
1. Buka browser debug Chrome dan navigasikan ke halaman target secara manual.
2. Gunakan Inspect Element (`Ctrl+Shift+I` atau `Cmd+Option+I`) untuk memeriksa struktur HTML tabel atau data yang ingin diambil.
3. Identifikasi tag HTML pembungkus (misal `<table>`, `<div>` dengan kelas tertentu, atau baris data `<tr>`).

### Bagian 2: Sesuaikan Logika BeautifulSoup di Kode Scraper
Modifikasi fungsi ekstraksi data pada file scraper Anda. Gantilah fungsi `scrape_dna_from_page` dengan logika yang sesuai:
*   Temukan kontainer data: `soup.find("table")` atau `soup.find_all("div", class_="data-row")`.
*   Iterasi baris data: ambil teks dari setiap elemen anak dan bersihkan spasi kosong dengan `.get_text(strip=True)`.
*   Petakan kolom data ke dalam bentuk dictionary Python, contoh:
    ```python
    {
        "id": row.find("td", class_="id-class").text,
        "name": row.find("td", class_="name-class").text,
    }
    ```

### Bagian 3: Gunakan Skill `playwright-cdp-scraper`
Untuk membantu Anda memodifikasi skrip ini secara sistematis atau membuat versi baru untuk keperluan scraping yang berbeda, gunakan skill `playwright-cdp-scraper` yang tersedia di direktori `skills/playwright_cdp_scraper/`. Skill tersebut menyediakan template kode generator universal dan langkah-langkah adaptasi kode yang aman.

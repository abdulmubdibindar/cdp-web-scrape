# Panduan Penggunaan Git & Media Komunikasi

Selamat datang di direktori khusus **`git-guide`**! Halaman ini dibuat sebagai panduan praktis penggunaan Git pada proyek **`cdp-web-scrape`** Anda, sekaligus sebagai media komunikasi interaktif antara Anda dan saya (Antigravity) mengenai Git.

---

## 📂 Cara Menggunakan Folder Ini untuk Komunikasi

Anda dapat menggunakan folder `git-guide` ini untuk berdiskusi, mengajukan pertanyaan, atau meminta bantuan terkait Git. Caranya sangat mudah:

1. **Ajukan Pertanyaan/Catatan Anda:**
   * Anda bisa membuat berkas baru (misalnya `git-guide/tanya.md`) atau langsung menyunting bagian **[Daftar Pertanyaan & Diskusi](#-daftar-pertanyaan--diskusi)** di bawah ini.
   * Tulis apa yang ingin Anda tanyakan atau lakukan dengan Git (contoh: cara menghubungkan ke GitHub, cara melakukan rollback, dsb.).
2. **Beri Tahu Saya:**
   * Di dalam obrolan chat kita, beri tahu saya bahwa Anda telah menambahkan catatan atau pertanyaan di folder `git-guide`.
3. **Respon Saya:**
   * Saya akan membaca berkas tersebut, lalu memberikan penjelasan detail, langkah-langkah Command Line, atau memandu Anda langsung melalui pembaruan berkas di folder ini.

---

## 🔍 Status Repositori Saat Ini

Berdasarkan pengecekan sistem, status Git pada proyek Anda saat ini adalah:
* **Branch Utama:** `main`
* **Status Komit:** Belum ada komit sama sekali (*No commits yet*).
* **Berkas yang Belum Dilacak (Untracked Files):**
  * `.gitignore`
  * `GEMINI.md`
  * `README.md`
  * `requirements.txt`
  * `scrape_dna.py`
  * `web_scrape.yml`
  * `skills/`
* **Berkas yang Diabaikan (.gitignore):**
  * Kredensial & Token: `credentials.json`, `token.json` (sangat penting agar data sensitif tidak bocor ke publik!).
  * Log & Progress: `progress.txt`, `errors.txt`, folder `output/`.
  * Berkas temporal Python: `__pycache__/`, `*.pyc`.

---

## 🛠️ Langkah Awal: Membuat Commit Pertama Anda

Karena repositori ini baru saja diinisialisasi dan belum memiliki riwayat commit, berikut adalah langkah-langkah untuk melakukan commit pertama Anda:

### Langkah 1: Tambahkan Berkas ke Staging Area
Untuk menandai berkas-berkas proyek agar siap disimpan ke dalam riwayat Git:
```powershell
git add .
```
> [!NOTE]
> Perintah di atas akan menambahkan semua berkas proyek *kecuali* berkas yang terdaftar di `.gitignore` (seperti `credentials.json` dan `token.json`).

### Langkah 2: Lakukan Commit Pertama
Simpan snapshot berkas-berkas tersebut ke dalam database Git lokal Anda dengan pesan deskriptif:
```powershell
git commit -m "initial commit: setup scraper project structure and guides"
```

### Langkah 3: Periksa Status
Pastikan semua perubahan berhasil disimpan:
```powershell
git status
```
Jika berhasil, terminal akan menampilkan pesan:
`nothing to commit, working tree clean`

---

## 📘 Cheatsheet Perintah Git yang Sering Digunakan

Berikut adalah rangkuman perintah Git dasar yang akan membantu Anda mendokumentasikan riwayat proyek ini:

| Perintah | Deskripsi | Kapan Digunakan? |
| :--- | :--- | :--- |
| `git status` | Menampilkan berkas yang diubah, dihapus, atau belum dilacak. | Kapan pun Anda ingin melihat kondisi repositori saat ini. |
| `git diff` | Menampilkan perubahan baris kode secara detail sebelum melakukan commit. | Sebelum melakukan `git add` untuk memastikan perubahan sudah benar. |
| `git add <nama-file>` | Memasukkan berkas tertentu ke staging area. | Sebelum commit. Gunakan `git add .` untuk memasukkan semua berkas. |
| `git commit -m "pesan"` | Menyimpan perubahan yang ada di staging area ke riwayat proyek. | Setiap kali Anda selesai menyelesaikan satu fitur atau perbaikan. |
| `git log --oneline` | Menampilkan daftar riwayat commit secara ringkas dan rapi. | Ketika Anda ingin melihat riwayat pekerjaan atau mencari ID commit tertentu. |
| `git checkout -b <nama-branch>` | Membuat branch baru dan langsung berpindah ke branch tersebut. | Ketika ingin bereksperimen dengan fitur baru tanpa merusak branch `main`. |

---

## 💬 Daftar Pertanyaan & Diskusi

> [!TIP]
> Tulis pertanyaan, kendala, atau topik diskusi Anda di bawah garis ini. Saya akan membacanya dan memperbarui panduan ini dengan solusi yang tepat.

***

### 📝 Catatan/Pertanyaan dari Anda:
*(Tulis di sini jika Anda ingin berdiskusi atau menanyakan perintah Git tertentu)*

1. [Contoh] Bagaimana cara menghubungkan repositori lokal ini ke akun GitHub saya?
2. Bagaimana cara menyatukan perubahan `.gitignore` (penambahan slash) ke commit sebelumnya?
   * *Jawaban:* Panduan detail langkah-langkahnya sudah ditulis di berkas [amend-commit.md](file:///C:/Users/LENOVO/cdp-web-scrape/git-guide/amend-commit.md). Silakan diikuti dan dijalankan sendiri di terminal Anda.

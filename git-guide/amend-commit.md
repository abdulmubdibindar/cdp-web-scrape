# Panduan Menyatukan Perubahan ke Commit Sebelumnya (Git Amend)

Panduan ini menjelaskan langkah-langkah untuk memasukkan perubahan terbaru Anda pada `.gitignore` (penambahan slash pada baris ke-2 `/git-guide/.`) ke dalam commit terakhir yang telah Anda buat sebelumnya.

---

## 🛠️ Langkah-Langkah Eksekusi

Silakan buka terminal/PowerShell di direktori root proyek (`C:\Users\LENOVO\cdp-web-scrape`), lalu jalankan perintah berikut secara berurutan:

### Langkah 1: Tambahkan `.gitignore` ke Staging Area
Perintah ini menandakan bahwa file `.gitignore` siap untuk dimasukkan ke dalam commit.
```powershell
git add .gitignore
```

### Langkah 2: Gabungkan Perubahan ke Commit Sebelumnya
Pilih salah satu dari dua opsi berikut sesuai kebutuhan Anda:

*   **Opsi A: Menggunakan pesan commit yang sama (Tanpa edit teks)**
    Jika Anda ingin langsung menggabungkannya tanpa mengubah pesan commit sebelumnya:
    ```powershell
    git commit --amend --no-edit
    ```

*   **Opsi B: Mengubah pesan commit sebelumnya**
    Jika Anda ingin menggabungkannya sekaligus mengedit atau memperbarui pesan commit sebelumnya:
    ```powershell
    git commit --amend
    ```
    *(Editor teks default Git Anda akan terbuka untuk memperbarui pesan commit).*

---

## 🔍 Cara Verifikasi Hasil

Setelah menjalankan salah satu perintah di atas, Anda bisa memastikan perubahan sudah menyatu dengan benar menggunakan perintah berikut:

1.  **Periksa Status Repositori**
    ```powershell
    git status
    ```
    *Pastikan output menunjukkan `nothing to commit, working tree clean`.*

2.  **Lihat Detail Commit Terakhir**
    Untuk melihat apakah perubahan `.gitignore` sudah masuk ke dalam commit terakhir:
    ```powershell
    git show HEAD
    ```
    *Anda akan melihat perbedaan (diff) yang menyertakan perubahan `.gitignore` Anda di dalam commit tersebut.*

3.  **Periksa Riwayat Commit**
    ```powershell
    git log -n 5 --oneline
    ```
    *Untuk memastikan tidak ada commit baru yang terbentuk (tetap pada commit sebelumnya).*

---

> [!WARNING]
> **Catatan Penting:** Hanya gunakan `--amend` pada commit lokal yang **belum di-push** ke repositori remote bersama (seperti GitHub). Jika commit tersebut sudah di-push, melakukan amend akan mengubah riwayat commit dan memerlukan push paksa (`git push --force`), yang dapat mengganggu pekerjaan kolaborator lain.

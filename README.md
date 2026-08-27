# VN Translation Tool

<div align="center">

  [![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![Vue.js](https://img.shields.io/badge/Frontend-Vue.js%203-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)](https://vuejs.org/)
  [![TailwindCSS](https://img.shields.io/badge/UI-Tailwind%20CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
  [![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](LICENSE)

  <br>

  **[🇮🇩 Bahasa Indonesia](README.md)** | **[🇬🇧 English](README_EN.md)**

</div>

**VN Translation Tool** adalah aplikasi web lokal modern yang dirancang khusus untuk mempermudah proses penerjemahan, penyuntingan (*editing/polishing*), dan lokalisasi naskah **Visual Novel (VN)** (seperti engine Circus / D.C. Series, LucaSystem, dan format game berbasis JSON lainnya). 

Aplikasi ini menggabungkan antarmuka *side-by-side editor*, pembacaan furigana otomatis, sistem glosarium naskah, pencarian cerdas berbasis Romaji & Regex, serta integrasi penuh dengan kecerdasan buatan (**Local LLM / WebAI-to-API Gemini**) tanpa perlu bolak-balik copy-paste manual.

---

## 📑 Daftar Isi
- [Fitur Utama](#-fitur-utama)
- [Struktur Antarmuka](#-struktur-antarmuka)
- [Persyaratan Sistem](#-persyaratan-sistem)
- [Instalasi & Menjalankan](#-instalasi--menjalankan)
- [Panduan Penggunaan (Step-by-Step)](#-panduan-penggunaan-step-by-step)
  - [1. Konfigurasi Proyek & Folder Game](#1-konfigurasi-proyek--folder-game)
  - [2. Navigasi & Penerjemahan Naskah](#2-navigasi--penerjemahan-naskah)
  - [3. Menerjemahkan dengan AI / LLM](#3-menerjemahkan-dengan-ai--llm)
  - [4. Glosarium Istilah & Nama Karakter](#4-glosarium-istilah--nama-karakter)
  - [5. Pencarian Global & Find-and-Replace](#5-pencarian-global--find-and-replace)
- [Pintasan Keyboard (Shortcuts)](#-pintasan-keyboard-shortcuts)
- [Troubleshooting & FAQ](#-troubleshooting--faq)
- [Kontribusi & Lisensi](#-kontribusi--lisensi)

---

## ✨ Fitur Utama

### 🎮 1. Manajemen Multi-Proyek & Isolasi Cache
* **Dukungan Banyak Game**: Kelola berbagai proyek game sekaligus (misalnya *D.C.4 Plus Harmony*, *Da Capo 4*, *D.C.III Platinum Partner*, *D.C.III Dream Days*, dll.) dalam satu aplikasi.
* **Isolasi Cache Mandiri (`project_data/<slug>`)**: Setiap proyek memiliki folder cache tersendiri sehingga data rich save, status pengerjaan, dan riwayat terjemahan antar-game tidak akan saling menimpa.
* **Dropdown Sync & Custom Path**: Sinkronkan folder cache yang sudah ada atau buat nama folder baru langsung dari menu pengaturan.

### 📝 2. Editor Naskah Side-by-Side Modern
* **Kolom Asli (Raw JP) vs Kolom Terjemahan**: Tampilan sejajar yang bersih memudahkan perbandingan konteks kalimat.
* **5 Lapisan Terjemahan (*Translation Tiers*)**:
  * `Initial` — Teks terjemahan dasar / impor awal dari game.
  * `Machine` — Hasil terjemahan mesin (Google Translate / DeepL / LLM).
  * `Better` — Draf perbaikan pertama.
  * `Best` — Terjemahan yang sudah disaring dan siap pakai.
  * `Polished` — Hasil akhir penyuntingan naskah yang mengalir alami (*lokalisasi final*).
* **Prioritas Ekspor Otomatis**: Saat menyimpan (*Save*), aplikasi secara cerdas mengekspor lapisan terjemahan tertinggi yang tersedia (`Polished` > `Best` > `Better` > `Initial` > `Machine`) ke file JSON game.
* **Split View**: Bandingkan dua tab terjemahan secara berdampingan (misal `Initial` vs `Polished`).
* **Auto-Heal & Auto-Sync**: Jika teks naskah Jepang asli sebelumnya kosong akibat salah folder, aplikasi akan memulihkan dan mengisi ulang teks Jepang secara otomatis begitu folder raw diarahkan dengan benar.

### 📖 3. Furigana Parser & Pencarian Romaji Cerdas
* **Pembacaan Kanji Otomatis**: Dilengkapi modul MeCab / UniDic untuk menampilkan furigana di atas kanji secara instan.
* **Pencarian Berbasis Romaji**: Mengetik `arisu` akan otomatis menemukan kanji `有里栖`, `ありす`, maupun katakana `アリス`.
* **Pencarian Regex & In-File Search**: Filter naskah dengan regular expression dan lompat langsung ke baris target dengan cepat.

### 🤖 4. Integrasi LLM & WebAI-to-API Manager
* **Kompatibel dengan OpenAI API & Gemini**: Terhubung ke endpoint standar `/v1/chat/completions` (seperti Ollama, LM Studio, vLLM, maupun WebAI-to-API).
* **Manajer Alat WebAI-to-API**:
  * Terintegrasi langsung dengan server lokal `WebAI-to-API` (port `6969`) untuk memanfaatkan akun Gemini browser secara gratis.
  * **Auto-Update Rilis GitHub**: Dilengkapi tombol *Check Update* dan *Update Now* 1-klik untuk memperbarui versi WebAI-to-API langsung dari repositori GitHub resmi.
* **Batch Translation & Polishing**: Terjemahkan atau poles seluruh skenario dalam satu klik dengan pemantauan progress real-time (*Server-Sent Events*).
* **Glosarium Otomatis**: Aturan penerjemahan nama karakter, gender, dan panggilan (misal: `Sora-nee`, `Icchan`) disuntikkan secara otomatis ke prompt AI.

---

## 🖥️ Struktur Antarmuka

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🌐 VN Translation Tool [🎮 D.C.4 Plus Harmony]         🤖 LLM  📚 Bulk  ⚙️ Settings│
├───────────────────┬─────────────────────────────────────────────────────────┤
│ 🔍 Cari skenario..│ Skenario: dc4_nin20190511b.json           [💾 Save] [📋 Copy]   │
├───────────────────┼────────────────────────────┬────────────────────────────┤
│ 📁 PROLOG         │ #1 「諳子」ご飯はちゃんと..│ #1 「Sorane」Makanannya..  │
│  ├─ page 1 baris 1│ #2 「諳子」食べ過ぎには..  │ #2 「Sorane」Jangan makan..│
│  └─ page 1 baris 2│ #3 一登                     │ #3 Ichito                  │
│ 📁 ROUTE NINO     │ #4 「了解ー……っと」        │ #4 「Okeee... siap」       │
└───────────────────┴────────────────────────────┴────────────────────────────┘
```

---

## 📦 Persyaratan Sistem

* **Sistem Operasi**: Windows 10 / 11, macOS, atau Linux
* **Python**: Versi `3.10` atau lebih baru
* **Browser**: Microsoft Edge, Google Chrome, Mozilla Firefox, atau browser berbasis Chromium lainnya

---

## 🚀 Instalasi & Menjalankan

### 1. Clone Repositori
```bash
git clone https://github.com/SakuraSymphonyReTranslation/VN-Translation-Tool.git
cd VN-Translation-Tool
```

### 2. Pasang Dependensi Python
```bash
pip install -r requirements.txt
```

### 3. Jalankan Aplikasi Utama
```bash
python app.py
```
Buka browser dan akses alamat:
👉 **`http://127.0.0.1:8000`**

---

## 📖 Panduan Penggunaan (Step-by-Step)

### 1. Konfigurasi Proyek & Folder Game
1. Tekan tombol **`Ctrl + ,`** atau klik ikon gerigi **Settings (⚙️)** di pojok kanan atas.
2. Di bagian **Project Profile & Identifier**:
   * Pilih profil yang sudah ada (misal `D.C.4 Plus Harmony`) atau klik **`+ New Project`** untuk membuat proyek game baru.
   * Masukkan **Project Identifier** (contoh: `dc3_platinum_partner`).
3. Di bagian **Directories**, tentukan jalur folder game Anda:
   * **Original JSON Directory**: Folder berisi file JSON naskah Jepang asli (raw).
   * **Translated JSON Directory**: Folder tujuan penyimpanan JSON terjemahan game.
   * **Excel Structure File (Opsional)**: File `.xlsx` pengelompokan bab skenario (jika tidak ada, aplikasi otomatis mengelompokkan file dari folder game).
   * **Project Data Directory**: Folder cache pengerjaan (pilih dari dropdown atau ketik nama folder).
4. Klik **Save Changes**.

---

### 2. Navigasi & Penerjemahan Naskah
1. Pilih skenario dari panel sidebar sebelah kiri.
2. Naskah akan dimuat berdampingan:
   * **Kolom Kiri**: Teks Jepang asli (dengan furigana jika diaktifkan).
   * **Kolom Kanan**: Kolom input terjemahan sesuai tab aktif (`Initial`, `Machine`, `Better`, `Best`, `Polished`).
3. Anda bisa mengedit teks secara langsung pada baris mana pun.
4. Tekan tombol **`Ctrl + S`** atau klik tombol **Save** untuk menyimpan perubahan.

---

### 3. Menerjemahkan dengan AI / LLM
Aplikasi mendukung integrasi AI lokal via `WebAI-to-API`:

1. **Jalankan Server AI**:
   * Double-click file [`start_webai.bat`](start_webai.bat) yang berada di root folder aplikasi.
   * Server `WebAI-to-API` akan aktif di port `6969`.
2. **Uji Koneksi**:
   * Masuk ke **Settings (⚙️) → LLM Configuration**.
   * Pastikan URL diset ke `http://localhost:6969/v1` dan nama model `gemini-3.0-flash` atau `gemini-3.7-flash`.
   * Klik **Test Connection** hingga muncul status **Connected!**.
3. **Menerjemahkan Satu Baris**:
   * Klik ikon petir/robot di samping baris yang ingin diterjemahkan atau dipoles.
4. **Menerjemahkan Massal (Batch)**:
   * Klik tombol **LLM Batch (🤖)** di bagian atas sidebar.
   * Pilih mode (*Retranslate* / *Polish*), rentang baris, dan klik **Start**.

---

### 4. Glosarium Istilah & Nama Karakter
Untuk menjaga nama karakter dan panggilan tidak diterjemahkan keliru oleh AI:
1. Buka **Settings (⚙️) → LLM Configuration → Glossary**.
2. Klik **`+ Add`** untuk menambah aturan baru, contoh:
   * Source (JP): `芳乃 さくら` $\rightarrow$ Target: `Yoshino Sakura` | Info: `Female`
   * Source (JP): `俺` $\rightarrow$ Target: `Aku` | Info: `Gunakan kata Aku/Kamu`
3. Anda juga bisa mengekspor atau mengimpor glosarium dalam format JSON.

---

### 5. Pencarian Global & Find-and-Replace
* **Global Search (`Ctrl + F`)**: Mencari kata kunci di seluruh file naskah proyek (mendukung teks asli, terjemahan, romaji, dan regex).
* **Find & Replace (`Ctrl + H`)**: Mengganti istilah secara massal di seluruh skenario dengan opsi pencocokan huruf kapital (*Preserve Case*).
* **In-File Search (`Ctrl + G`)**: Pencarian cepat khusus pada file skenario yang sedang terbuka.

---

## ⌨️ Pintasan Keyboard (Shortcuts)

| Shortcut | Aksi |
| :--- | :--- |
| **`Ctrl + S`** | Menyimpan skenario yang sedang diedit |
| **`Ctrl + F`** | Membuka jendela Pencarian Global (*Global Search*) |
| **`Ctrl + H`** | Membuka jendela Cari & Ganti Massal (*Find & Replace*) |
| **`Ctrl + G`** | Membuka pencarian cepat dalam file (*In-File Search*) |
| **`Ctrl + ,`** | Membuka jendela Pengaturan (*Settings*) |
| **`Ctrl + Shift + S`** | Membuka menu *Save Copy As* |
| **`Esc`** | Menutup modal atau jendela popup yang sedang aktif |

---

## ❓ Troubleshooting & FAQ

#### Q: Mengapa kolom naskah Jepang asli kosong / tidak muncul?
> **Jawaban**: Pastikan jalur **Original JSON Directory** pada menu Settings diarahkan tepat ke folder yang berisi file `.json` raw Jepang (bukan folder kosong). Setelah path diperbaiki, buka kembali file tersebut dan aplikasi akan mengisi ulang teks aslinya secara otomatis (*auto-heal*).

#### Q: Test Connection LLM menghasilkan pesan "Cannot connect to http://localhost:6969/v1"?
> **Jawaban**: Pastikan server `WebAI-to-API` sudah dijalankan dengan me-running file `start_webai.bat`. Biarkan terminal tersebut tetap terbuka di latar belakang.

#### Q: Browser Edge menahan cache tampilan lama?
> **Jawaban**: Tekan **`Ctrl + F5`** (atau `Ctrl + Shift + R`) pada keyboard untuk melakukan *hard refresh* dan mengunduh pembaruan antarmuka terbaru.

---

## 📄 Lisensi & Kredit

* **Lisensi**: Dirilis di bawah lisensi [MIT License](LICENSE).
* **Pengembang**: [Sakura Symphony Re; Translation](https://github.com/SakuraSymphonyReTranslation)
* **WebAI-to-API**: Berdasarkan repositori upstream oleh [Amm1rr/WebAI-to-API](https://github.com/Amm1rr/WebAI-to-API).

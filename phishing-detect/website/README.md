# Phishing URL Detector

Aplikasi web pendeteksi URL phishing menggunakan Machine Learning (Gradient Boosting) dan Flask.

## Fitur
- Deteksi real-time menggunakan 30 fitur ekstraksi URL.
- Desain modern dan responsif.
- Indikator loading dan hasil prediksi yang jelas.

## Prasyarat
- Python 3.8+
- Koneksi Internet (untuk fitur WHOIS dan requests ke URL target)

## Instalasi

1.  Pastikan Anda berada di dalam folder project:
    ```bash
    cd "d:\05_SAINS DATA\phising-detect\website"
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Cara Menjalankan

1.  Jalankan aplikasi Flask:
    ```bash
    python app.py
    ```

2.  Buka browser dan kunjungi:
    ```
    http://127.0.0.1:5000
    ```

3.  Masukkan URL yang ingin dicek (contoh: `google.com` atau URL mencurigakan) dan klik "Cek URL".

## Catatan
- Proses prediksi mungkin memakan waktu beberapa detik karena sistem melakukan pengecekan real-time (WHOIS, HTTP Status, dll) ke URL yang dituju.
- Jika model `gradient_boosting_model.pkl` tidak ditemukan atau tidak kompatibel, aplikasi akan menggunakan mode fallback (dummy).

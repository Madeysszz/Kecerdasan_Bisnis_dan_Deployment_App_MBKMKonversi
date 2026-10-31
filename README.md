# KecerdasanBisnis_TOG

Norton Intelligent Transaction Anomaly Detection untuk PT Triple One Global: audit data, fitur historis, tiga model unsupervised, mart analitik, dan dashboard BI. Analisis bersifat retrospektif pada snapshot log; prioritas investigasi tidak menyatakan fraud.

Dokumen utama adalah [Knowledge Hasil dan Pembahasan A–Z](kecerdasan-bisnis/docs/KNOWLEDGE_HASIL_DAN_PEMBAHASAN.md). Dokumen tersebut menjelaskan metodologi, hasil aktual, kesimpulan bisnis, keterbatasan, serta rujukan 12 gambar EDA dan validasi.

## Isi repositori

- Kode pipeline, dashboard, konfigurasi eksperimen, dependensi, dan pengujian.
- Notebook EDA dengan hasil agregat, knowledge, kamus fitur, arsitektur, serta ringkasan konversi mata kuliah.
- Tabel hasil agregat, laporan yang tidak menampilkan kasus individual, metadata evaluasi, manifest sumber, dan gambar bukti.

Dataset mentah, seluruh `data/processed/`, database, skor/kasus per log, model biner, environment, cache, kredensial, dan alat publikasi lokal tidak disertakan. Hasil agregat dan knowledge dapat dibaca tanpa dataset. Pipeline lengkap serta dashboard memerlukan data lokal yang berizin; clone saja tidak menyertakan data untuk investigasi per log.

## Menjalankan ulang dengan data berizin

Sediakan Python 3.12 pada PATH. Letakkan ketiga CSV lokal pada folder `dataset/` di root repositori dengan nama yang sesuai [konfigurasi audit](kecerdasan-bisnis/configs/audit.json). Folder tersebut diabaikan Git. Jalankan dari Git Bash:

```bash
cd kecerdasan-bisnis
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python run_pipeline.py
python build_knowledge_evidence.py
python -m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

Buka alamat yang muncul di terminal. Tekan `Ctrl+C` pada terminal yang menjalankan server untuk menghentikannya; `deactivate` digunakan untuk keluar dari environment.

Pipeline membangkitkan kembali artefak privat lokal. Hash pada [manifest sumber](kecerdasan-bisnis/outputs/reports/source_manifest.json) dapat dipakai untuk memastikan snapshot sama dengan laporan. Informasi instalasi notebook dan perintah PowerShell tersedia pada [panduan proyek BI](kecerdasan-bisnis/README.md).

## Pengujian

```bash
cd kecerdasan-bisnis
python -m unittest discover -s tests -v
```

Pada clone tanpa data privat, 19 tes mandiri dapat dijalankan dan sembilan tes yang memerlukan data/artefak privat ditandai `skipped` dengan alasan. Setelah data berizin tersedia dan pipeline selesai, seluruh 28 tes dapat dijalankan. Hasil validasi snapshot lengkap terdokumentasi pada [verifikasi implementasi](kecerdasan-bisnis/outputs/reports/implementation_verification.md).

## Batas hasil

Dataset belum memiliki ground truth investigasi. Agreement dan stabilitas mengukur konsistensi ranking, bukan akurasi fraud. Kuota prioritas 1% berbeda dari filter skor konsensus 0,99. Relasi pricing–package, makna status/price, kelengkapan ekspor, dan availability atribut masih memerlukan konfirmasi; temporal replay serta model akun belum diterapkan.

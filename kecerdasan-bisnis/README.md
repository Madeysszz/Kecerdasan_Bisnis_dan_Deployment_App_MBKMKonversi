# Norton Intelligent Transaction Anomaly Detection

Proyek Kecerdasan Bisnis untuk PT Triple One Global. Pekerjaan dilaksanakan bertahap: audit dan EDA, fitur historis, mart terpisah, tiga model, evaluasi tanpa label, alasan statistik, serta dashboard empat halaman. Hasil merupakan analisis retrospektif snapshot; prioritas investigasi bukan label fraud atau ukuran generalisasi pada masa depan.

## Artefak utama

- [Knowledge hasil dan pembahasan A–Z](docs/KNOWLEDGE_HASIL_DAN_PEMBAHASAN.md), dengan rujukan 12 gambar dan batas interpretasi hasil.
- [Laporan audit lengkap](outputs/reports/data_audit_report.md): skema, missing values, timestamp, harga, status, pengulangan, riwayat akun, dan validasi relasi katalog.
- [Notebook EDA](notebooks/eda_analysis.ipynb): analisis agregat dan tujuh grafik, dengan keluaran eksekusi tersimpan.
- [Interpretasi audit](docs/data_audit_interpretation.md): batas interpretasi bisnis dan prioritas konfirmasi data.
- [Arsitektur dan eksperimen](docs/architecture_and_experiments.md): diagram BI, grain dimensional, contoh SQL, kamus fitur, kelayakan tiga algoritma, dan protokol evaluasi tanpa label.
- [Kamus fitur](docs/feature_dictionary.md) dan fitur per log/snapshot akun di `data/processed/`.
- [Metodologi dan hasil model](outputs/reports/model_comparison_report.md), skor dan bukti pada `outputs/tables/anomaly_scores.csv`.
- [Ringkasan konversi mata kuliah](docs/course_conversion_summary.md).
- [Verifikasi implementasi](outputs/reports/implementation_verification.md): hasil 28 pengujian, notebook, data mart, dashboard, dan batas pemeriksaan browser.
- `data/processed/norton_bi.db`: data mart terpisah dengan grain dan foreign key yang diperiksa.
- `outputs/tables/`: tabel audit, agreement, stabilitas, threshold, parameter eksperimen, dan kasus investigasi.
- `outputs/figures/`: tujuh grafik EDA, distribusi skor, agreement model, stabilitas, sensitivitas ambang, dan rekonsiliasi data.
- `outputs/models/`: baseline model dan preprocessing setiap kanal.
- `outputs/reports/`: laporan, manifest SHA-256 sumber, konfigurasi audit, dan hasil validasi.

Dataset aktual berisi 14.083 log cobrandgen, 178 log retail, dan 90 baris katalog paket. Database operasional serta dokumentasi terdahulu tidak ditemukan di workspace awal. Pengulangan transaction_id tidak ditafsirkan sebagai duplikat pembelian. Total price tidak ditafsirkan sebagai pendapatan bersih. Katalog tidak digabungkan karena relasinya belum tervalidasi.

## Menjalankan pipeline

Gunakan Python 3.12. Perintah berikut dijalankan dari folder `kecerdasan-bisnis` dengan Python yang telah tersedia pada PATH:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_pipeline.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Virtual environment lokal sudah disiapkan. Pada komputer saat ini perintah `python` belum tersedia di PATH, tetapi pipeline dapat dijalankan dari folder BI dengan `.\.venv\Scripts\python.exe`. Virtual environment bergantung pada lokasi interpreter asal; buat ulang jika proyek dipindahkan.

`run_audit.py` mencari konfigurasi berdasarkan lokasi script. Sumber dalam `configs/audit.json` relatif terhadap folder proyek BI. Opsi konfigurasi lain: `python run_audit.py --config configs/audit.json`. `display_timezone` pada konfigurasi mendokumentasikan UTC yang dipakai tahap ini; penggantian zona waktu pelaporan memerlukan perubahan agregasi dan label grafik secara konsisten.

Input tetap di folder `../dataset/`. Pipeline membaca sumber tanpa menimpanya dan tidak mengimputasi atau menghapus baris. Rerun membangun ulang seluruh mart dan mengganti keluaran model, termasuk skor lama yang tidak lagi sesuai fitur. Konfigurasi eksperimen, seed, parameter efektif, dan versi paket disimpan. Identifier asli dipakai untuk grouping dalam memori; keluaran memakai agregat atau pseudonim per snapshot. Artefak tersanitasi tetap untuk penggunaan internal karena waktu dan nilai transaksi dapat bersifat sensitif. Untuk audit saja, jalankan `.\.venv\Scripts\python.exe run_audit.py`.

Repositori GitHub hanya menyertakan kode, dokumentasi, dan bukti agregat. Dataset, folder processed, database, skor/kasus per log, serta model biner tetap lokal. Clone tanpa berkas privat dapat membaca laporan dan menjalankan tes mandiri; dashboard investigasi memerlukan hasil pipeline lokal. Sembilan tes integrasi ditandai skipped hanya ketika prasyarat privat tidak tersedia.

Untuk menghasilkan ulang empat gambar validasi tambahan dan ringkasan knowledge setelah pipeline selesai:

```powershell
.\.venv\Scripts\python.exe build_knowledge_evidence.py
```

## Dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

Buka `http://localhost:8501`. Halaman meliputi Executive Overview, Anomaly Monitoring, Model Comparison, dan Transaction Investigation. Tersedia filter kanal, waktu UTC, status, model, serta ambang skor. Tabel evaluasi memakai seluruh snapshot kanal terpilih, sesuai keterangan pada halaman. Dashboard tidak menyediakan unggahan sumber mentah atau unduhan kredensial/data rahasia.

## Membuka notebook

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-notebook.txt
```

Buka `notebooks/eda_analysis.ipynb` melalui VS Code atau Jupyter, pilih kernel dari `.venv`, lalu jalankan seluruh sel. Dependensi notebook dipisahkan dari dependensi audit. Notebook menjalankan kembali audit dan memuat tabel serta gambar yang dihasilkan.

## Validasi dan batas hasil

Audit dijalankan pada semua berkas aktual. Timestamp nonmissing berhasil diparse dengan aturan day-first, penghapusan literal `.-1f`, dan UTC eksplisit. Rekonsiliasi jumlah log pada tabel status, harga, dan tren harian sesuai sumber. Uji tambahan memeriksa parser tanggal ambigu/tidak valid, pembedaan missing dan nol, agregat terhadap sumber, serta absennya identifier dan kredensial panjang pada keluaran.

Riwayat fitur memakai `created_at < t`; timestamp sama berbagi histori yang sama. Delapan fitur inti mewakili nilai, hitungan log historis, pengulangan referensi, serta pola waktu UTC. Bukti yang tidak tersedia tetap missing dan tidak menjadi input model inti. Status, tanggal langganan, identifier, dan kredensial tidak menjadi fitur model.

Ketiga algoritma di-fit serta diberi skor per kanal pada snapshot yang sama. LOF menggunakan outlier detection dan ECOD menggunakan skor fit. Normalisasi persentil dilakukan dalam kanal; konsensus adalah rerata tiga persentil. Kuota prioritas awal adalah ceil(1% n) tinggi dan hingga ceil(5% n) sedang, sebagai kapasitas tinjauan, bukan prevalensi anomali. Alasan statistik tidak diklaim sebagai kontribusi fitur model.

Model akun tidak dipaksakan karena histori banyak akun terlalu pendek. Evaluasi temporal, label hasil investigasi, dan stress test sintetis belum tersedia. Tidak ada accuracy, precision, recall, F1, atau ROC-AUC pada anomali nyata. Tiga CANCEL tanpa tanggal pembatalan, interval nol, ketimpangan kanal, grain, arti status/harga, availability atribut, mapping pricing–package, serta kelengkapan ekspor tetap memerlukan konfirmasi sebelum penggunaan operasional.

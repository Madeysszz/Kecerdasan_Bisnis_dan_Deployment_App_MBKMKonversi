# Dokumentasi gambar — d. Pemodelan Anomaly Detection

Dokumen utama: [d_pemodelan_anomaly_detection.md](d_pemodelan_anomaly_detection.md). Semua caption menggunakan `4.X` agar nomor dapat disesuaikan dengan urutan BAB IV. Label A–G hanya penanda dalam paket dokumentasi. Setiap PNG dapat dibuka melalui tautan berikut.

## Gambar untuk penempatan di laporan

| No. | Caption | Lokasi File PNG | Source Code / Data | Penjelasan Singkat |
| --- | --- | --- | --- | --- |
| A.1 | Gambar 4.X Implementasi Pembentukan Riwayat Log dengan Prinsip Strict History | [assets/feature_history_code.png](assets/feature_history_code.png) | `src/features.py`; fungsi `_history`; baris 32–40 | Riwayat lebih awal dan jendela akun; kode asli. |
| A.2 | Gambar 4.X Implementasi Pembentukan Delapan Fitur Log Transaksi | [assets/feature_engineering_code.png](assets/feature_engineering_code.png) | `src/features.py`; fungsi `build_features`; baris 121–130 | Transformasi log1p, komponen siklik, dan pemeriksaan finite. |
| A.3 | Gambar 4.X Implementasi Pemisahan Kanal dan Penskalaan Fitur Menggunakan RobustScaler | [assets/feature_scaling_code.png](assets/feature_scaling_code.png) | `src/modeling.py`; fungsi `run_models`; baris 174–184 | Fitur aktif dan scaler per kanal. |
| B | Gambar 4.X Ringkasan Median dan Persentil ke-95 Delapan Fitur Sebelum Penskalaan | [assets/feature_summary.png](assets/feature_summary.png) | `data/processed/transaction_features.csv`; daftar fitur pada `feature_metadata.json` | Visualisasi dokumentasi tambahan; agregat fitur valid, tanpa fit ulang. |
| C.1 | Gambar 4.X Implementasi Pelatihan dan Perhitungan Skor Isolation Forest | [assets/model_isolation_forest_code.png](assets/model_isolation_forest_code.png) | `src/modeling.py`; fungsi `run_models`; baris 205–213 | Inisialisasi, fit, pembalikan tanda skor, dan pencatatan parameter. |
| C.2 | Gambar 4.X Implementasi Pelatihan dan Pengambilan Skor ECOD | [assets/model_ecod_code.png](assets/model_ecod_code.png) | `src/modeling.py`; fungsi `run_models`; baris 214–218 | Fit pada snapshot dan pengambilan decision_scores_. |
| C.3 | Gambar 4.X Implementasi Pelatihan dan Perhitungan Skor Local Outlier Factor | [assets/model_lof_code.png](assets/model_lof_code.png) | `src/modeling.py`; fungsi `run_models`; baris 223–226; `src/modeling.py`; fungsi `run_models`; baris 237–240 | Dua panel terpisah; baris pemeriksaan warning227–236 tetap ada di sumber. |
| D | Gambar 4.X Distribusi Skor Anomali Isolation Forest, ECOD, dan LOF pada Masing-Masing Kanal | [assets/model_score_distributions_a4.png](assets/model_score_distributions_a4.png) | `08_model_score_distributions.png`; skor baseline pada `outputs/tables/anomaly_scores.csv`; `src/reporting.py::write_results`,82–88 | Rendering A4:35bin per model/kanal, rentang penuh, tidak mengubah skor. |
| E | Gambar 4.X Perbandingan Kesesuaian Peringkat Model Berdasarkan Spearman dan Jaccard Top-25 | [assets/model_agreement_a4.png](assets/model_agreement_a4.png) | `09_model_agreement.png`; `outputs/tables/model_agreement.csv`, K25; `build_knowledge_evidence.py::agreement_figure`,27–44 | Rendering A4 dari matriks yang sama; agreement bukan accuracy. |
| F | Gambar 4.X Perbandingan Stabilitas Peringkat Isolation Forest dan Local Outlier Factor | [assets/model_stability_a4.png](assets/model_stability_a4.png) | `10_model_stability.png`; `outputs/tables/model_stability.csv`; `stability_figure`,47–61 | Rendering A4; mean dan rentang varian unik; subsampel IF terpisah. |
| G | Gambar 4.X Analisis Sensitivitas Kapasitas Investigasi dan Ambang Skor Konsensus | [assets/threshold_sensitivity_a4.png](assets/threshold_sensitivity_a4.png) | `11_threshold_sensitivity.png`; `outputs/tables/threshold_sensitivity.csv`, consensus; `threshold_figure`,64–78 | Rendering A4; kuota mekanis dan skor batas, bukan prevalensi fraud. |

## Salinan grafik asli

Keempat salinan ini identik dengan keluaran sebelumnya. Versi `_a4` pada tabel utama memperbesar font atau mengubah tata letak menggunakan nilai artefak yang sama. Histogram menggunakan 35 bin pada rentang penuh. Grafik agreement dan sensitivitas menggunakan baris agregat yang sama; grafik stabilitas menggunakan varian unik. Tidak ada training, perubahan skor, pemotongan ekor distribusi, atau manipulasi gambar asli.

| Nama sumber di outputs/figures | Lokasi salinan PNG | Status |
| --- | --- | --- |
| 08_model_score_distributions.png | [assets/model_score_distributions.png](assets/model_score_distributions.png) | Salinan byte-identik dari keluaran eksperimen asli. |
| 09_model_agreement.png | [assets/model_agreement.png](assets/model_agreement.png) | Salinan byte-identik dari keluaran eksperimen asli. |
| 10_model_stability.png | [assets/model_stability.png](assets/model_stability.png) | Salinan byte-identik dari keluaran eksperimen asli. |
| 11_threshold_sensitivity.png | [assets/threshold_sensitivity.png](assets/threshold_sensitivity.png) | Salinan byte-identik dari keluaran eksperimen asli. |

## Ukuran aset PNG

| Lokasi | Ukuran piksel | Jenis |
| --- | --- | --- |
| [assets/feature_engineering_code.png](assets/feature_engineering_code.png) | 1802 × 434 | Kode asli |
| [assets/feature_history_code.png](assets/feature_history_code.png) | 1800 × 406 | Kode asli |
| [assets/feature_scaling_code.png](assets/feature_scaling_code.png) | 1800 × 462 | Kode asli |
| [assets/feature_summary.png](assets/feature_summary.png) | 2352 × 1392 | Grafik agregat |
| [assets/model_agreement.png](assets/model_agreement.png) | 1636 × 1418 | Grafik agregat |
| [assets/model_agreement_a4.png](assets/model_agreement_a4.png) | 2352 × 2016 | Grafik agregat |
| [assets/model_ecod_code.png](assets/model_ecod_code.png) | 1800 × 294 | Kode asli |
| [assets/model_isolation_forest_code.png](assets/model_isolation_forest_code.png) | 1952 × 406 | Kode asli |
| [assets/model_lof_code.png](assets/model_lof_code.png) | 1800 × 508 | Kode asli |
| [assets/model_score_distributions.png](assets/model_score_distributions.png) | 2059 × 1103 | Grafik agregat |
| [assets/model_score_distributions_a4.png](assets/model_score_distributions_a4.png) | 2352 × 2784 | Grafik agregat |
| [assets/model_stability.png](assets/model_stability.png) | 1743 × 760 | Grafik agregat |
| [assets/model_stability_a4.png](assets/model_stability_a4.png) | 2352 × 1368 | Grafik agregat |
| [assets/threshold_sensitivity.png](assets/threshold_sensitivity.png) | 1742 × 1261 | Grafik agregat |
| [assets/threshold_sensitivity_a4.png](assets/threshold_sensitivity_a4.png) | 2352 × 2064 | Grafik agregat |

## Urutan dan pengaturan di Word

1. A.1: prinsip strict history.
2. A.2: transformasi delapan fitur.
3. A.3: pemisahan kanal dan RobustScaler.
4. B: ringkasan fitur aktual.
5. C.1, C.2, C.3: kode IF, ECOD, dan LOF secara berurutan.
6. D: distribusi skor anomali.
7. E: Spearman dan Jaccard Top-25.
8. F: stabilitas parameter/seed dan subsampel IF.
9. G: konsensus serta kuota investigasi.

Gunakan satu gambar per baris dan pertahankan rasio aspek. Grafik versi A4 disiapkan untuk lebar sekitar 15–16 cm pada halaman portrait. Gambar kode dengan baris panjang sebaiknya ditempatkan pada halaman A4 landscape dengan lebar sekitar 24 cm agar kode dan indentasi aslinya tetap terbaca. Jangan memasang dua gambar kode berdampingan atau memaksa gambar yang lebar menjadi kecil. Letakkan caption di bawah gambar dan paragraf pembahasan setelahnya. Nomor `4.X` adalah placeholder penomoran yang diminta, bukan placeholder isi.

Gambar kode menggunakan font Consolas, syntax highlighting, latar putih, dan nomor baris asli. Cuplikan ECOD sengaja singkat karena inisialisasi hingga pengambilan skor hanya memerlukan lima baris sumber. Gambar LOF mempunyai dua panel dengan rentang 223–226 dan 237–240; bagian 227–236 tidak dihapus dari source code dan tidak ditampilkan sebagai sambungan kode.

## Hasil verifikasi dokumentasi

- Seluruh cuplikan Python pada Markdown dibandingkan karakter demi karakter dengan rentang source code, termasuk indentasi. Rentang juga diperiksa berada di dalam fungsi yang disebutkan.
- Sumber gambar kode disimpan dalam metadata PNG agar teksnya dapat diverifikasi kembali.
- Semua tabel hasil diturunkan dari artefak aktual dan dicocokkan dengan metadata evaluasi; jumlah prioritas tinggi terkonfirmasi 143 log.
- Semua PNG dapat dibuka, mempunyai sisi panjang minimal 1.600 piksel, dan diperiksa secara visual sebelum penyerahan.
- Salinan empat grafik asli mempunyai SHA-256 yang sama dengan sumbernya.
- Fingerprint sebelum/sesudah memastikan source code, konfigurasi, CSV sumber, database, fitur, skor, model, dan hasil eksperimen tidak berubah selama pembuatan dokumentasi.
- Dokumen hanya menampilkan kode dan agregat. Tidak ada ekspor data per log, identifier asli, kredensial, atau isi database.
- Laporan tidak memakai accuracy, precision, recall, F1, atau ROC-AUC sebagai hasil eksperimen; agreement dan stabilitas ditafsirkan sebagai konsistensi.

## Sumber yang tidak tersedia sebagai hasil implementasi

Tidak ada sumber wajib yang hilang: source code, artefak fitur/skor, dan keempat grafik hasil tersedia di workspace ini. Namun, ground-truth anomaly labels, evaluasi metrik berlabel, temporal holdout, ECOD frozen-reference untuk penilaian masa depan, LOF novelty scoring, stress test sintetis, dan model akun belum tersedia sebagai hasil proyek. Bagian tersebut dicatat sebagai keterbatasan, bukan dibuat sebagai bukti baru. Screenshot editor asli tidak diperlukan karena PNG kode secara terbuka merupakan rendering dari source code.

## Fingerprint sumber utama

Hash berikut mengidentifikasi berkas yang dirujuk saat dokumentasi dibuat; hash tidak memuat data per log. Daftar fitur dan skor per log tetap berada dalam artefak lokal dan tidak disalin ke paket dokumentasi.

| Berkas relatif terhadap kecerdasan-bisnis | SHA-256 |
| --- | --- |
| src/features.py | c164f85131d6eb0e24a62602fa533918b5fd6b7936ce63018e78bc20a8e23e82 |
| src/modeling.py | a470ed86c4b0f687b25de9b16f2407a3fe708fd6e9f2be50a8302e05159e0f99 |
| src/reporting.py | 5cfc44ba4a7204ac953dc646b4b008dd7451deb5d6ae11623e952872c3eb64ad |
| configs/experiments.json | a1b53eb3ea43e0e42a696f89d27e00ab13a1d21b475c654c541024caeae7141b |
| outputs/reports/model_evaluation.json | ab8854db6f46a8f6b9b8c07f614bc29be1aa00896bbf1c3fe92e11aecc4851fb |
| outputs/tables/anomaly_scores.csv | 9f6c301fcb83c6e0e41b377d1a31a8b097bd1e2434c3ea33387e6c5b0a7b2c0a |
| outputs/tables/model_agreement.csv | 8fbb843a4c89beb104f92a81d3e3ae7714a06496623cb9f38e8bb7188abf5778 |
| outputs/tables/model_stability.csv | 4970ed0b849098f207bcc7db91cbbe7131dedc90a15a69b9894409aafa65dd43 |
| outputs/tables/threshold_sensitivity.csv | d16852994b4f47fef62f0311b853155c9fab9ff01db1d972eada4a7876eef50a |
| data/processed/transaction_features.csv | b60ed46fccfbb9fcf6404b82072dbddb7eb136d378b845ed1a98873bedde0bad |
| run_pipeline.py | 19890a48334a22146626c483b345164edc26f98df556001459194056f46a0dc7 |
| build_knowledge_evidence.py | 58d5a4acfce3e5633a30f16984171a765732e162931b328b7150aaa666758bae |

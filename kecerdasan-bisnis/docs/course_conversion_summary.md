# Ringkasan Konversi Proyek ke Kecerdasan Bisnis

## 1. Tujuan dan kontribusi

Proyek Norton diarahkan menjadi sistem Kecerdasan Bisnis untuk menata data operasional yang tersedia, menilai kualitasnya, membentuk mart analitik, dan menyediakan bukti bagi peninjauan transaksi. Kontribusi utamanya adalah hubungan yang dapat ditelusuri antara sumber, definisi indikator, fitur, skor, dan tampilan investigasi. Model anomali menjadi salah satu komponen analitik dalam alur tersebut.

Database operasional enam tabel dan dokumentasi rancangan terdahulu tidak tersedia pada workspace awal. Implementasi menggunakan dua CSV log serta satu CSV katalog package sebagai sumber nyata. Proyek tidak merekayasa isi database yang tidak tersedia dan tidak mengubah database operasional. Katalog tidak digabungkan ke log karena kunci relasinya belum tervalidasi.

## 2. Pemetaan kontribusi terhadap materi Kecerdasan Bisnis

| Komponen | Realisasi proyek | Nilai akademik dan bisnis |
| --- | --- | --- |
| Pemahaman sumber | Audit skema, missing, harga, status, waktu, pengulangan, dan relasi katalog. | Mencegah indikator bisnis dibangun dari asumsi grain atau relasi yang salah. |
| ETL analitik | Pembacaan sumber tanpa penimpaan, parsing timestamp terdokumentasi, sanitasi, dan fitur terstruktur. | Menyediakan data analitik yang dapat direproduksi dan ditelusuri ke sumber. |
| Data warehouse/data mart | SQLite terpisah dengan dimensi, fact log, snapshot akun, dan fact skor model. | Mendukung agregasi dan perbandingan pada grain yang jelas melalui SQL serta foreign key. |
| Analitik deskriptif | Distribusi nilai, status, waktu, pengulangan, dan cakupan riwayat akun. | Mengungkap kondisi operasional snapshot dan agenda perbaikan kualitas data. |
| Analitik anomali | Isolation Forest, ECOD, dan LOF secara terpisah per kanal. | Menyediakan beberapa sudut pandang ranking untuk antrean peninjauan. |
| Evaluasi | Agreement, stabilitas, sensitivitas ambang, distribusi skor, dan bukti kasus. | Menilai konsistensi hasil tanpa mengarang label atau ketepatan fraud. |
| Penyajian informasi | Dashboard empat halaman dengan filter dan konteks akun pseudonim. | Menghubungkan ringkasan manajerial dengan pemeriksaan log yang terperinci. |

## 3. Grain dan model data

Fact_log mempunyai satu baris per rekaman sumber dengan log_key unik serta pasangan source/source_row_number yang unik. Baris log tidak disamakan dengan transaksi pembayaran unik. Account_key dan reference_key merupakan surrogat namespace kanal berdasarkan kemunculan pertama; identifier asli dan pemetaan identitas tidak diekspor.

Dimensi aktual adalah dim_source, dim_date, dim_channel, dim_status_snapshot, dan dim_account. Dim_source menyimpan hash SHA-256 serta lokasi relatif sumber untuk membedakan versi berkas. Fact_account_snapshot mempunyai grain akun/cutoff dan merangkum seluruh sumber teramati sebelum cutoff kanal, bukan jendela rolling yang tidak tersedia.

Pemodelan menambahkan dim_model, dim_run, dan fact_anomaly_scores. Skor individual disimpan pada grain log_key/run_key; raw_score, percentile, dan anomaly_rank tidak dijumlahkan sebagai volume transaksi. Konsensus serta prioritas antrean hanya berada pada CSV hasil dan bukan kolom tambahan pada fact skor.

Mart dibangun ulang oleh pipeline dan skor lama diinvalidasi sebelum regenerasi. Hash versi sumber penting karena surrogat dalam snapshot tidak dirancang sebagai identitas stabil lintas snapshot. Contoh SQL yang sesuai implementasi tersedia pada [arsitektur dan eksperimen](architecture_and_experiments.md).

## 4. Kontrak fitur dan metode analitik

Semua fitur historis log memakai waktu strictly earlier: created_at terdahulu harus lebih kecil daripada t. Jendela historis mencakup batas awal dan mengecualikan t. Timestamp yang sama berbagi riwayat yang sama; posisi CSV tidak menciptakan histori tambahan di dalam waktu serentak.

Delapan fitur inti mencakup log1p amount, jumlah log akun 24 jam dan tujuh hari sebelumnya, pengulangan referensi terdahulu, serta komponen siklik waktu/hari UTC. Versi fitur 2_time_of_day_seconds mempertahankan menit dan detik yang tersedia tanpa jitter atau penambahan presisi buatan. Missing tidak diimputasi. Interval, median kanal strict-prior, dan kelengkapan jendela disimpan sebagai bukti pendamping.

Model di-fit dan diberi skor pada snapshot kanal yang sama. RobustScaler, pengeluaran fitur konstan, dan referensi persentil mengikuti snapshot fit tersebut. Oleh karena itu, eksperimen disebut retrospective_in_sample; strict history fitur tidak mengubahnya menjadi validasi masa depan. Rincian formula dan kebijakan missing tersedia pada [kamus fitur](feature_dictionary.md).

Isolation Forest memakai kebalikan score_samples, ECOD memakai decision_scores_ hasil fit, dan LOF memakai novelty=False dengan kebalikan negative_outlier_factor_. Skor yang lebih besar berarti lebih anomali menurut model. Skor mentah tidak dibandingkan langsung lintas model atau kanal; konsensus merupakan rerata persentil dalam kanal.

## 5. Evaluasi yang dapat dipertanggungjawabkan

Implementasi menyediakan Top-K overlap, Jaccard, Spearman, variasi parameter/seed yang relevan, sensitivitas subsampel Isolation Forest pada referensi log yang sama, serta sensitivitas kapasitas threshold. Tie peringkat ditangani secara deterministik untuk Top-K dan memakai average ranks untuk persentil/korelasi. Hasil numerik aktual harus merujuk laporan keluaran, bukan disimpulkan dari keberadaan implementasi.

Agreement tinggi hanya menunjukkan konsistensi antarmodel. Stabilitas tinggi tidak memastikan bahwa log berperingkat atas adalah fraud. Antrean prioritas tinggi/sedang/rendah merupakan asumsi kapasitas tinjauan yang terdokumentasi, bukan prevalensi anomali nyata. Alasan kasus bersifat statistik deskriptif, bukan kontribusi fitur model yang telah didekomposisi.

Tidak tersedia ground truth hasil investigasi atau bukti pembayaran. Karena itu accuracy, precision, recall, F1, ROC-AUC, kerugian fraud, pendapatan bersih, dan churn final tidak menjadi klaim hasil. Tidak ada klaim model terbaik sebelum membaca hasil aktual dan batas interpretasinya.

## 6. Dashboard dan penggunaan keputusan

Dashboard Streamlit telah diimplementasikan dengan empat halaman berikut.

| Halaman | Keputusan yang didukung |
| --- | --- |
| Executive Overview | Menilai komposisi log, nilai tercatat, status snapshot, kanal, dan periode observasi. |
| Anomaly Monitoring | Menyeleksi log menurut skor serta threshold dan memeriksa distribusinya. |
| Model Comparison | Membaca agreement, stabilitas, parameter, dan sensitivitas threshold pada snapshot kanal. |
| Transaction Investigation | Meninjau alasan statistik, bukti, serta konteks akun pseudonim untuk tindak lanjut. |

Persentil tidak dikalibrasi ulang ketika filter dashboard berubah. Tabel evaluasi memakai snapshot kanal, sedangkan konteks akun memakai seluruh periode akun. Pemisahan cakupan tersebut ditampilkan agar pengguna tidak menyamakan filter visual dengan eksperimen baru.

## 7. Batas hasil dan pekerjaan lanjutan

Snapshot akun telah tersedia untuk deskripsi, tetapi model akun belum diterapkan. Riwayat banyak akun singkat, beberapa akun retail sangat dominan, dan label tervalidasi belum tersedia. Simpangan baku singleton serta median interval yang tidak memenuhi syarat tetap missing.

Temporal replay, evaluasi pada periode masa depan, referensi ECDF ECOD yang dibekukan, LOF novelty, dan stress test sintetis belum dilakukan. Fase lanjutan membutuhkan konfirmasi availability harga, makna timestamp/status, mapping pricing-package, serta pencatatan keputusan analis. Hasil yang sekarang tersedia ditujukan untuk investigasi retrospektif dan kualitas data, bukan klaim detektor fraud produksi.

## 8. Reproduksi dan bukti keluaran

Perintah berikut dijalankan dari folder kecerdasan-bisnis dengan Python yang sesuai tersedia. Pada workspace ini virtual environment lokal telah disiapkan; dua perintah awal diperlukan ketika membuat lingkungan baru.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_pipeline.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

Pipeline menghasilkan ulang artefak analitik dan skor; sumber pada ../dataset tidak ditimpa. Konfigurasi sumber dan parser berada pada configs/audit.json, sedangkan konfigurasi eksperimen berada pada configs/experiments.json. Notebook EDA merupakan pendamping analisis, bukan satu-satunya jalur reproduksi.

Rujukan hasil aktual adalah [laporan audit](../outputs/reports/data_audit_report.md), [validasi audit](../outputs/reports/audit_validation.json), [laporan model](../outputs/reports/model_comparison_report.md), [metadata evaluasi](../outputs/reports/model_evaluation.json), serta [validasi pipeline](../outputs/reports/pipeline_validation.json). Berkas model/evaluasi/validasi pipeline menjadi bukti hanya setelah eksekusi berhasil; angka yang belum dihasilkan tidak digantikan oleh asumsi.

Dokumen ini menjelaskan kontribusi implementasi. Pipeline aktual menghasilkan skor untuk 14.261 log dan 9.326 snapshot akun. Sebanyak 28 pengujian lulus; tujuh sel kode notebook selesai tanpa error. Status pemeriksaan dashboard, batas inspeksi browser, serta ringkasan angka eksperimen tersedia pada [verifikasi implementasi](../outputs/reports/implementation_verification.md).

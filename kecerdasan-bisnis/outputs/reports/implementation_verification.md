# Verifikasi Implementasi Norton

Pipeline telah dijalankan bertahap pada sumber aktual: audit/EDA, fitur dan mart, lalu pemodelan, evaluasi, serta penjelasan. Versi hasil akhir memakai `feature_version=2_time_of_day_seconds`.

| Pemeriksaan | Hasil aktual |
| --- | --- |
| Jumlah sumber | Dua CSV log dan satu CSV katalog; seluruh hash tetap sama sesudah pemodelan. |
| Log yang diberi skor | 14.261, masing-masing satu baris hasil dengan tiga skor model. |
| Snapshot akun | 9.326, pada cutoff masing-masing sumber. |
| Matriks fitur inti | Delapan fitur finite pada seluruh log; tidak ada imputasi atau penghapusan baris. |
| Unit test dan integrasi | 28 pengujian lulus melalui `python -m unittest discover -s tests -v`. |
| Notebook | Tujuh sel kode dieksekusi; nol error; keluaran tabel dan gambar tersimpan. |
| Data mart | Foreign key valid; join dimensi mempertahankan kontrol jumlah dan nilai sumber. |
| Fact skor model | 42.783 baris pada grain log/model-run; enam baseline run total, yaitu dua kanal × tiga model. |
| Metadata run | Seluruh parameters_json valid sebagai JSON SQLite. |
| Dashboard | Empat halaman, pergantian model, filter kanal/status, dan kondisi kosong lulus AppTest. |
| Server lokal | HTTP 200 pada `http://127.0.0.1:8501`. |
| Gambar analitik | Tujuh gambar EDA, distribusi skor, serta empat gambar tambahan agreement, stabilitas, threshold, dan rekonsiliasi data telah diinspeksi sebagai artefak PNG. |

Pemeriksaan visual dashboard melalui browser dihentikan oleh Computer Use karena URL aktif Windows tidak dapat dipastikan dengan cukup yakin. Tidak ada tindakan UI lanjutan setelah penghentian tersebut. Verifikasi fungsi dashboard dilakukan melalui AppTest; inspeksi visual browser belum selesai.

## Hasil perbandingan yang relevan

| Indikator | Cobrandgen | Retail |
| --- | --- | --- |
| Rata-rata Spearman stabilitas parameter/seed IF | 0,9701 | 0,9831 |
| Rata-rata Spearman stabilitas parameter LOF | 0,4052 | 0,5880 |
| Spearman IF–ECOD | 0,8309 | 0,8100 |
| Irisan Top-25 IF–ECOD | 13 dari 25 | 17 dari 25 |
| Prioritas tinggi menurut kuota konsensus | 141 log | 2 log |

Isolation Forest layak dipertahankan sebagai baseline peninjauan retrospektif karena ranking lebih konsisten pada variasi yang diuji. ECOD menyediakan pembanding dengan hubungan ranking yang relatif kuat terhadap baseline tersebut. LOF menyajikan hasil yang berbeda dan lebih sensitif terhadap parameter; kasus yang hanya diprioritaskan LOF perlu ditinjau terpisah. Cakupan variasi parameter tiap algoritma berbeda sehingga angka tersebut tidak membuktikan bahwa IF adalah model paling tepat.

Konsensus tetap disediakan sebagai antrean eksploratif yang transparan, bukan rekomendasi yang telah divalidasi memakai hasil investigasi manusia. Sebanyak 143 prioritas tinggi merupakan konsekuensi kuota awal ceil(1% jumlah log per kanal), bukan temuan 143 fraud.

## Batas validasi

Eksperimen utama bersifat retrospektif in-sample. Pengujian sintetis pada kode memverifikasi perilaku implementasi; pengujian tersebut bukan stress test deteksi anomali sintetis atau evaluasi pada anomali nyata. Temporal replay, model akun, ground truth investigasi, mapping pricing–package, dan rekonsiliasi pembayaran belum tersedia. Sumber mentah serta database operasional tidak diubah.

Rincian dapat ditelusuri pada `pipeline_validation.json`, `audit_validation.json`, `model_evaluation.json`, `model_comparison_report.md`, serta tabel agreement/stabilitas. Dependensi, parameter, dan seed tersimpan untuk reproduksi.

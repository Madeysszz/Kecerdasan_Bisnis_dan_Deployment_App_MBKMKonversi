# Audit Data Norton — Tahap 1

Unit observasi adalah satu baris log dalam satu sumber. Audit tidak membentuk label fraud, pembelian unik, pembayaran berhasil, maupun churn. Interpretasi dan keterbatasan tersedia dalam `../../docs/data_audit_interpretation.md`; rancangan tahap berikutnya tersedia dalam `../../docs/architecture_and_experiments.md`.

## Inventaris aktual

Workspace awal hanya berisi tiga CSV. Database `norton_bisnis.db`, kode proyek sebelumnya, repositori Git, `knowledge_dataset_norton.md`, dan `ringkasan_konversi_proyek_basis_data.md` tidak ditemukan. Skema maupun foreign key keenam tabel operasional belum dapat diaudit. Kanal diturunkan dari asal CSV, bukan join tabel channel. Hash input tersimpan di `source_manifest.json`.

| source | rows | columns | exact_duplicate_excess | duplicate_excess_without_row_keys |
| --- | --- | --- | --- | --- |
| retail | 178 | 23 | 0 | 0 |
| cobrandgen | 14083 | 28 | 0 | 0 |
| package | 90 | 16 | 0 | 0 |

Total log: **14,261**. Katalog: **90 baris**. Tidak ada input yang ditimpa.

## Skema dan missing values

CSV tidak memiliki tipe database; pembacaan memakai teks agar identifier tidak berubah. Tipe inferensi bukan konversi identifier menjadi fitur numerik. Token missing dinyatakan dalam konfigurasi; nol tetap bernilai nol. Kolom pertama cobrandgen tidak bernama dan dibaca sebagai `Unnamed: 0`. Tidak ada imputasi.

| source | column | storage_dtype | inferred_type | rows | missing_count | missing_pct | unique_nonmissing |
| --- | --- | --- | --- | --- | --- | --- | --- |
| retail | id | string | text | 178 | 0 | 0.0 | 178 |
| retail | created_at | string | timestamp_text | 178 | 0 | 0.0 | 164 |
| retail | updated_at | string | timestamp_text | 178 | 0 | 0.0 | 163 |
| retail | deleted_at | string | timestamp_text | 178 | 178 | 100.0 | 0 |
| retail | transaction_id | string | text | 178 | 0 | 0.0 | 51 |
| retail | pricing_id | string | text | 178 | 0 | 0.0 | 12 |
| retail | customer_id | string | text | 178 | 0 | 0.0 | 41 |
| retail | retail_transaction_log_detail_id | string | text | 178 | 0 | 0.0 | 51 |
| retail | callback_url | string | text | 178 | 10 | 5.618 | 40 |
| retail | status_activated | string | text | 178 | 0 | 0.0 | 3 |
| retail | psn | string | text | 178 | 10 | 5.618 | 41 |
| retail | redeem_code | string | text | 178 | 0 | 0.0 | 178 |
| retail | bill_number | string | text | 178 | 0 | 0.0 | 178 |
| retail | price | string | numeric_text | 178 | 0 | 0.0 | 8 |
| retail | subscription_expired_at | string | timestamp_text | 178 | 0 | 0.0 | 140 |
| retail | subscription_start_date | string | timestamp_text | 178 | 10 | 5.618 | 40 |
| retail | subscription_cancel_date | string | timestamp_text | 178 | 26 | 14.6067 | 143 |
| retail | email | string | text | 178 | 178 | 100.0 | 0 |
| retail | referral_code | string | text | 178 | 173 | 97.191 | 1 |
| retail | sec_ch | string | text | 178 | 178 | 100.0 | 0 |
| retail | user_agent | string | text | 178 | 151 | 84.8315 | 1 |
| retail | device_data | string | text | 178 | 156 | 87.6404 | 16 |
| retail | ip | string | text | 178 | 151 | 84.8315 | 2 |
| cobrandgen | Unnamed: 0 | string | text | 14083 | 0 | 0.0 | 14083 |
| cobrandgen | sort | string | numeric_text | 14083 | 0 | 0.0 | 14083 |
| cobrandgen | created_at | string | timestamp_text | 14083 | 0 | 0.0 | 12483 |
| cobrandgen | updated_at | string | timestamp_text | 14083 | 0 | 0.0 | 12224 |
| cobrandgen | deleted_at | string | timestamp_text | 14083 | 14083 | 100.0 | 0 |
| cobrandgen | camp_id | string | numeric_text | 14083 | 2 | 0.0142 | 9 |
| cobrandgen | transaction_id | string | text | 14083 | 0 | 0.0 | 9763 |
| cobrandgen | pricing_id | string | text | 14083 | 0 | 0.0 | 14 |
| cobrandgen | customer_id | string | text | 14083 | 0 | 0.0 | 9285 |
| cobrandgen | cobrandgen_transaction_log_detail_id | string | text | 14083 | 1 | 0.0071 | 9762 |
| cobrandgen | callback_url | string | text | 14083 | 7 | 0.0497 | 9286 |
| cobrandgen | status_activated | string | text | 14083 | 0 | 0.0 | 4 |
| cobrandgen | psn | string | text | 14083 | 7 | 0.0497 | 9756 |
| cobrandgen | redeem_code | string | text | 14083 | 0 | 0.0 | 14083 |
| cobrandgen | bill_number | string | text | 14083 | 0 | 0.0 | 14083 |
| cobrandgen | price | string | numeric_text | 14083 | 0 | 0.0 | 11 |
| cobrandgen | package_name | string | text | 14083 | 14083 | 100.0 | 0 |
| cobrandgen | skup | string | text | 14083 | 14083 | 100.0 | 0 |
| cobrandgen | pricing | string | text | 14083 | 14083 | 100.0 | 0 |
| cobrandgen | subscription_expired_at | string | timestamp_text | 14083 | 0 | 0.0 | 12591 |
| cobrandgen | subscription_start_date | string | timestamp_text | 14083 | 0 | 0.0 | 8801 |
| cobrandgen | subscription_cancel_date | string | timestamp_text | 14083 | 9280 | 65.8951 | 4075 |
| cobrandgen | puid | string | numeric_text | 14083 | 6 | 0.0426 | 1 |
| cobrandgen | pin | string | text | 14083 | 8 | 0.0568 | 9285 |
| cobrandgen | sec_ch | string | text | 14083 | 14083 | 100.0 | 0 |
| cobrandgen | user_agent | string | text | 14083 | 12083 | 85.7985 | 1 |
| cobrandgen | device_data | string | text | 14083 | 12477 | 88.5962 | 783 |
| cobrandgen | ip | string | text | 14083 | 12083 | 85.7985 | 2 |
| package | id | string | text | 90 | 0 | 0.0 | 90 |
| package | sort | string | numeric_text | 90 | 0 | 0.0 | 4 |
| package | created_at | string | timestamp_text | 90 | 0 | 0.0 | 84 |
| package | updated_at | string | timestamp_text | 90 | 5 | 5.5556 | 85 |
| package | deleted_at | string | timestamp_text | 90 | 79 | 87.7778 | 1 |
| package | creator_id | string | text | 90 | 90 | 100.0 | 0 |
| package | modifier_id | string | text | 90 | 90 | 100.0 | 0 |
| package | name | string | text | 90 | 0 | 0.0 | 87 |
| package | duration | string | numeric_text | 90 | 0 | 0.0 | 11 |
| package | code | string | text | 90 | 0 | 0.0 | 90 |
| package | spku | string | text | 90 | 0 | 0.0 | 12 |
| package | norton_name | string | text | 90 | 3 | 3.3333 | 31 |
| package | description | string | text | 90 | 3 | 3.3333 | 65 |
| package | package_type_id | string | text | 90 | 43 | 47.7778 | 4 |
| package | duration_type | string | text | 90 | 0 | 0.0 | 1 |
| package | norton_credential_id | string | text | 90 | 12 | 13.3333 | 3 |

Nilai kredensial, atribut pribadi, customer_id, dan transaction_id tidak ditulis ke laporan/tabel keluaran. Profil hanya memuat nama kolom, jumlah missing, dan keunikan. Identifier mentah dipakai sementara untuk grouping di memori, bukan diekspor.

## Harga dan status

| channel | count | invalid_or_missing | min | p25 | median | p75 | p95 | p99 | max | mean | recorded_value_sum | zero_count | negative_count | above_upper_iqr_fence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cobrandgen | 14083 | 0 | 1000 | 11000.0 | 15000.0 | 15000.0 | 15000.0 | 109000.0 | 500000 | 14982.3901 | 210997000 | 0 | 0 | 702 |
| retail | 178 | 0 | 0 | 15000.0 | 15000.0 | 15000.0 | 50000.0 | 500000.0 | 500000 | 24123.0337 | 4293900 | 8 | 0 | 13 |

Jumlah price adalah total nilai tercatat pada log. Mata uang, pembayaran terkonfirmasi, refund, pajak, dan kebijakan pendapatan tidak tersedia; jumlah ini bukan pendapatan bersih. Batas IQR hanya deskriptif; seluruh nol dan nilai ekstrem dipertahankan.

| channel | status | log_count |
| --- | --- | --- |
| cobrandgen | ACTIVE | 9270 |
| cobrandgen | CANCEL | 4806 |
| cobrandgen | FAILED | 6 |
| cobrandgen | PENDING | 1 |
| retail | ACTIVE | 16 |
| retail | CANCEL | 152 |
| retail | PENDING | 10 |

Status merupakan nilai pada ekspor. ACTIVE belum membuktikan pembayaran berhasil, sedangkan CANCEL belum membuktikan churn.

## Timestamp dan urutan kejadian

Parser memakai day-first dan UTC eksplisit. Hanya token literal `.-1f` dibuang pada salinan dalam memori; offset +00 dinormalkan ke +0000 sebelum format eksplisit diterapkan. Presisi pecahan detik yang hilang tidak direkonstruksi. Missing dan kegagalan parse nonmissing dicatat terpisah. Baris file tidak diasumsikan kronologis. Waktu grafik tetap UTC.

| source | column | missing | artifact_replacements | parse_failures_nonmissing | min_utc | max_utc |
| --- | --- | --- | --- | --- | --- | --- |
| retail | created_at | 0 | 178 | 0 | 2025-09-18T02:21:56+00:00 | 2026-08-02T00:14:57+00:00 |
| retail | updated_at | 0 | 178 | 0 | 2025-09-18T02:55:21+00:00 | 2026-08-07T01:00:01+00:00 |
| retail | deleted_at | 178 | 0 | 0 |  |  |
| retail | subscription_expired_at | 0 | 178 | 0 | 2026-01-16T02:21:56+00:00 | 2030-09-16T04:02:49+00:00 |
| retail | subscription_start_date | 10 | 168 | 0 | 2025-09-18T02:21:57+00:00 | 2026-08-02T00:14:58+00:00 |
| retail | subscription_cancel_date | 26 | 152 | 0 | 2025-09-24T08:44:43+00:00 | 2026-08-07T01:00:01+00:00 |
| cobrandgen | created_at | 0 | 14070 | 0 | 2026-05-11T06:34:25+00:00 | 2026-08-07T06:50:58+00:00 |
| cobrandgen | updated_at | 0 | 14071 | 0 | 2026-05-11T06:34:25+00:00 | 2026-08-07T06:50:58+00:00 |
| cobrandgen | deleted_at | 14083 | 0 | 0 |  |  |
| cobrandgen | subscription_expired_at | 0 | 14071 | 0 | 2026-05-12T06:34:25+00:00 | 2028-07-23T13:31:56+00:00 |
| cobrandgen | subscription_start_date | 0 | 14067 | 0 | 2026-05-11T06:34:25+00:00 | 2026-08-07T06:50:58+00:00 |
| cobrandgen | subscription_cancel_date | 9280 | 4802 | 0 | 2026-06-05T12:49:48+00:00 | 2026-08-07T06:23:45+00:00 |
| package | created_at | 0 | 84 | 0 | 2024-09-23T17:31:47+00:00 | 2026-08-03T05:59:15+00:00 |
| package | updated_at | 5 | 85 | 0 | 2024-10-21T12:52:46+00:00 | 2026-08-03T05:59:15+00:00 |
| package | deleted_at | 79 | 0 | 0 | 2025-06-25T21:44:30+00:00 | 2025-06-25T21:44:30+00:00 |

Pemeriksaan berikut memakai pasangan timestamp yang lengkap atau grup transaction_id berulang sebagai denominator, sesuai nama pemeriksaan:

| source | check | count | eligible_rows_or_groups |
| --- | --- | --- | --- |
| retail | repeated_transaction_varies_status_activated | 5 | 6 |
| retail | repeated_transaction_varies_customer_id | 0 | 6 |
| retail | repeated_transaction_varies_price | 0 | 6 |
| retail | repeated_transaction_varies_pricing_id | 0 | 6 |
| retail | repeated_transaction_varies_subscription_start_date | 0 | 6 |
| retail | repeated_transaction_varies_subscription_expired_at | 6 | 6 |
| retail | updated_before_created | 0 | 178 |
| retail | updated_after_created | 151 | 178 |
| retail | start_before_created | 127 | 168 |
| retail | start_after_created | 41 | 168 |
| retail | expiry_before_start | 0 | 168 |
| retail | cancel_before_start | 0 | 152 |
| retail | cancel_after_expiry | 1 | 152 |
| retail | cancel_status_without_cancel_date | 0 | 152 |
| retail | noncancel_with_cancel_date | 0 | 26 |
| retail | adjacent_created_decreases_in_file_order | 44 | 177 |
| cobrandgen | repeated_transaction_varies_status_activated | 3758 | 3808 |
| cobrandgen | repeated_transaction_varies_customer_id | 0 | 3808 |
| cobrandgen | repeated_transaction_varies_price | 0 | 3808 |
| cobrandgen | repeated_transaction_varies_pricing_id | 0 | 3808 |
| cobrandgen | repeated_transaction_varies_subscription_start_date | 11 | 3808 |
| cobrandgen | repeated_transaction_varies_subscription_expired_at | 3808 | 3808 |
| cobrandgen | updated_before_created | 0 | 14083 |
| cobrandgen | updated_after_created | 584 | 14083 |
| cobrandgen | start_before_created | 4545 | 14083 |
| cobrandgen | start_after_created | 0 | 14083 |
| cobrandgen | expiry_before_start | 0 | 14083 |
| cobrandgen | cancel_before_start | 0 | 4803 |
| cobrandgen | cancel_after_expiry | 1804 | 4803 |
| cobrandgen | cancel_status_without_cancel_date | 3 | 4806 |
| cobrandgen | noncancel_with_cancel_date | 0 | 9277 |
| cobrandgen | adjacent_created_decreases_in_file_order | 4211 | 14082 |

Start sebelum created_at, cancel setelah expiry, atau expiry yang berubah pada ID berulang memerlukan validasi semantik proses. Hasil tersebut tidak otomatis menunjukkan kesalahan atau fraud. Status, updated_at, dan tanggal langganan belum dianggap tersedia saat kejadian.

## Pengulangan dan riwayat akun

| source | key | unique | repeated_groups | rows_in_repeated_groups | max_rows_per_key |
| --- | --- | --- | --- | --- | --- |
| retail | transaction_id | 51 | 6 | 133 | 64 |
| retail | customer_id | 41 | 7 | 144 | 65 |
| cobrandgen | transaction_id | 9763 | 3808 | 8128 | 9 |
| cobrandgen | customer_id | 9285 | 4103 | 8901 | 11 |

Exact duplicate memakai seluruh kolom. Pemeriksaan payload kedua mengabaikan hanya id, indeks ekspor, dan sort; tidak ada deduplikasi. Pengulangan ID tidak dianggap pembelian unik atau data rusak.

| source | accounts | single_log_accounts | accounts_at_least_3_logs | accounts_at_least_5_logs | logs_without_strictly_prior_account_timestamp | same_account_timestamp_groups | rows_in_same_account_timestamp_groups | consecutive_intervals | zero_intervals | median_gap_seconds | p95_gap_seconds | max_gap_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| retail | 41 | 34 | 4 | 3 | 42 | 13 | 26 | 137 | 13 | 69.0 | 10018.4 | 17269259.0 |
| cobrandgen | 9285 | 5182 | 443 | 37 | 9285 | 0 | 0 | 4798 | 0 | 2591880.0 | 2592527.15 | 4082575.0 |

Unit akun adalah (kanal, customer_id). Interval EDA adalah selisih timestamp berurutan setelah sort. Interval nol tidak menentukan urutan dalam satu detik. Untuk fitur historis, seluruh baris dengan waktu sama harus berbagi riwayat strictly earlier, bukan urutan arbitrer. Awal/akhir observasi merupakan batas ekspor, bukan tanggal akuisisi/churn akun.

## Validasi relasi katalog

| channel | log_column | package_column | nonmissing_log_rows | distinct_log_values | matched_rows_exact | target_unique_nonmissing | join_validated |
| --- | --- | --- | --- | --- | --- | --- | --- |
| retail | pricing_id | id | 178 | 12 | 0 | True | False |
| cobrandgen | pricing_id | id | 14083 | 14 | 0 | True | False |
| cobrandgen | package_name | name | 0 | 0 | 0 | False | False |
| cobrandgen | skup | spku | 0 | 0 | 0 | False | False |

| key | distinct_value_overlap |
| --- | --- |
| customer_id | 0 |
| transaction_id | 0 |
| pricing_id | 0 |

Tidak ada join katalog yang disahkan. pricing_id tidak dianggap package.id. Dibutuhkan mapping pricing–package yang valid beserta kardinalitas dan masa berlaku; pencocokan nama atau SKU tanpa validasi tidak digunakan.

## EDA

Tujuh gambar pada `../figures/` mencakup distribusi nilai, frekuensi harian, kanal, status, aktivitas akun, pengulangan ID, dan interval akun. Histogram memakai ln(1+x); statistik asli tersimpan pada tabel agregat. Nol log pada hari di dalam cakupan berarti tidak ada baris teramati pada ekspor, bukan bukti tidak ada aktivitas operasional. Hari di luar cakupan setiap sumber tidak diisi nol.

## Keputusan dan kelanjutan

Fungsi audit hanya melakukan analisis deskriptif dan EDA, tanpa imputasi, penghapusan outlier, deduplikasi, join katalog, pemodelan, atau penulisan database. Implementasi fase lanjutan dijalankan terpisah melalui run_pipeline.py; hasil eksperimen aktual tersedia pada model_comparison_report.md. Audit ini tidak menghasilkan label ground truth atau metrik performa berlabel.

Konfirmasi berikutnya meliputi grain log/renewal, makna price/status, kelengkapan ekspor, ketersediaan atribut saat scoring, mapping katalog, dan format timestamp. Perbedaan kanal serta sparsitas riwayat perlu menjadi dasar eksperimen, bukan dihilangkan lewat penggabungan otomatis.

## Reproduksibilitas

Jalankan `python run_audit.py` di folder BI. Konfigurasi memakai path relatif terhadap folder BI; script dapat dipanggil dari direktori lain. Manifest input, versi runtime, salinan konfigurasi, dan hasil rekonsiliasi disimpan. Hash semua CSV diperiksa kembali sesudah audit. Notebook memakai fungsi audit yang sama.

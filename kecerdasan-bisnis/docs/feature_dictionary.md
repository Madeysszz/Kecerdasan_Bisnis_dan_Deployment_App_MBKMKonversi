# Kamus Fitur dan Mart Analitik

## Cakupan dan kontrak

`src.features.build_features(config_path)` mengembalikan empat objek: log tersanitasi, fitur per log, snapshot akun, dan metadata.
`save_artifacts(logs, features, accounts, metadata, project_root)` menyimpan hasil ke `data/processed` dan mengembalikan lokasi `norton_bi.db`.
Data sumber hanya dibaca melalui `src.audit.load_sources`; normalisasi waktu memakai `src.audit.parse_timestamp`.
Katalog package tidak digabung karena relasinya belum tervalidasi.
Satuan fitur transaksi tetap satu baris log, bukan transaksi bisnis unik.

## Identitas tersanitasi dan grain

| Kolom | Definisi |
| --- | --- |
| `log_key` | Kanal dan urutan baris sumber, mulai dari satu; contohnya `retail:000001`. |
| `source`, `channel` | Nama sumber terkonfigurasi dan kanal asal; saat ini masing-masing kanal mempunyai satu CSV log. |
| `source_row_number` | Nomor posisi baris sumber sebelum pengurutan; bukan identifier asli pada CSV. |
| `account_key` | Surrogat pelanggan dengan namespace sumber dan nomor menurut kemunculan pertama. |
| `reference_key` | Surrogat transaction_id dengan namespace sumber dan nomor menurut kemunculan pertama. |
| `created_at` | Waktu hasil parsing dalam UTC; timestamp tidak valid tetap kosong. |
| `status_snapshot` | Status yang terlihat pada baris ekspor; tidak diperlakukan sebagai label fraud atau status final. |
| `amount` | Nilai price numerik sumber; bukan pendapatan terkonfirmasi. Nilai hilang/tidak numerik/tidak finite tetap kosong. |

Surrogat tidak berasal dari hash identifier, kata sandi, atau kunci rahasia.
Pemetaan identifier asli tidak ditulis ke keluaran; identifier asli hanya dipakai sementara untuk pengelompokan dalam memori.
Pengulangan build terhadap snapshot dengan urutan sama menghasilkan surrogat yang sama.
Surrogat dapat berubah ketika urutan snapshot berubah; keluaran bukan identitas lintas snapshot atau mekanisme anonimisasi formal.
Missing identifier tidak diberi akun atau referensi pengganti.
Artefak ini tetap perlu diperlakukan sebagai data internal karena waktu dan nilai transaksi dapat memiliki sifat sensitif.

## Fitur inti model per log

Seluruh riwayat memakai syarat `created_at < t` pada kanal yang sama.
Baris dengan timestamp sama memperoleh riwayat yang sama; urutan baris pada timestamp tersebut tidak menambah riwayat.
Jendela waktu memakai interval `[t - durasi, t)`, sehingga batas awal termasuk dan timestamp saat ini tidak termasuk.
Tidak ada imputasi; hanya baris dengan delapan fitur finite yang layak masuk model inti.

| Fitur | Definisi |
| --- | --- |
| `log1p_amount` | `ln(1 + amount)` untuk amount nonnegatif yang diketahui. |
| `log1p_prior_account_count_24h` | `ln(1 + jumlah log akun yang teramati dalam 24 jam sebelumnya)`. |
| `log1p_prior_account_count_7d` | `ln(1 + jumlah log akun yang teramati dalam tujuh hari sebelumnya)`. |
| `log1p_prior_reference_count` | `ln(1 + jumlah log terdahulu dengan reference_key sama)` di seluruh jendela sumber yang teramati. |
| `hour_sin`, `hour_cos` | Representasi siklik waktu UTC dengan periode 24: jam + menit/60 + detik/3600. |
| `weekday_sin`, `weekday_cos` | Representasi siklik hari UTC dengan periode tujuh; Senin bernilai nol. |

Hitungan nol berarti tidak ada kejadian terdahulu yang teramati; nilainya bukan imputasi untuk riwayat yang hilang.
Versi fitur `2_time_of_day_seconds` mempertahankan menit dan detik yang teramati; tidak menambahkan pecahan detik, jitter, atau deduplikasi untuk membedakan log.
Riwayat tidak dapat dibentuk ketika waktu atau identitas pengelompokan tidak diketahui; fitur terkait tetap kosong.
Status, tanggal pembatalan/kedaluwarsa, identifier, data pribadi, kredensial, dan atribut katalog tidak masuk fitur inti.

## Bukti pendamping yang tidak masuk model inti

| Kolom | Definisi dan penanganan missing |
| --- | --- |
| `prior_history_count` | Jumlah seluruh log akun yang teramati dengan timestamp lebih awal; nol sah pada cold start. |
| `prior_account_count_24h`, `prior_account_count_7d` | Hitungan sebelum transformasi logaritmik. |
| `prior_reference_count` | Hitungan referensi sebelum transformasi logaritmik. |
| `window_24h_complete`, `window_7d_complete` | Benar jika selisih t terhadap timestamp awal sumber mencapai durasi terkait; kosong jika waktu tidak diketahui. |
| `seconds_since_previous_log` | Detik sejak timestamp akun sebelumnya yang berbeda dan lebih awal; kosong tanpa riwayat. |
| `prior_channel_median_amount` | Median amount kanal hanya dari log dengan timestamp lebih awal; kosong tanpa nilai historis yang diketahui. |
| `amount_minus_prior_channel_median` | Amount saat ini dikurangi median historis kanal; kosong jika salah satu komponen tidak diketahui. |
| `core_features_eligible` | Benar hanya jika seluruh fitur inti finite; bukan prediksi anomali. |

Kelengkapan jendela hanya diukur terhadap batas awal snapshot sumber dan tidak menjamin tidak ada kejadian produksi yang hilang.
Riwayat teramati tidak boleh disebut riwayat lengkap sepanjang hidup akun.
Median kanal tidak memasukkan amount saat ini ataupun amount baris lain pada timestamp yang sama.

## Snapshot deskriptif akun

Satu baris snapshot mewakili satu pasangan kanal/akun pada cutoff `max(created_at sumber) + 1 detik`.
Snapshot memakai seluruh log akun dengan waktu diketahui sebelum cutoff dan tidak menjadi fitur historis log sebelumnya.

| Kolom | Definisi |
| --- | --- |
| `observed_log_count`, `observed_reference_count` | Jumlah log dan jumlah reference_key berbeda yang teramati. |
| `amount_observation_count` | Jumlah amount yang diketahui; memungkinkan pembaca menilai cakupan statistik amount. |
| `amount_mean`, `amount_std` | Rata-rata dan simpangan baku sampel amount, `ddof=1`; std kosong untuk satu observasi. |
| `unique_timestamp_count` | Jumlah timestamp akun berbeda; kejadian serentak tidak memperbanyak cakupan waktu. |
| `median_interval_seconds` | Median selisih timestamp unik yang diurutkan, hanya tersedia jika minimal tiga timestamp unik. |
| `first_created_at`, `last_created_at`, `account_observation_days` | Awal, akhir, dan rentang pengamatan akun. |
| `source_coverage_start`, `source_coverage_end`, `source_observation_days` | Batas waktu dan rentang snapshot sumber; bukan bukti kelengkapan produksi. |
| `cutoff_utc` | Batas eksklusif pembentukan snapshot. |

Snapshot akun bersifat deskriptif; kecukupan data untuk model akun belum terpenuhi secara metodologis.
Riwayat banyak akun pendek, durasi observasi berbeda, semantik log belum seluruhnya terkonfirmasi, dan label fraud tervalidasi belum tersedia.
Median interval dan simpangan baku yang tidak tersedia tetap kosong dan tidak diganti nol.

## Penyimpanan dan relasi

CSV yang dihasilkan adalah `sanitized_logs.csv`, `transaction_features.csv`, dan `account_features.csv`.
`feature_metadata.json` mencatat daftar fitur inti, kelayakan baris, cold start, cutoff, kebijakan riwayat, dan pengecualian.
SQLite terpisah disimpan pada `data/processed/norton_bi.db` dengan tabel berikut.

| Tabel | Grain dan relasi |
| --- | --- |
| `dim_channel` | Satu baris per kanal. |
| `dim_source` | Satu baris per sumber, terkait kanal, jumlah baris, batas waktu observasi, `source_sha256`, dan `relative_path` dari manifest. |
| `dim_date` | Satu baris per tanggal UTC yang mempunyai log; memuat tahun, bulan, hari, dan indeks hari pekan. |
| `dim_status_snapshot` | Satu baris per status snapshot yang diketahui. |
| `dim_account` | Satu baris per surrogat akun dengan kanal dan batas observasi. |
| `fact_log` | Satu baris per log_key; pasangan source/source_row_number juga unik; memuat bukti pendamping dan fitur inti. |
| `fact_account_snapshot` | Satu baris per account_key/cutoff_utc; tidak boleh digabung ke log sebagai fitur masa lalu. |

Foreign key menghubungkan fakta dengan dimensi yang sesuai dan diperiksa saat penyimpanan.
Tidak ada foreign key buatan ke package, pemetaan identifier asli, data pribadi, atau kredensial dalam mart.
Pemanggilan ulang `save_artifacts` membangun kembali seluruh mart fitur dan menghapus tabel skor serta metadata model/run lama.
Pipeline utama harus menghasilkan ulang skor sesudah rebuild; skor lama tidak dipertahankan ketika versi snapshot atau surrogat berubah.
Hash sumber dan lokasi relatif pada `dim_source` menelusurkan fakta ke versi berkas sumber dalam manifest.

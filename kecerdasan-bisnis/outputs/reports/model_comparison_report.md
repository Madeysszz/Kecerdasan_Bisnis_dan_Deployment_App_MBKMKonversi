# Metodologi dan Hasil Pemodelan Norton

Eksperimen ini merupakan analisis retrospektif in-sample atas snapshot log, bukan pengukuran generalisasi atau deteksi fraud. Ketiga model di-fit dan diberi skor pada set observasi yang sama untuk membandingkan ranking tanpa ground truth. Data tidak diimputasi, dideduplikasi, atau dibersihkan dengan menghapus nilai ekstrem. Basis data operasional tidak ditulis.

## Populasi, fitur, dan preprocessing

| channel | log_count | accounts | recorded_value |
| --- | --- | --- | --- |
| cobrandgen | 14083 | 9285 | 210997000.0 |
| retail | 178 | 41 | 4293900.0 |

Unit analisis adalah log per kanal. Akun dan referensi transaksi memakai pseudonim yang deterministik dalam snapshot sumber yang sama. Price tetap disebut nilai tercatat. Fitur historis menghitung waktu strictly earlier; baris dengan timestamp sama tidak saling memasukkan histori. Interval dan median harga historis yang belum tersedia tetap missing sebagai bukti konteks, dan tidak menjadi input model inti.

Fitur inti: `log1p_amount`, `log1p_prior_account_count_24h`, `log1p_prior_account_count_7d`, `log1p_prior_reference_count`, `hour_sin`, `hour_cos`, `weekday_sin`, `weekday_cos`. Rincian rumus, coverage, dan unit snapshot akun tersedia pada `../../docs/feature_dictionary.md`. Fitur status/update/tanggal langganan, identifier, dan atribut pribadi tidak menjadi input model.

Transformasi log1p diterapkan pada nilai/jumlah nonnegatif. RobustScaler di-fit per kanal dan fitur konstan dikeluarkan sesuai metadata run. Karena evaluasi utama retrospektif, referensi model/preprocessing mencakup snapshot fit tersebut; hasilnya tidak boleh disebut penilaian masa depan. Fitur akun tersedia sebagai snapshot terpisah, tanpa memaksakan model akun pada riwayat yang jarang.

## Protokol tiga model

Isolation Forest memakai kebalikan score_samples agar skor lebih tinggi berarti lebih anomali. LOF memakai novelty=False dan kebalikan negative_outlier_factor_ pada observasi fit. ECOD memakai decision_scores_ pada observasi fit. Tidak ada scoring holdout gabungan ECOD yang diklaim sebagai replay temporal. [Dokumentasi scikit-learn](https://scikit-learn.org/stable/modules/outlier_detection.html) dan [implementasi resmi ECOD](https://pyod.readthedocs.io/en/latest/_modules/pyod/models/ecod.html) menjadi rujukan kontrak skor.

Skor mentah tidak dibandingkan langsung lintas algoritma atau kanal. Persentil memakai average ranks pada set per kanal dan bukan probabilitas fraud. Konsensus adalah rerata persentil IF, ECOD, dan LOF; ini merupakan antrean tinjauan yang transparan, bukan model terlatih keempat atau bukti kebenaran hasil.

## Parameter dan stabilitas

| channel | model | variant | n_estimators | max_samples | seed | baseline | threshold_used_for_priority | n_neighbors | requested_n_neighbors | adjustment_reason | fit_warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cobrandgen | if | trees=100;max_samples=256;seed=11 | 100.0 | 256.0 | 11.0 | True |  |  |  |  |  |
| cobrandgen | if | trees=100;max_samples=256;seed=42 | 100.0 | 256.0 | 42.0 | False |  |  |  |  |  |
| cobrandgen | if | trees=100;max_samples=256;seed=73 | 100.0 | 256.0 | 73.0 | False |  |  |  |  |  |
| cobrandgen | if | trees=100;max_samples=1024;seed=11 | 100.0 | 1024.0 | 11.0 | False |  |  |  |  |  |
| cobrandgen | if | trees=100;max_samples=1024;seed=42 | 100.0 | 1024.0 | 42.0 | False |  |  |  |  |  |
| cobrandgen | if | trees=100;max_samples=1024;seed=73 | 100.0 | 1024.0 | 73.0 | False |  |  |  |  |  |
| cobrandgen | if | trees=300;max_samples=256;seed=11 | 300.0 | 256.0 | 11.0 | False |  |  |  |  |  |
| cobrandgen | if | trees=300;max_samples=256;seed=42 | 300.0 | 256.0 | 42.0 | False |  |  |  |  |  |
| cobrandgen | if | trees=300;max_samples=256;seed=73 | 300.0 | 256.0 | 73.0 | False |  |  |  |  |  |
| cobrandgen | if | trees=300;max_samples=1024;seed=11 | 300.0 | 1024.0 | 11.0 | False |  |  |  |  |  |
| cobrandgen | if | trees=300;max_samples=1024;seed=42 | 300.0 | 1024.0 | 42.0 | False |  |  |  |  |  |
| cobrandgen | if | trees=300;max_samples=1024;seed=73 | 300.0 | 1024.0 | 73.0 | False |  |  |  |  |  |
| cobrandgen | ecod | empirical_snapshot |  |  |  | True | False |  |  |  |  |
| cobrandgen | lof | requested_k=10;n_neighbors=10;novelty=False |  |  |  | True |  | 10.0 | 10.0 | none | [] |
| cobrandgen | lof | requested_k=20;n_neighbors=20;novelty=False |  |  |  | False |  | 20.0 | 20.0 | none | [] |
| cobrandgen | lof | requested_k=50;n_neighbors=50;novelty=False |  |  |  | False |  | 50.0 | 50.0 | none | [] |
| retail | if | trees=100;max_samples=178;seed=11 | 100.0 | 178.0 | 11.0 | True |  |  |  |  |  |
| retail | if | trees=100;max_samples=178;seed=42 | 100.0 | 178.0 | 42.0 | False |  |  |  |  |  |
| retail | if | trees=100;max_samples=178;seed=73 | 100.0 | 178.0 | 73.0 | False |  |  |  |  |  |
| retail | if | trees=300;max_samples=178;seed=11 | 300.0 | 178.0 | 11.0 | False |  |  |  |  |  |
| retail | if | trees=300;max_samples=178;seed=42 | 300.0 | 178.0 | 42.0 | False |  |  |  |  |  |
| retail | if | trees=300;max_samples=178;seed=73 | 300.0 | 178.0 | 73.0 | False |  |  |  |  |  |
| retail | ecod | empirical_snapshot |  |  |  | True | False |  |  |  |  |
| retail | lof | requested_k=10;n_neighbors=10;novelty=False |  |  |  | True |  | 10.0 | 10.0 | none | [] |
| retail | lof | requested_k=20;n_neighbors=20;novelty=False |  |  |  | False |  | 20.0 | 20.0 | none | [] |
| retail | lof | requested_k=50;n_neighbors=50;novelty=False |  |  |  | False |  | 50.0 | 50.0 | none | [] |

| channel | model | comparison | baseline_variant | variant | reference_rows | k_requested | k_effective | intersection_count | top_k_overlap | jaccard | spearman | sample_train_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=256;seed=42 | 14083 | 10 | 10 | 6 | 0.6 | 0.42857 | 0.95063 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=256;seed=42 | 14083 | 25 | 25 | 18 | 0.72 | 0.5625 | 0.95063 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=256;seed=42 | 14083 | 50 | 50 | 40 | 0.8 | 0.66667 | 0.95063 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=256;seed=73 | 14083 | 10 | 10 | 8 | 0.8 | 0.66667 | 0.96769 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=256;seed=73 | 14083 | 25 | 25 | 19 | 0.76 | 0.6129 | 0.96769 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=256;seed=73 | 14083 | 50 | 50 | 38 | 0.76 | 0.6129 | 0.96769 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=1024;seed=11 | 14083 | 10 | 10 | 7 | 0.7 | 0.53846 | 0.98403 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=1024;seed=11 | 14083 | 25 | 25 | 17 | 0.68 | 0.51515 | 0.98403 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=1024;seed=11 | 14083 | 50 | 50 | 39 | 0.78 | 0.63934 | 0.98403 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=1024;seed=42 | 14083 | 10 | 10 | 6 | 0.6 | 0.42857 | 0.9506 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=1024;seed=42 | 14083 | 25 | 25 | 16 | 0.64 | 0.47059 | 0.9506 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=1024;seed=42 | 14083 | 50 | 50 | 36 | 0.72 | 0.5625 | 0.9506 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=1024;seed=73 | 14083 | 10 | 10 | 6 | 0.6 | 0.42857 | 0.95694 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=1024;seed=73 | 14083 | 25 | 25 | 18 | 0.72 | 0.5625 | 0.95694 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=100;max_samples=1024;seed=73 | 14083 | 50 | 50 | 35 | 0.7 | 0.53846 | 0.95694 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=256;seed=11 | 14083 | 10 | 10 | 9 | 0.9 | 0.81818 | 0.98923 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=256;seed=11 | 14083 | 25 | 25 | 21 | 0.84 | 0.72414 | 0.98923 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=256;seed=11 | 14083 | 50 | 50 | 46 | 0.92 | 0.85185 | 0.98923 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=256;seed=42 | 14083 | 10 | 10 | 7 | 0.7 | 0.53846 | 0.97168 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=256;seed=42 | 14083 | 25 | 25 | 20 | 0.8 | 0.66667 | 0.97168 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=256;seed=42 | 14083 | 50 | 50 | 43 | 0.86 | 0.75439 | 0.97168 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=256;seed=73 | 14083 | 10 | 10 | 8 | 0.8 | 0.66667 | 0.98029 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=256;seed=73 | 14083 | 25 | 25 | 19 | 0.76 | 0.6129 | 0.98029 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=256;seed=73 | 14083 | 50 | 50 | 42 | 0.84 | 0.72414 | 0.98029 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=1024;seed=11 | 14083 | 10 | 10 | 7 | 0.7 | 0.53846 | 0.98382 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=1024;seed=11 | 14083 | 25 | 25 | 17 | 0.68 | 0.51515 | 0.98382 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=1024;seed=11 | 14083 | 50 | 50 | 38 | 0.76 | 0.6129 | 0.98382 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=1024;seed=42 | 14083 | 10 | 10 | 6 | 0.6 | 0.42857 | 0.96815 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=1024;seed=42 | 14083 | 25 | 25 | 16 | 0.64 | 0.47059 | 0.96815 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=1024;seed=42 | 14083 | 50 | 50 | 37 | 0.74 | 0.5873 | 0.96815 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=1024;seed=73 | 14083 | 10 | 10 | 6 | 0.6 | 0.42857 | 0.96768 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=1024;seed=73 | 14083 | 25 | 25 | 16 | 0.64 | 0.47059 | 0.96768 |  |
| cobrandgen | if | parameter_or_seed | trees=100;max_samples=256;seed=11 | trees=300;max_samples=1024;seed=73 | 14083 | 50 | 50 | 35 | 0.7 | 0.53846 | 0.96768 |  |
| cobrandgen | lof | parameter_or_seed | requested_k=10;n_neighbors=10;novelty=False | requested_k=20;n_neighbors=20;novelty=False | 14083 | 10 | 10 | 7 | 0.7 | 0.53846 | 0.54604 |  |
| cobrandgen | lof | parameter_or_seed | requested_k=10;n_neighbors=10;novelty=False | requested_k=20;n_neighbors=20;novelty=False | 14083 | 25 | 25 | 16 | 0.64 | 0.47059 | 0.54604 |  |
| cobrandgen | lof | parameter_or_seed | requested_k=10;n_neighbors=10;novelty=False | requested_k=20;n_neighbors=20;novelty=False | 14083 | 50 | 50 | 30 | 0.6 | 0.42857 | 0.54604 |  |
| cobrandgen | lof | parameter_or_seed | requested_k=10;n_neighbors=10;novelty=False | requested_k=50;n_neighbors=50;novelty=False | 14083 | 10 | 10 | 4 | 0.4 | 0.25 | 0.26444 |  |
| cobrandgen | lof | parameter_or_seed | requested_k=10;n_neighbors=10;novelty=False | requested_k=50;n_neighbors=50;novelty=False | 14083 | 25 | 25 | 9 | 0.36 | 0.21951 | 0.26444 |  |
| cobrandgen | lof | parameter_or_seed | requested_k=10;n_neighbors=10;novelty=False | requested_k=50;n_neighbors=50;novelty=False | 14083 | 50 | 50 | 20 | 0.4 | 0.25 | 0.26444 |  |
| cobrandgen | if | subsample_training | trees=100;max_samples=256;seed=11 | fraction=0.8 | 14083 | 10 | 10 | 7 | 0.7 | 0.53846 | 0.95732 | 11266.0 |
| cobrandgen | if | subsample_training | trees=100;max_samples=256;seed=11 | fraction=0.8 | 14083 | 25 | 25 | 20 | 0.8 | 0.66667 | 0.95732 | 11266.0 |
| cobrandgen | if | subsample_training | trees=100;max_samples=256;seed=11 | fraction=0.8 | 14083 | 50 | 50 | 44 | 0.88 | 0.78571 | 0.95732 | 11266.0 |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=100;max_samples=178;seed=42 | 178 | 10 | 10 | 7 | 0.7 | 0.53846 | 0.97896 |  |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=100;max_samples=178;seed=42 | 178 | 25 | 25 | 23 | 0.92 | 0.85185 | 0.97896 |  |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=100;max_samples=178;seed=42 | 178 | 50 | 50 | 44 | 0.88 | 0.78571 | 0.97896 |  |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=100;max_samples=178;seed=73 | 178 | 10 | 10 | 8 | 0.8 | 0.66667 | 0.97729 |  |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=100;max_samples=178;seed=73 | 178 | 25 | 25 | 23 | 0.92 | 0.85185 | 0.97729 |  |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=100;max_samples=178;seed=73 | 178 | 50 | 50 | 47 | 0.94 | 0.88679 | 0.97729 |  |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=300;max_samples=178;seed=11 | 178 | 10 | 10 | 8 | 0.8 | 0.66667 | 0.99181 |  |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=300;max_samples=178;seed=11 | 178 | 25 | 25 | 23 | 0.92 | 0.85185 | 0.99181 |  |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=300;max_samples=178;seed=11 | 178 | 50 | 50 | 49 | 0.98 | 0.96078 | 0.99181 |  |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=300;max_samples=178;seed=42 | 178 | 10 | 10 | 7 | 0.7 | 0.53846 | 0.98652 |  |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=300;max_samples=178;seed=42 | 178 | 25 | 25 | 23 | 0.92 | 0.85185 | 0.98652 |  |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=300;max_samples=178;seed=42 | 178 | 50 | 50 | 45 | 0.9 | 0.81818 | 0.98652 |  |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=300;max_samples=178;seed=73 | 178 | 10 | 10 | 9 | 0.9 | 0.81818 | 0.98083 |  |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=300;max_samples=178;seed=73 | 178 | 25 | 25 | 23 | 0.92 | 0.85185 | 0.98083 |  |
| retail | if | parameter_or_seed | trees=100;max_samples=178;seed=11 | trees=300;max_samples=178;seed=73 | 178 | 50 | 50 | 49 | 0.98 | 0.96078 | 0.98083 |  |
| retail | lof | parameter_or_seed | requested_k=10;n_neighbors=10;novelty=False | requested_k=20;n_neighbors=20;novelty=False | 178 | 10 | 10 | 7 | 0.7 | 0.53846 | 0.77673 |  |
| retail | lof | parameter_or_seed | requested_k=10;n_neighbors=10;novelty=False | requested_k=20;n_neighbors=20;novelty=False | 178 | 25 | 25 | 15 | 0.6 | 0.42857 | 0.77673 |  |
| retail | lof | parameter_or_seed | requested_k=10;n_neighbors=10;novelty=False | requested_k=20;n_neighbors=20;novelty=False | 178 | 50 | 50 | 44 | 0.88 | 0.78571 | 0.77673 |  |
| retail | lof | parameter_or_seed | requested_k=10;n_neighbors=10;novelty=False | requested_k=50;n_neighbors=50;novelty=False | 178 | 10 | 10 | 1 | 0.1 | 0.05263 | 0.39924 |  |
| retail | lof | parameter_or_seed | requested_k=10;n_neighbors=10;novelty=False | requested_k=50;n_neighbors=50;novelty=False | 178 | 25 | 25 | 8 | 0.32 | 0.19048 | 0.39924 |  |
| retail | lof | parameter_or_seed | requested_k=10;n_neighbors=10;novelty=False | requested_k=50;n_neighbors=50;novelty=False | 178 | 50 | 50 | 26 | 0.52 | 0.35135 | 0.39924 |  |
| retail | if | subsample_training | trees=100;max_samples=178;seed=11 | fraction=0.8 | 178 | 10 | 10 | 7 | 0.7 | 0.53846 | 0.98623 | 142.0 |
| retail | if | subsample_training | trees=100;max_samples=178;seed=11 | fraction=0.8 | 178 | 25 | 25 | 22 | 0.88 | 0.78571 | 0.98623 | 142.0 |
| retail | if | subsample_training | trees=100;max_samples=178;seed=11 | fraction=0.8 | 178 | 50 | 50 | 46 | 0.92 | 0.85185 | 0.98623 | 142.0 |

Stabilitas membandingkan log_key yang sama. Perubahan seed hanya berlaku pada model stokastik; perubahan parameter dan sampel referensi dilaporkan menurut eksperimen aktual. Evaluasi temporal pada observasi masa depan dan eksperimen sintetis belum dilakukan. Konfigurasi serta versi paket disimpan dalam model_evaluation.json dan artefak model.

## Agreement dan sensitivitas ambang

| channel | model_left | model_right | k_requested | k_effective | intersection_count | top_k_overlap | jaccard | spearman |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cobrandgen | if | ecod | 10 | 10 | 6 | 0.6 | 0.42857 | 0.83087 |
| cobrandgen | if | ecod | 25 | 25 | 13 | 0.52 | 0.35135 | 0.83087 |
| cobrandgen | if | ecod | 50 | 50 | 34 | 0.68 | 0.51515 | 0.83087 |
| cobrandgen | if | lof | 10 | 10 | 0 | 0.0 | 0.0 | 0.10276 |
| cobrandgen | if | lof | 25 | 25 | 0 | 0.0 | 0.0 | 0.10276 |
| cobrandgen | if | lof | 50 | 50 | 0 | 0.0 | 0.0 | 0.10276 |
| cobrandgen | ecod | lof | 10 | 10 | 0 | 0.0 | 0.0 | 0.10123 |
| cobrandgen | ecod | lof | 25 | 25 | 0 | 0.0 | 0.0 | 0.10123 |
| cobrandgen | ecod | lof | 50 | 50 | 0 | 0.0 | 0.0 | 0.10123 |
| retail | if | ecod | 10 | 10 | 5 | 0.5 | 0.33333 | 0.80999 |
| retail | if | ecod | 25 | 25 | 17 | 0.68 | 0.51515 | 0.80999 |
| retail | if | ecod | 50 | 50 | 39 | 0.78 | 0.63934 | 0.80999 |
| retail | if | lof | 10 | 10 | 2 | 0.2 | 0.11111 | 0.47169 |
| retail | if | lof | 25 | 25 | 9 | 0.36 | 0.21951 | 0.47169 |
| retail | if | lof | 50 | 50 | 26 | 0.52 | 0.35135 | 0.47169 |
| retail | ecod | lof | 10 | 10 | 3 | 0.3 | 0.17647 | 0.34693 |
| retail | ecod | lof | 25 | 25 | 10 | 0.4 | 0.25 | 0.34693 |
| retail | ecod | lof | 50 | 50 | 27 | 0.54 | 0.36986 | 0.34693 |

| channel | model | capacity_percentage | selected_count | score_at_boundary | rows_tied_at_boundary | rows_above_boundary | selection_rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cobrandgen | if | 1 | 141 | 0.68184 | 1 | 140 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | if | 2 | 282 | 0.65077 | 1 | 281 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | if | 5 | 705 | 0.60409 | 1 | 704 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | if | 10 | 1409 | 0.55869 | 1 | 1408 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | ecod | 1 | 141 | 17.40059 | 1 | 140 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | ecod | 2 | 282 | 15.42323 | 1 | 281 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | ecod | 5 | 705 | 12.52415 | 1 | 704 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | ecod | 10 | 1409 | 10.91848 | 1 | 1408 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | lof | 1 | 141 | 3.43595 | 1 | 140 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | lof | 2 | 282 | 2.15152 | 1 | 281 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | lof | 5 | 705 | 1.56674 | 1 | 704 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | lof | 10 | 1409 | 1.32541 | 1 | 1408 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | consensus | 1 | 141 | 0.95903 | 2 | 139 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | consensus | 2 | 282 | 0.93567 | 1 | 281 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | consensus | 5 | 705 | 0.87176 | 1 | 704 | ordinal_capacity_with_log_key_tiebreak |
| cobrandgen | consensus | 10 | 1409 | 0.79808 | 1 | 1408 | ordinal_capacity_with_log_key_tiebreak |
| retail | if | 1 | 2 | 0.6464 | 1 | 1 | ordinal_capacity_with_log_key_tiebreak |
| retail | if | 2 | 4 | 0.63481 | 2 | 3 | ordinal_capacity_with_log_key_tiebreak |
| retail | if | 5 | 9 | 0.60477 | 1 | 8 | ordinal_capacity_with_log_key_tiebreak |
| retail | if | 10 | 18 | 0.58003 | 1 | 17 | ordinal_capacity_with_log_key_tiebreak |
| retail | ecod | 1 | 2 | 18.26938 | 1 | 1 | ordinal_capacity_with_log_key_tiebreak |
| retail | ecod | 2 | 4 | 17.08335 | 1 | 3 | ordinal_capacity_with_log_key_tiebreak |
| retail | ecod | 5 | 9 | 16.28971 | 1 | 8 | ordinal_capacity_with_log_key_tiebreak |
| retail | ecod | 10 | 18 | 14.89596 | 1 | 17 | ordinal_capacity_with_log_key_tiebreak |
| retail | lof | 1 | 2 | 6.39082 | 1 | 1 | ordinal_capacity_with_log_key_tiebreak |
| retail | lof | 2 | 4 | 5.11415 | 1 | 3 | ordinal_capacity_with_log_key_tiebreak |
| retail | lof | 5 | 9 | 2.94131 | 1 | 8 | ordinal_capacity_with_log_key_tiebreak |
| retail | lof | 10 | 18 | 1.92135 | 1 | 17 | ordinal_capacity_with_log_key_tiebreak |
| retail | consensus | 1 | 2 | 0.9794 | 1 | 1 | ordinal_capacity_with_log_key_tiebreak |
| retail | consensus | 2 | 4 | 0.93633 | 1 | 3 | ordinal_capacity_with_log_key_tiebreak |
| retail | consensus | 5 | 9 | 0.90075 | 1 | 8 | ordinal_capacity_with_log_key_tiebreak |
| retail | consensus | 10 | 18 | 0.85581 | 1 | 17 | ordinal_capacity_with_log_key_tiebreak |

Top-K memakai aturan tie deterministik dan korelasi memakai average ranks sesuai protokol evaluasi. Agreement tinggi hanya berarti hasil konsisten. Banyaknya log yang ditandai mengikuti aturan threshold atau kapasitas tinjauan, bukan estimasi jumlah anomali nyata.

## Prioritas dan bukti investigasi

| channel | investigation_priority | log_count |
| --- | --- | --- |
| cobrandgen | rendah | 13378 |
| cobrandgen | sedang | 564 |
| cobrandgen | tinggi | 141 |
| retail | rendah | 169 |
| retail | sedang | 7 |
| retail | tinggi | 2 |

Prioritas tinggi dialokasikan pada ceil(1% × jumlah log kanal), sedang hingga ceil(5%), dan rendah untuk sisanya berdasarkan ranking konsensus. Ini adalah asumsi kapasitas awal yang dapat disesuaikan; ia tidak menyatakan prevalensi fraud. Ambang skor kontinu pada dashboard merupakan filter tambahan dan tidak identik dengan kuota peringkat.

Ringkasan berikut mencakup sepuluh log dengan peringkat konsensus tertinggi per kanal, atau seluruh log bila jumlahnya kurang dari sepuluh. Contoh per log tidak ditampilkan di dokumen ini.

| channel | selected_log_count | median_recorded_amount | min_consensus_score | max_consensus_score |
| --- | --- | --- | --- | --- |
| cobrandgen | 10 | 11000.0 | 0.99063 | 0.99413 |
| retail | 10 | 15000.0 | 0.897 | 0.98315 |

Kasus individual dan bukti lengkap tetap diproduksi pada CSV internal lokal top_investigation_cases.csv dan anomaly_scores.csv untuk dashboard serta investigasi berizin. Dokumen ini hanya menampilkan agregat. `explanation_kind` menandai alasan deskriptif. Deviasi harga, jumlah log historis, interval, dan konteks pengulangan dapat dihitung ulang; alasan tersebut tidak diklaim sebagai kontribusi fitur yang dihitung dari model. Kasus tanpa deviasi marginal ekstrem memerlukan pemeriksaan kombinasi fitur lebih lanjut; kelangkaan kombinasi belum diuji secara terpisah.

## Rekomendasi dan batas interpretasi

Gunakan konsensus sebagai antrean tinjauan awal dan periksa perbedaan antar model. Rentang agreement/stabilitas terlampir hanya mengukur konsistensi snapshot; tidak cukup untuk memilih model terbaik atau menyimpulkan fraud. Retail dengan sedikit log dan konsentrasi akun tinggi memerlukan penafsiran eksploratif.

| channel | distinct_feature_vectors | max_identical_vectors | if_mean_stability_spearman | lof_mean_stability_spearman |
| --- | --- | --- | --- | --- |
| cobrandgen | 11514 | 7 | 0.97007 | 0.40524 |
| retail | 164 | 2 | 0.98308 | 0.58798 |

**cobrandgen**: IF rata-rata korelasi stabilitas 0.970; LOF rata-rata korelasi stabilitas 0.405. Korelasi antar model berada pada 0.101–0.831. Terdapat 11514 vektor fitur berbeda dari 14083 log; blok identik terbesar 7 baris. IF lebih konsisten secara rata-rata pada variasi yang diuji; cakupan variasi kedua algoritma berbeda sehingga ini bukan bukti model terbaik. Tinjau kasus yang disepakati maupun yang berbeda antar model; hasil ini belum mengukur ketepatan investigasi.

**retail**: IF rata-rata korelasi stabilitas 0.983; LOF rata-rata korelasi stabilitas 0.588. Korelasi antar model berada pada 0.347–0.810. Terdapat 164 vektor fitur berbeda dari 178 log; blok identik terbesar 2 baris. IF lebih konsisten secara rata-rata pada variasi yang diuji; cakupan variasi kedua algoritma berbeda sehingga ini bukan bukti model terbaik. Tinjau kasus yang disepakati maupun yang berbeda antar model; hasil ini belum mengukur ketepatan investigasi.

Encoding waktu versi 2 mempertahankan menit/detik yang tersedia pada sumber. Uji awal dengan pembulatan jam menghasilkan banyak vektor identik dan peringatan LOF; hasil akhir dihitung ulang memakai versi 2 tanpa deduplikasi atau jitter. Metadata mencatat blok fitur identik, requested/effective k, serta warning setiap varian. k disesuaikan bila blok identik terlalu besar; warning hasil tidak valid menghentikan run.

Rekomendasi ini dibatasi pada konsistensi ranking snapshot. Retail berukuran kecil dan terkonsentrasi pada beberapa akun sehingga bersifat eksploratif. Belum tersedia label hasil investigasi, bukti pembayaran, mapping pricing–package, atau riwayat status yang memungkinkan klaim fraud, churn, pendapatan bersih, atau accuracy/precision/recall/F1/ROC-AUC pada anomali nyata.

## Keputusan bisnis yang didukung

Analis dapat memulai dari antrean prioritas per kanal, memeriksa bukti statistik dan riwayat akun, lalu mengonfirmasi proses bisnis pada pemilik data. Pemeriksaan tanggal CANCEL yang tidak lengkap dan pola pencatatan berulang merupakan agenda kualitas data tersendiri. Tindak lanjut kasus harus mencatat hasil tinjauan manusia sebelum menjadi label evaluasi yang sah.

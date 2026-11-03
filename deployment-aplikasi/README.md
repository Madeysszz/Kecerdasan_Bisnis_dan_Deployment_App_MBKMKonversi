# Deployment Aplikasi Norton

Implementasi dashboard dan GitHub Actions CI untuk mata kuliah Deployment Aplikasi. Folder ini berasal dari salinan `DEPLOYMENT_KECERDASAN BISNIS` dan berjalan mandiri. Folder sumber tersebut serta `kecerdasan-bisnis` tetap utuh.

## Struktur

```text
deployment-aplikasi/
├── app.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .streamlit/config.toml
├── tests/
│   ├── conftest.py
│   └── test_dashboard.py
├── scripts/smoke_test.py
├── docs/DEPLOYMENT_CI.md
└── README.md
```

Workflow berada di [`.github/workflows/deployment-ci.yml`](../.github/workflows/deployment-ci.yml). Penjelasan preparation, testing, hasil verifikasi, rencana Docker, dan bukti BAB IV tersedia pada [dokumentasi Deployment CI](docs/DEPLOYMENT_CI.md).

## Persiapan Python 3.12

Jalankan dari folder ini:

```bash
python -m venv .venv
```

Aktifkan environment dengan `source .venv/Scripts/activate` pada Git Bash Windows, atau `source .venv/bin/activate` pada Linux/macOS. Pada PowerShell, gunakan interpreter `.\.venv\Scripts\python.exe` sebagai pengganti `python` pada perintah berikut.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Buka `http://localhost:8501`. Tekan `Ctrl+C` pada terminal server untuk menghentikannya. Konfigurasi Streamlit memakai port 8501 dan menonaktifkan pengiriman statistik penggunaan.

## Data aplikasi

Secara default, lokasi artefak adalah folder deployment ini sendiri. Tanpa artefak, aplikasi menampilkan pemberitahuan bahwa data belum tersedia. Untuk menjalankan empat halaman dengan data berizin, atur environment variable `NORTON_DATA_ROOT` menuju direktori artefak berikut:

```text
direktori-artefak/
├── data/processed/sanitized_logs.csv
└── outputs/
    ├── tables/
    │   ├── anomaly_scores.csv
    │   ├── model_agreement.csv
    │   ├── model_stability.csv
    │   ├── threshold_sensitivity.csv
    │   └── experiment_parameters.csv
    └── reports/model_evaluation.json
```

Log dan skor per log diperlukan untuk empat halaman; tabel evaluasi serta rekomendasi merupakan pendukung halaman perbandingan. Tidak ada data Norton yang disalin ke folder ini. Folder `data/`, `outputs/`, environment, dan laporan pengujian lokal diabaikan Git. Jangan memakai data privat untuk menjalankan CI.

## Pengujian lokal

```bash
python -m compileall -q app.py tests scripts
python -m pytest tests -q --junitxml=test-results/pytest.xml
python scripts/smoke_test.py
```

Pytest menjalankan 12 kasus dengan data sintetis yang dibuat di direktori sementara: empat halaman, filter kanal/status/tanggal, tiga pilihan model, filter kosong, konteks akun, dan artefak hilang. Smoke test memulai server sementara tanpa data privat, memeriksa endpoint health dan halaman utama, lalu menghentikan prosesnya. Hasil berada di `test-results/`.

## GitHub Actions

Setiap push dan pull request menuju `main` menjalankan workflow Python 3.12. Tahapannya: checkout, setup Python, instalasi, validasi syntax, pytest/AppTest, smoke test, ringkasan hasil, dan unggahan laporan. Job tidak memanggil pipeline analisis atau training model. Ringkasan tetap dibuat ketika suatu tahap gagal; kegagalan tes tetap menyebabkan job gagal.

## Rencana Docker

Build context adalah folder ini, sehingga Docker tidak memerlukan folder Kecerdasan Bisnis:

```bash
docker build -t norton-deployment-ci .
docker run --rm --name norton-deployment-ci -p 127.0.0.1:8501:8501 norton-deployment-ci
```

Tanpa bind mount artefak, aplikasi menampilkan pemberitahuan data belum tersedia. Pada lingkungan berizin, pasang direktori artefak read-only dan arahkan `NORTON_DATA_ROOT` ke lokasi mount di container. `.dockerignore` membatasi isi image pada aplikasi, requirements, dan konfigurasi Streamlit.

Build/run Docker serta hosting online belum dilakukan. Keberhasilan CI, jika sudah tercatat di Actions, membuktikan rangkaian pengujian otomatis; hal tersebut tidak menggantikan bukti deployment aplikasi ke server.

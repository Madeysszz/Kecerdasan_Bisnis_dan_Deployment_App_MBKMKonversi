# Deployment Kecerdasan Bisnis

Folder ini memuat implementasi dashboard dan konfigurasi deployment aplikasi Norton untuk konversi MBKM. Analisis, audit, feature engineering, dan pemodelan tetap berada di `kecerdasan-bisnis/`. Dashboard menyajikan hasil analisis tersebut melalui empat halaman tanpa melakukan training ulang.

## Struktur file

| File | Fungsi |
| --- | --- |
| `app.py` | Aplikasi Streamlit: Executive Overview, Anomaly Monitoring, Model Comparison, dan Transaction Investigation. |
| `requirements.txt` | Dependensi aplikasi dashboard. |
| `Dockerfile` | Konfigurasi image aplikasi berbasis Python 3.12. |
| `Dockerfile.dockerignore` | Membatasi build context pada kode aplikasi dan hasil evaluasi agregat yang diperlukan. |
| `README.md` | Panduan menjalankan dan menyiapkan deployment. |

## Artefak yang diperlukan

Dashboard membaca dua berkas privat hasil pipeline di folder saudara `kecerdasan-bisnis/`:

- `data/processed/sanitized_logs.csv`
- `outputs/tables/anomaly_scores.csv`

Keduanya tetap lokal dan diabaikan Git. Untuk halaman perbandingan model, aplikasi juga membaca empat tabel agregat `model_agreement.csv`, `model_stability.csv`, `threshold_sensitivity.csv`, `experiment_parameters.csv`, serta `outputs/reports/model_evaluation.json`. Berkas agregat tersebut sudah disertakan dalam repository.

Clone repository tanpa artefak privat akan menampilkan pemberitahuan bahwa data dashboard belum tersedia. Siapkan hasil pipeline berizin sesuai [panduan analisis](../kecerdasan-bisnis/README.md). Pemindahan folder aplikasi tidak memerlukan pembentukan ulang fitur atau training model yang artefaknya sudah tersedia.

## Menjalankan secara lokal

Jalankan dari root repository menggunakan Python 3.12 pada environment yang aktif:

```bash
python -m pip install -r "DEPLOYMENT_KECERDASAN BISNIS/requirements.txt"
python -m streamlit run "DEPLOYMENT_KECERDASAN BISNIS/app.py" --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

Pada workspace Windows ini, environment proyek analisis yang sudah tersedia juga dapat digunakan dari Git Bash:

```bash
./kecerdasan-bisnis/.venv/Scripts/python.exe -m streamlit run "DEPLOYMENT_KECERDASAN BISNIS/app.py"
```

Buka `http://localhost:8501`. Tekan `Ctrl+C` pada terminal yang menjalankan aplikasi untuk menghentikannya.

## Menjalankan dengan Docker

Gunakan Docker Engine atau Docker Desktop dengan Linux containers. Build context harus root repository karena image menyertakan hasil evaluasi agregat dari folder analisis. Perintah berikut dijalankan melalui PowerShell dari root repository:

```powershell
docker build -t norton-bi-dashboard -f "DEPLOYMENT_KECERDASAN BISNIS/Dockerfile" .

docker run --rm --name norton-bi-dashboard -p 127.0.0.1:8501:8501 `
  --mount "type=bind,source=$((Get-Location).Path)/kecerdasan-bisnis/data/processed/sanitized_logs.csv,target=/app/kecerdasan-bisnis/data/processed/sanitized_logs.csv,readonly" `
  --mount "type=bind,source=$((Get-Location).Path)/kecerdasan-bisnis/outputs/tables/anomaly_scores.csv,target=/app/kecerdasan-bisnis/outputs/tables/anomaly_scores.csv,readonly" `
  norton-bi-dashboard
```

Image hanya memuat kode, dependensi, dan evaluasi agregat. Dua artefak privat dihubungkan saat runtime sebagai bind mount read-only. Dataset mentah, database, model biner, environment lokal, dan skor per log tidak dimasukkan ke build context atau image. Kedua file sumber bind mount harus sudah tersedia sebelum container dijalankan.

Health check menggunakan endpoint `/_stcore/health` untuk memeriksa server Streamlit. Status server sehat tidak membuktikan data telah tersedia; jika artefak belum dipasang, aplikasi menampilkan pemberitahuan. Untuk menghentikan container dari terminal lain:

```powershell
docker stop norton-bi-dashboard
```

## Cakupan deployment dan bukti laporan

Folder ini menyediakan aplikasi, dependensi, konfigurasi container, dan panduan operasi lokal. Hosting online belum dilakukan. Screenshot empat halaman yang benar-benar berjalan, hasil health check, dan status container dapat menjadi bukti implementasi deployment setelah langkah terkait dijalankan. Konfigurasi Docker saja tidak dilaporkan sebagai bukti container telah berhasil dijalankan.

Pengujian aplikasi dijalankan dari folder `kecerdasan-bisnis`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_dashboard.py -v
```

Pengujian menggunakan artefak lokal untuk memeriksa empat halaman, filter kanal/status, perubahan model, dan filter kosong. Prioritas investigasi tetap merupakan antrean tinjauan, bukan label fraud.

Rujukan konfigurasi: [panduan Docker Streamlit](https://docs.streamlit.io/deploy/tutorials/docker) dan [aturan build context serta Dockerfile-specific ignore file](https://docs.docker.com/build/concepts/context/#dockerignore-files).

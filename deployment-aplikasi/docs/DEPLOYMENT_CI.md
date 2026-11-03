# Deployment Aplikasi Norton — Preparation, Testing, dan GitHub Actions CI

## 1. Strategi dan cakupan implementasi

Pekerjaan ini menyiapkan aplikasi Streamlit dan continuous integration untuk memenuhi indikator mata kuliah Deployment Aplikasi. Aplikasi disalin ke `deployment-aplikasi/`, sedangkan `kecerdasan-bisnis/` serta `DEPLOYMENT_KECERDASAN BISNIS/` tetap dipertahankan. Dashboard tetap mempunyai empat halaman dengan logika perhitungan, filter, skor, dan konteks akun yang sama seperti aplikasi sumber.

CI memverifikasi kemampuan aplikasi berjalan pada Python 3.12 menggunakan data sintetis. Tidak ada training ulang model, penyalinan dataset Norton, atau pembacaan database operasional. Docker disediakan sebagai rencana pengemasan aplikasi; workflow ini tidak mem-build image, mendorong image ke registry, atau menerbitkan aplikasi ke hosting.

## 2. Audit repository dan pemisahan proyek

Audit menemukan aplikasi awal membaca dua artefak privat melalui lokasi folder Kecerdasan Bisnis. Dependensi langsungnya adalah pandas, Streamlit, dan Plotly. Pengujian awal juga memakai artefak privat, sehingga tidak sesuai untuk CI tanpa data. Salinan baru mengubah penentuan root artefak dan menyesuaikan pengujian agar mandiri.

| Komponen | Sumber | Hasil di folder baru | Penyesuaian |
| --- | --- | --- | --- |
| Aplikasi | `DEPLOYMENT_KECERDASAN BISNIS/app.py` | `deployment-aplikasi/app.py` | Tambahan import `os` dan root artefak dari environment/folder aplikasi. |
| Dependensi | `DEPLOYMENT_KECERDASAN BISNIS/requirements.txt` | `deployment-aplikasi/requirements.txt` | Tiga pin aplikasi dipertahankan; pytest ditambahkan untuk CI. |
| Dockerfile | `DEPLOYMENT_KECERDASAN BISNIS/Dockerfile` | `deployment-aplikasi/Dockerfile` | Build context mandiri; path folder sumber dan COPY agregat asli dikeluarkan dari salinan. |
| Ignore build | `DEPLOYMENT_KECERDASAN BISNIS/Dockerfile.dockerignore` | `deployment-aplikasi/.dockerignore` | Aturan disesuaikan untuk app, requirements, dan config lokal. |
| Pengujian | Skenario pada `kecerdasan-bisnis/tests/test_dashboard.py` | `deployment-aplikasi/tests/test_dashboard.py` | Diadaptasi menjadi pytest, memakai fixture sintetis, dan menambahkan pemeriksaan perilaku UI. |

File baru mencakup `.streamlit/config.toml`, `.gitignore`, `tests/conftest.py`, `scripts/smoke_test.py`, README, dokumentasi ini, dan `.github/workflows/deployment-ci.yml`. Tidak ada file sumber yang dipindahkan atau dihapus. Pemeriksaan fingerprint membandingkan 104 file sumber/artefak dengan keadaan awal pekerjaan; seluruhnya tetap sama. Environment dan cache tidak dimasukkan dalam pembandingan konten proyek. Perubahan notebook yang sudah ada sebelum pekerjaan tetap tidak dimasukkan ke commit ini.

Perbandingan AST juga memastikan delapan fungsi aplikasi tidak berubah. Perubahan pada salinan aplikasi terbatas pada import dan penentuan direktori data.

## 3. Tahap preparation

Environment pengembangan baru dibuat pada `deployment-aplikasi/.venv` menggunakan Python 3.12.14. Versi dependensi yang dipakai adalah pandas 3.1.0, Streamlit 1.66.1, Plotly 7.1.0, dan pytest 9.2.0. Instalasi dilakukan hanya pada environment baru; environment proyek Kecerdasan Bisnis tidak diubah.

Konfigurasi `.streamlit/config.toml` menentukan mode headless, alamat server `0.0.0.0`, port 8501, dan penonaktifan statistik penggunaan. Variabel `NORTON_DATA_ROOT` bersifat opsional; tanpa variabel tersebut, aplikasi mencari artefak di folder deployment sendiri. Tidak ada path absolut atau import menuju proyek Kecerdasan Bisnis dalam aplikasi, tests, Dockerfile, atau workflow baru.

Sumber: `deployment-aplikasi/app.py`, baris 1–10.

```python
import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(os.environ.get("NORTON_DATA_ROOT", Path(__file__).resolve().parent)).expanduser().resolve()
```

Cuplikan tersebut berasal dari source aplikasi salinan. Lokasi data berizin dapat ditentukan saat aplikasi dijalankan, sementara CI mengarahkan root ke direktori sementara. Jika dua artefak wajib tidak tersedia, fungsi `main` menampilkan pemberitahuan dan berhenti dengan tertib. Perilaku ini dipertahankan dari aplikasi sumber.

## 4. Tahap testing

Fixture pada `tests/conftest.py`, fungsi `dashboard_root`, membentuk delapan log sintetis: empat cobrandgen dan empat retail, enam akun buatan, serta total nilai buatan 1.260. Tanggal pengujian berada pada 1–4 Januari 2030. Nama, jumlah, nilai, skor, dan rekomendasi dibuat untuk skenario UI; semuanya tidak berasal dari eksperimen Norton dan tidak digunakan untuk mengukur kualitas model.

Log dan skor sintetis ditulis pada direktori sementara pytest, bukan disimpan sebagai data per log dalam repository. Tabel perbandingan dummy hanya menyediakan konten sintetis untuk menguji rendering. Tidak ada fit model di dalam fixture.

| Kelompok pengujian | Jumlah kasus | Perilaku yang diverifikasi |
| --- | ---: | --- |
| Empat halaman dashboard | 4 | Header halaman, metrik/dataset, dan tidak ada exception. |
| Filter kanal dan status | 1 | Retail berisi empat log; retail ACTIVE dua log dengan nilai 120. |
| Pemilihan IF, ECOD, LOF | 3 | Pada ambang 0,99, jumlah sintetis yang lolos masing-masing 2, 1, dan 4. |
| Filter kosong | 1 | Pesan tidak ada log dan tidak ada metrik hasil. |
| Rentang tanggal UTC | 1 | Filter inklusif 2–3 Januari memilih empat log dengan nilai 630. |
| Konteks investigasi akun | 1 | Riwayat akun di luar filter tanggal tetap tersedia. |
| Artefak tidak tersedia | 1 | Pemberitahuan data belum tersedia tanpa exception. |
| Total | 12 | Tidak ada skip, xfail, atau tes yang dinonaktifkan. |

Sumber: `deployment-aplikasi/tests/test_dashboard.py`, baris 9–19.

```python
@pytest.mark.parametrize("page", [
    "Executive Overview", "Anomaly Monitoring", "Model Comparison", "Transaction Investigation",
])
def test_four_pages_render_with_synthetic_outputs(dashboard, page):
    dashboard.sidebar.radio[0].set_value(page).run()
    assert not dashboard.exception
    assert dashboard.header[0].value == page
    if page == "Executive Overview":
        assert [item.value for item in dashboard.metric] == ["8", "1,260", "6"]
    else:
        assert len(dashboard.dataframe) > 0
```

Cuplikan asli tersebut menjalankan halaman yang diparameterisasi melalui Streamlit AppTest. Pemeriksaan tidak hanya memastikan tidak ada exception, tetapi juga memastikan halaman dan hasil benar-benar tampil. Dengan demikian, berhenti karena data hilang tidak dianggap sebagai keberhasilan rendering halaman lengkap.

Smoke test pada `scripts/smoke_test.py`, fungsi `main`, membentuk direktori data kosong, memulai server Streamlit pada port lokal sementara, dan memeriksa `/_stcore/health` serta `/`. Proses dihentikan dalam blok `finally`, termasuk ketika pemeriksaan gagal. `test-results/smoke.json` mencatat status HTTP, penggunaan data privat, dan pembersihan proses. Pemeriksaan HTTP melengkapi AppTest; ia tidak menggantikan validasi isi empat halaman.

## 5. Implementasi GitHub Actions

Workflow [deployment-ci.yml](../../.github/workflows/deployment-ci.yml) menggunakan event `push` dan `pull_request` menuju `main`. Job `deployment-tests` memakai `ubuntu-latest`, Python 3.12, batas waktu sepuluh menit, dan default working directory `deployment-aplikasi`. Hak token dibatasi `contents: read`; workflow tidak membutuhkan kredensial data Norton atau secret deployment.

Urutan prosesnya adalah checkout repository, setup Python, instalasi dari requirements lokal, validasi syntax, pytest/AppTest, smoke test tanpa data privat, penulisan job summary, dan unggahan laporan. Action resmi yang digunakan adalah checkout v7.0.1, setup-python v7.0.0, dan upload-artifact v7.0.2.

Sumber: `.github/workflows/deployment-ci.yml`, baris 32–47.

```yaml
      - name: Install dependencies
        id: install
        run: python -m pip install -r requirements.txt

      - name: Validate Python syntax
        id: syntax
        run: python -m compileall -q app.py tests scripts

      - name: Run pytest and Streamlit AppTest
        id: tests
        run: python -m pytest tests -q --junitxml=test-results/pytest.xml

      - name: Smoke test without private data
        id: smoke
        if: ${{ always() && steps.install.outcome == 'success' && steps.syntax.outcome == 'success' }}
        run: python scripts/smoke_test.py
```

Validasi syntax memproses `app.py`, `tests`, dan `scripts` saja. Perintah pytest menghasilkan JUnit XML. Smoke test tetap dijalankan setelah kegagalan pytest apabila instalasi dan syntax berhasil, tanpa mengubah status gagal job. Langkah summary serta upload menggunakan `always()`. Apabila tes tidak sempat berjalan, hasilnya dilaporkan sebagai skipped/tidak berjalan pada status step, bukan sebagai tes lulus. Tidak ada `continue-on-error` atau perintah yang menyembunyikan kegagalan pengujian.

Ringkasan terdapat pada tab Summary sebuah run. Artifact `deployment-ci-reports` berisi `pytest.xml`, `smoke.json`, serta log server bila langkah terkait sempat dijalankan. Artifact disimpan selama 14 hari dan hanya berisi hasil pengujian sintetis. Working directory pada `run` tidak berlaku untuk action upload, sehingga path artifact ditulis relatif terhadap root repository.

## 6. Hasil verifikasi

### Verifikasi lokal — 3 November 2026

| Pemeriksaan | Hasil aktual |
| --- | --- |
| Instalasi dari requirements pada environment baru | Berhasil. |
| `python -m pip check` | Tidak ada dependensi rusak. |
| `python -m compileall -q app.py tests scripts` | Lulus. |
| `python -m pytest tests -q --junitxml=test-results/pytest.xml` | 12 passed dalam 5,90 detik; 0 gagal, 0 skipped. |
| `python scripts/smoke_test.py` | Passed; health HTTP 200 dan halaman utama HTTP 200. |
| Data pada smoke test | Direktori sementara kosong; data privat tidak digunakan. |
| Pembersihan smoke server | Proses server dihentikan. |
| actionlint v1.7.12 | Workflow valid; exit code 0. |
| Fingerprint dua folder sumber | 104 file sumber/artefak tetap sama dari baseline. |
| Docker build/run | Belum dilakukan; Docker tidak tersedia pada mesin verifikasi. |
| Hosting aplikasi | Belum dilakukan. |

Versi actionlint diambil dari rilis resminya dan checksum arsip diperiksa sebelum digunakan. Angka durasi pengujian merupakan catatan eksekusi lokal ini, bukan target performa atau jaminan durasi runner GitHub.

### Verifikasi GitHub Actions

Workflow sudah berjalan di GitHub dan selesai dengan kesimpulan **success**. Bukti diperiksa melalui metadata run, status setiap langkah job, log pengujian, dan daftar artifact. Repository tetap private.

| Informasi | Hasil terverifikasi |
| --- | --- |
| Workflow | Norton Deployment CI |
| Event / branch | Push ke `main` |
| Commit implementasi yang diuji | [`432d9ab0f70ad2183b56efa91b1c7544165606d0`](https://github.com/Madeysszz/Kecerdasan_Bisnis_dan_Deployment_App_MBKMKonversi/commit/432d9ab0f70ad2183b56efa91b1c7544165606d0) |
| Run | [Run #1 — 41648175293](https://github.com/Madeysszz/Kecerdasan_Bisnis_dan_Deployment_App_MBKMKonversi/actions/runs/41648175293) |
| Status akhir | Completed / success |
| Environment | GitHub-hosted Ubuntu, Python 3.12 |
| Pytest / Streamlit AppTest pada runner | 12 passed dalam 4,59 detik; tidak ada tes gagal atau skipped. |
| Smoke test pada runner | Passed; health HTTP 200, halaman utama HTTP 200, data privat tidak digunakan, server dihentikan. |
| Job Summary | Langkah penulisan ringkasan berhasil. |
| Artifact | `deployment-ci-reports`, ID `13236570960`; unggahan berhasil. |
| Selesai pada | 3 November 2026; log tes dan unggahan artifact tercatat sekitar 13:52 UTC / 20:52 WIB. |

Checkout, setup Python, instalasi, validasi syntax, pytest/AppTest, smoke test, ringkasan, dan unggahan artifact semuanya selesai sukses. Dokumentasi hasil ini dicatat melalui commit lanjutan setelah run implementasi selesai; tautan di atas secara khusus merujuk commit implementasi yang benar-benar diuji. Keberhasilan run tersebut adalah bukti CI, bukan deployment Docker atau hosting aplikasi.

## 7. Rencana deployment Docker

Dockerfile salinan memakai base image `python:3.12-slim` dan working directory `/app`. Instruksi COPY hanya mengambil `requirements.txt`, `app.py`, dan `.streamlit/config.toml` dari build context `deployment-aplikasi/`. Tidak ada COPY data Norton, database, artefak model, atau file dari folder sumber.

```bash
cd deployment-aplikasi
docker build -t norton-deployment-ci .
docker run --rm --name norton-deployment-ci -p 127.0.0.1:8501:8501 norton-deployment-ci
```

Untuk penggunaan berizin, direktori artefak dapat dipasang read-only pada container dan `NORTON_DATA_ROOT` diarahkan ke lokasi mount. Image tidak menyertakan data privat. Tanpa mount, aplikasi menunjukkan pemberitahuan data belum tersedia. Tahap berikutnya adalah menguji build image, menjalankan container, memeriksa health check dan empat halaman dengan data yang diizinkan, lalu menentukan server tujuan serta pengaturan akses.

Konfigurasi ini belum menjadi bukti deployment berhasil. CI tidak melakukan Docker build/run, registry push, atau hosting. Keberhasilan pengujian otomatis harus disebut sebagai keberhasilan CI, sedangkan deployment aplikasi hanya dinyatakan berhasil setelah container atau server tujuan benar-benar diuji.

## 8. Bukti screenshot untuk BAB IV

| No. | Caption yang disarankan | Tampilan yang perlu diambil | Batas klaim |
| --- | --- | --- | --- |
| 1 | Gambar 4.X Struktur Proyek Deployment Aplikasi Norton | Folder baru, workflow, dan dua folder sumber yang masih utuh. | Membuktikan pemisahan file. |
| 2 | Gambar 4.X Konfigurasi GitHub Actions untuk Pengujian Aplikasi | Source workflow: trigger, Python 3.12, working directory, dan tahap tests. | Membuktikan konfigurasi CI. |
| 3 | Gambar 4.X Pengujian Dashboard dengan Data Sintetis | Source fixture dan terminal `12 passed`. | Tidak disebut hasil model Norton. |
| 4 | Gambar 4.X Smoke Test Aplikasi Tanpa Data Privat | Terminal hasil HTTP 200 dan status pembersihan server. | Bukti server lokal sementara. |
| 5 | Gambar 4.X Hasil GitHub Actions Deployment CI | Run dengan commit SHA, event, status, dan seluruh step. | Diambil setelah run selesai; gunakan status nyata. |
| 6 | Gambar 4.X Ringkasan dan Artifact Pengujian Otomatis | Job Summary dan artifact `deployment-ci-reports`. | Melengkapi log run, bukan bukti hosting. |
| 7 | Gambar 4.X Rencana Pengemasan Aplikasi Menggunakan Docker | Dockerfile dan konfigurasi Streamlit. | Konfigurasi saja; build/run belum diverifikasi. |
| 8 | Gambar 4.X Implementasi Deployment Container Norton | Output build, `docker ps`, health, dan aplikasi pada tujuan. | Bukti lanjutan; belum tersedia pada pekerjaan CI ini. |

Screenshot belum dibuat dalam pekerjaan ini. Daftar tersebut merupakan panduan pengambilan bukti asli, bukan klaim bahwa seluruh screenshot sudah tersedia. Tidak digunakan gambar editor atau status Actions buatan.

## 9. Keterbatasan dan keamanan data

Pengujian sintetis memeriksa perilaku aplikasi dan integrasi dependensi, bukan akurasi anomaly detection. Tidak ada label fraud, training baru, evaluasi ulang model, atau hasil bisnis baru yang dihasilkan. Tabel dummy untuk halaman perbandingan juga tidak dinyatakan sebagai hasil eksperimen.

Dataset mentah, database internal, skor per log, model biner, virtual environment, cache, dan kredensial tidak disertakan pada commit ini. Data yang mungkin dibutuhkan saat operasi harus disediakan di luar Git atau di direktori yang diabaikan. Dalam Docker, data diberikan melalui mount read-only pada lingkungan yang berizin. Workflow hanya menjalankan kode dalam folder deployment baru dan tidak memodifikasi dua proyek sumber.

CI belum mencakup deployment otomatis, evaluasi browser end-to-end, beban produksi, autentikasi pengguna, atau akses hosting. AppTest memeriksa empat halaman secara programatis, sedangkan smoke test memeriksa proses HTTP. Keberhasilan keduanya tidak boleh dilaporkan sebagai aplikasi sudah tersedia secara online.

## 10. Referensi implementasi

- [Aplikasi mandiri](../app.py), konfigurasi root artefak dan empat halaman.
- [Fixture sintetis](../tests/conftest.py), fungsi `dashboard_root` dan `dashboard`.
- [Pengujian AppTest](../tests/test_dashboard.py), tujuh fungsi pengujian yang menghasilkan 12 kasus.
- [Smoke test HTTP](../scripts/smoke_test.py), fungsi `main`.
- [Workflow GitHub Actions](../../.github/workflows/deployment-ci.yml).
- [Konfigurasi Streamlit](../.streamlit/config.toml) dan [Dockerfile](../Dockerfile).
- [Dokumentasi resmi pengujian Streamlit](https://docs.streamlit.io/develop/concepts/app-testing).
- [Sintaks workflow GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
- [Job Summary GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#adding-a-job-summary).
- [Rilis checkout](https://github.com/actions/checkout/releases), [setup-python](https://github.com/actions/setup-python/releases), dan [upload-artifact](https://github.com/actions/upload-artifact/releases).

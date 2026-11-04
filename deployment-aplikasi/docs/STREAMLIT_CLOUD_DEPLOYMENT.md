# Deployment Demo Norton ke Streamlit Community Cloud

## 1. Konsep dan strategi deployment

Versi cloud disiapkan untuk memperagakan implementasi aplikasi web pada mata kuliah Deployment Aplikasi. Dashboard menggunakan kembali pola empat halaman aplikasi sebelumnya: Executive Overview, Anomaly Monitoring, Model Comparison, dan Transaction Investigation. Salinan khusus hosting berada pada `deployment-aplikasi/cloud-demo/`, sedangkan aplikasi lokal dan proyek Kecerdasan Bisnis tetap menjadi implementasi terpisah.

Data dibentuk secara terprogram tanpa membaca transaksi perusahaan. Generator menghasilkan 128 log, masing-masing 64 log cobrandgen dan retail, dengan 16 akun serta 64 referensi sintetis. Waktu demonstrasi berada pada Januari 2030 dan seed default adalah 2026. Seluruh skor berlabel IF, ECOD, dan LOF merupakan simulasi; tidak ada pelatihan ketiga algoritma pada aplikasi ini.

Perbedaan ruang lingkup ditampilkan pada aplikasi. Agreement dihitung dari peringkat skor simulasi yang sama, sedangkan eksperimen stabilitas model tidak dijalankan. Nilai tersebut hanya memperagakan fungsi antarmuka dan tidak menggantikan hasil eksperimen Norton.

## 2. Preparation dan konfigurasi aplikasi

Struktur yang diperlukan untuk hosting adalah sebagai berikut. Path ditulis relatif terhadap root repository.

```text
deployment-aplikasi/
├── cloud-demo/
│   ├── app.py
│   ├── demo_data.py
│   ├── requirements.txt
│   ├── .python-version
│   └── .streamlit/config.toml
├── tests/test_cloud_demo.py
├── scripts/smoke_cloud_demo.py
└── docs/STREAMLIT_CLOUD_DEPLOYMENT.md
.github/workflows/deployment-ci.yml
```

Entrypoint adalah [cloud-demo/app.py](../cloud-demo/app.py). Generator [demo_data.py](../cloud-demo/demo_data.py) tersedia di direktori yang sama, sehingga aplikasi tidak bergantung pada dataset, database, atau artefak model lokal. Fungsi pemuatan data memakai cache Streamlit dan memanggil generator secara langsung. Tidak ada pembacaan CSV atau penggunaan `NORTON_DATA_ROOT` pada versi cloud.

Dependensi runtime dipasang dari [requirements.txt khusus cloud](../cloud-demo/requirements.txt): NumPy 2.5.4, pandas 3.1.0, Streamlit 1.66.1, dan Plotly 7.1.0. Pytest berada pada requirements pengujian folder deployment dan tidak diperlukan untuk menjalankan aplikasi publik.

Berkas [.python-version](../cloud-demo/.python-version) mencatat versi 3.12 untuk lingkungan pengembangan. Pemilihan interpreter di Community Cloud tetap dilakukan melalui **Advanced settings → Python version → 3.12** saat membuat deployment. Berkas tersebut tidak dijadikan jaminan bahwa Community Cloud akan memilih versi Python secara otomatis.

Konfigurasi [.streamlit/config.toml](../cloud-demo/.streamlit/config.toml) mengaktifkan mode headless dan menonaktifkan statistik penggunaan. Streamlit 1.66.1 mendukung konfigurasi di direktori entrypoint untuk repository dengan beberapa aplikasi; karena itu konfigurasi ditempatkan di `cloud-demo/.streamlit/`. Konfigurasi root repository tambahan tidak diperlukan untuk versi ini. Penempatan tersebut mengikuti [dokumentasi organisasi file Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization), bagian beberapa aplikasi dalam satu repository.

Sumber: `deployment-aplikasi/cloud-demo/demo_data.py`; fungsi `build_demo_data`; baris 9–24.

```python
def build_demo_data(seed=2026):
    rng = np.random.default_rng(seed)
    models = ("if", "ecod", "lof")
    parts = []
    for channel in ("cobrandgen", "retail"):
        count = 64
        data = pd.DataFrame({
            "log_key": [f"demo-{channel}-log-{i + 1:04d}" for i in range(count)],
            "channel": channel,
            "account_key": [f"demo-{channel}-account-{i % 8 + 1:02d}" for i in range(count)],
            "reference_key": [f"demo-{channel}-reference-{i // 2 + 1:03d}" for i in range(count)],
            "created_at": pd.Timestamp("2030-01-01T08:00:00Z")
                + pd.to_timedelta(np.arange(count) * 360 + rng.integers(0, 60, count), unit="m"),
            "status_snapshot": np.resize(["ACTIVE", "CANCEL", "PENDING", "ACTIVE"], count),
            "amount": rng.integers(20, 501, count),
        })
```

Cuplikan asli tersebut menunjukkan pembentukan identifier, waktu, status, dan nilai sintetis. Awalan `demo-` serta seed eksplisit membantu membedakan data demonstrasi dari data operasional. Identitas dan nilai tidak disalin dari baris transaksi perusahaan.

Sumber: `deployment-aplikasi/cloud-demo/app.py`; fungsi `main`; baris 122–129.

```python
def main():
    st.set_page_config(page_title="Norton — Demo Deployment", layout="wide", initial_sidebar_state="expanded")
    st.title("Norton — Demo Deployment")
    st.info("Demo publik menggunakan data sintetis yang dibuat secara terprogram. Skor berlabel IF, ECOD, dan LOF disimulasikan; bukan hasil pelatihan atau performa aktual model Norton.")
    data = load_data()
    if data.empty:
        st.error("Data demonstrasi belum tersedia. Silakan muat ulang aplikasi.")
        st.stop()
```

Fungsi `main` memberikan keterangan sintetis sebelum interaksi dashboard. Jika generator mengembalikan data kosong, aplikasi menampilkan pesan dan berhenti dengan tertib. Penanganan ini tidak menyembunyikan exception lain; kesalahan startup atau dependensi tetap perlu diperiksa melalui log hosting.

## 3. Testing dengan pytest dan Streamlit AppTest

Pengujian cloud terdapat pada [tests/test_cloud_demo.py](../tests/test_cloud_demo.py). Skenario memeriksa reproduksibilitas seed, rekonsiliasi skor dan peringkat, empat halaman, kombinasi filter, perubahan model dan ambang, filter kosong, konteks akun, serta penanganan data kosong. Pengujian tambahan melarang `pd.read_csv` dan memasang sentinel privat sementara untuk memastikan cloud-demo tidak membaca artefak perusahaan dari environment.

Terdapat 16 kasus cloud-demo setelah parameterisasi, di samping 12 kasus aplikasi deployment sebelumnya. Dengan demikian, target eksekusi seluruh folder tests adalah 28 kasus. Jumlah ini merupakan cakupan tes yang tersedia; status eksekusi aktual dicatat pada bagian hasil pengujian.

Sumber: `deployment-aplikasi/tests/test_cloud_demo.py`; fungsi `test_demo_generator_is_reproducible_for_seed`; baris 38–46.

```python
def test_demo_generator_is_reproducible_for_seed(demo_generator):
    first, first_tables = demo_generator(seed=2026)
    second, second_tables = demo_generator(seed=2026)
    changed, _ = demo_generator(seed=2027)
    pd.testing.assert_frame_equal(first, second)
    assert first_tables.keys() == second_tables.keys()
    for name in first_tables:
        pd.testing.assert_frame_equal(first_tables[name], second_tables[name])
    assert not first.equals(changed)
```

Cuplikan tersebut memastikan seed sama menghasilkan data dan tabel yang sama, sedangkan seed berbeda mengubah hasil simulasi. AppTest melengkapi pemeriksaan data dengan menjalankan interaksi widget dan memeriksa keluaran dashboard. Pengujian ini menilai perilaku aplikasi, bukan akurasi anomaly detection.

Perintah berikut dijalankan dari root repository pada environment Python 3.12 yang aktif:

```bash
python -m pip install -r deployment-aplikasi/requirements.txt
python -m pip install -r deployment-aplikasi/cloud-demo/requirements.txt
python -m pip check
python -m compileall -q deployment-aplikasi/app.py deployment-aplikasi/tests deployment-aplikasi/scripts deployment-aplikasi/cloud-demo
python -m pytest deployment-aplikasi/tests -q --junitxml=deployment-aplikasi/test-results/pytest.xml
python deployment-aplikasi/scripts/smoke_test.py
python deployment-aplikasi/scripts/smoke_cloud_demo.py
```

Smoke test cloud memulai server Streamlit sementara pada port lokal, memeriksa `/_stcore/health` dan `/`, kemudian menghentikan proses dalam blok `finally`. Laporannya ditulis ke `deployment-aplikasi/test-results/cloud-smoke.json`. Smoke test HTTP memeriksa kesiapan proses; hasil rendering dan interaksi empat halaman diperiksa melalui AppTest.

Untuk menjalankan demo secara interaktif setelah instalasi dependensi, gunakan `python -m streamlit run deployment-aplikasi/cloud-demo/app.py`. Penghentian dilakukan dengan `Ctrl+C` pada terminal proses tersebut.

## 4. DevOps dan Continuous Integration

Workflow [Norton Deployment CI](../../.github/workflows/deployment-ci.yml) tetap dipicu oleh push dan pull request menuju `main`. Job menggunakan `ubuntu-latest`, Python 3.12, working directory `deployment-aplikasi`, batas waktu sepuluh menit, dan izin token `contents: read`. Checkout memakai `persist-credentials: false`.

Workflow memasang kedua requirements, memeriksa syntax aplikasi lokal dan cloud-demo, menjalankan seluruh pytest/AppTest, lalu menjalankan dua smoke test. Tahap summary dan upload artifact menggunakan `always()` agar bukti tetap tersedia ketika langkah sebelumnya gagal. Tidak ada `continue-on-error` yang mengubah kegagalan tes menjadi keberhasilan.

Artifact `deployment-ci-reports` menyimpan hasil JUnit, laporan smoke, dan log server sintetis selama 14 hari. CI tidak membaca dataset Norton, menjalankan pipeline Kecerdasan Bisnis, melakukan training, atau mengatur visibilitas repository. Keberhasilan CI menunjukkan pengujian otomatis pada commit tertentu; hosting Community Cloud diverifikasi secara terpisah.

Praktik ini menghubungkan preparation, perubahan kode, pemeriksaan otomatis, dan pencatatan bukti pada satu alur DevOps. Proses deploy Community Cloud tetap merupakan tahap tersendiri setelah commit aplikasi tersedia di branch tujuan.

## 5. Tahapan deployment manual ke Community Cloud

Deployment langsung tidak dilanjutkan karena alat interaksi browser tidak dapat memverifikasi URL Windows yang aktif. Keadaan login Streamlit atau GitHub tidak dapat disimpulkan dari kondisi tersebut. Langkah manual berikut memakai struktur repository aktual dan tidak memerlukan perubahan repository menjadi publik.

1. Masuk ke [Streamlit Community Cloud](https://share.streamlit.io/) menggunakan akun yang mempunyai akses ke repository tujuan. Berikan integrasi akses repository privat bila layanan memintanya dan akun Anda berwenang.
2. Pilih pembuatan aplikasi dari repository GitHub. Isi konfigurasi pada tabel berikut.
3. Buka **Advanced settings**, pilih **Python 3.12**, dan biarkan Secrets kosong. Aplikasi ini tidak memerlukan kredensial, dataset unggahan, atau `NORTON_DATA_ROOT`.
4. Pertahankan repository GitHub dalam keadaan private. Pengaturan akses aplikasi hosting merupakan pengaturan terpisah. Jika demo hendak diakses publik, pemilik akun perlu memilih atau menyetujui pengaturan visibilitas aplikasi tersebut; pekerjaan ini belum mengubah akses aplikasi.
5. Jalankan deploy, tunggu instalasi dependensi dan startup selesai, kemudian periksa log pada pengelolaan aplikasi. Jangan menyatakan deployment berhasil hanya karena build dimulai.
6. Buka aplikasi dan verifikasi banner sintetis, keempat halaman, filter kanal/status/periode, pemilihan skor, ambang, serta konteks investigasi. Periksa bahwa halaman dapat digunakan tanpa exception.
7. Setelah aplikasi berjalan, salin URL yang benar-benar diberikan Community Cloud. Jika akses publik dipilih, periksa URL pada sesi browser tanpa hak akses khusus untuk memastikan pengaturan akses sesuai kebutuhan.

| Pengaturan | Nilai yang digunakan |
| --- | --- |
| Repository | `Madeysszz/Kecerdasan_Bisnis_dan_Deployment_App_MBKMKonversi` |
| Branch | `main` |
| Main file path | `deployment-aplikasi/cloud-demo/app.py` |
| Requirements | `deployment-aplikasi/cloud-demo/requirements.txt`, bersebelahan dengan entrypoint |
| Python pada Advanced settings | `3.12` |
| Secrets | Kosong; tidak dibutuhkan |
| Konfigurasi Streamlit | `deployment-aplikasi/cloud-demo/.streamlit/config.toml` |
| Visibilitas repository | Private; tidak diubah |

Jika repository atau branch belum menampilkan file baru, pastikan commit cloud-demo sudah berada di `main` sebelum melanjutkan. Jika instalasi gagal, baca paket dan versi Python yang disebut log, cocokkan dengan requirements, lalu perbaiki penyebabnya tanpa menghapus pengujian. Jika modul `demo_data` tidak ditemukan, periksa entrypoint dan keberadaan kedua file Python di direktori yang sama. Jika muncul permintaan data privat atau `NORTON_DATA_ROOT`, pastikan entrypoint menunjuk ke `cloud-demo/app.py`, bukan aplikasi lokal.

## 6. Hasil pengujian yang terverifikasi

Catatan tahap dokumentasi ini memisahkan hasil nyata dan pemeriksaan yang belum selesai. Hasil CI sebelumnya berlaku untuk commit sebelumnya dan belum menjadi bukti cloud-demo saat ini.

| Pemeriksaan | Status pada saat dokumentasi disusun |
| --- | --- |
| Validasi syntax source baru | Lulus berdasarkan eksekusi lokal. |
| Validasi workflow dengan actionlint | Lulus berdasarkan eksekusi lokal. |
| Pytest pada environment Windows baru | Terhenti pada pemuatan DLL dependensi sebelum collection; belum menghasilkan hasil 28 tes. |
| Pengujian Python 3.12.3 melalui Ubuntu WSL | Environment dan dependensi sedang disiapkan; hasil belum terverifikasi. |
| Pytest/AppTest cloud-demo dan aplikasi lama | Target 28 kasus; hasil eksekusi terkini belum tersedia. |
| Smoke test cloud-demo untuk perubahan ini | Hasil terkini belum terverifikasi. |
| GitHub Actions pada commit cloud-demo baru | Belum terverifikasi. |
| CI commit sebelumnya | Sukses pada riwayat pekerjaan sebelumnya; tidak dipakai sebagai hasil commit cloud-demo baru. |
| Pelatihan model | Tidak dilakukan. |

Hambatan DLL pada Windows dicatat sebagai kegagalan lingkungan eksekusi, tanpa menganggap tes lulus atau menonaktifkan pemeriksaan. Hasil WSL dan CI perlu diperbarui menggunakan log dan commit yang benar-benar diuji setelah proses selesai.

## 7. Status deployment yang terverifikasi

Aplikasi belum dinyatakan berhasil di-deploy ke Streamlit Community Cloud. Belum ada log hosting, halaman aplikasi online, atau pengujian browser pada URL tujuan yang dapat dijadikan bukti. Penggunaan fallback manual pada bagian sebelumnya sesuai dengan kondisi alat browser yang tidak dapat memverifikasi URL aktif.

Kesiapan struktur file dan konfigurasi merupakan hasil preparation. Status online hanya dapat dicatat setelah aplikasi pada Community Cloud berjalan dan empat halamannya dapat diverifikasi. Tidak ada perubahan visibilitas repository atau aplikasi hosting yang diklaim telah dilakukan.

## 8. URL aplikasi

URL Community Cloud belum tersedia dan belum diverifikasi. Dokumentasi ini tidak mencantumkan alamat contoh sebagai alamat aplikasi yang telah berjalan. Setelah deploy manual berhasil, catat URL sebenarnya, tanggal verifikasi, commit yang digunakan, serta hasil pengujian empat halaman dan akses sesuai visibilitas yang dipilih.

## 9. Keamanan dan keterbatasan data sintetis

Cloud-demo hanya menggunakan data yang dibentuk generator. Dataset mentah, database internal, identifier pelanggan, skor per log perusahaan, dan file model tidak diperlukan oleh entrypoint hosting. Data sintetis tidak disimpan sebagai salinan dataset Norton. Secrets, environment lokal, cache, dan hasil tes sementara tidak perlu dimasukkan ke repository.

Skor simulasi mempunyai skenario sengaja ditinggikan pada satu log per kanal agar contoh pada ambang 0,99 dapat ditampilkan. Konsensus adalah rerata tiga persentil simulasi; antrean tinggi menggunakan kuota satu persen yang dibulatkan ke atas. Pada 64 log per kanal, contoh prioritas menghasilkan satu tinggi, tiga sedang, dan 60 rendah per kanal. Jumlah tersebut tidak menyatakan prevalensi atau temuan fraud.

Tabel agreement dihitung dari skor simulasi, bukan metrik akurasi. Tabel stabilitas kosong karena tidak ada eksperimen stabilitas. Demo juga tidak menyediakan bukti performa model Norton, ketepatan investigasi, generalisasi, keamanan produksi, atau uji beban. Tujuannya adalah membuktikan integrasi antarmuka, pengujian, CI, dan kesiapan hosting dengan data yang aman ditampilkan.

## 10. Bukti screenshot untuk laporan BAB IV

Screenshot berikut perlu diambil dari aplikasi, terminal, Actions, dan Community Cloud yang benar-benar berjalan. Belum ada screenshot baru yang dihasilkan dalam dokumentasi ini. Bukti tahap hosting diambil setelah deploy manual selesai; status atau URL tidak dibuat sebagai gambar pengganti.

| No. | Caption yang disarankan | Tampilan yang diambil | Batas pembuktian |
| --- | --- | --- | --- |
| 1 | Gambar 4.X Struktur Persiapan Aplikasi Streamlit Community Cloud | Folder cloud-demo, app.py, demo_data.py, requirements, .python-version, config, tests, dan workflow. | Struktur implementasi dan pemisahan proyek. |
| 2 | Gambar 4.X Penerapan Data Sintetis pada Dashboard Demo Norton | Executive Overview dengan banner sintetis, jumlah demo, dan filter. | Data demonstrasi; tidak menjadi hasil bisnis Norton. |
| 3 | Gambar 4.X Hasil Pengujian pytest dan Streamlit AppTest | Terminal atau log runner dengan perintah dan hasil aktual seluruh tes. | Catat environment dan status nyata; jangan menuliskan 28 passed sebelum terverifikasi. |
| 4 | Gambar 4.X Continuous Integration Aplikasi Cloud-Demo | Run GitHub Actions dengan commit, branch, langkah tes, dua smoke test, serta artifact. | Bukti CI untuk commit yang sama dengan implementasi. |
| 5 | Gambar 4.X Konfigurasi Deployment Streamlit Community Cloud | Form repository, main, path cloud-demo/app.py, dan Python 3.12 pada Advanced settings. | Konfigurasi deploy; jangan menampilkan token atau Secrets. |
| 6 | Gambar 4.X Log Instalasi dan Startup Streamlit Community Cloud | Log hosting setelah instalasi dan startup, dengan status nyata. | Bukti proses hosting; aplikasi tetap perlu dibuka dan diuji. |
| 7 | Gambar 4.X Akses Dashboard Demo Melalui URL Community Cloud | Browser dengan URL aktual dan halaman Executive Overview setelah verifikasi akses. | Bukti URL bekerja dan visibilitas sesuai pilihan pemilik. |
| 8 | Gambar 4.X Implementasi Empat Halaman Dashboard pada Hosting | Empat tangkapan asli berurutan: Executive Overview, Anomaly Monitoring, Model Comparison, dan Transaction Investigation. | Bukti fungsi halaman dan interaksi pada hosting yang sama. |

Urutan bukti mengikuti preparation, pengujian, CI, konfigurasi deploy, log startup, URL, lalu fungsi aplikasi online. Referensi implementasi utama adalah [entrypoint](../cloud-demo/app.py), [generator sintetis](../cloud-demo/demo_data.py), [pengujian cloud-demo](../tests/test_cloud_demo.py), [smoke test cloud](../scripts/smoke_cloud_demo.py), dan [workflow](../../.github/workflows/deployment-ci.yml). Dokumentasi deployment lokal sebelumnya tersedia pada [DEPLOYMENT_CI.md](DEPLOYMENT_CI.md).

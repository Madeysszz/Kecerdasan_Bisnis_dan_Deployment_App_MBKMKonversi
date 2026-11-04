# Norton — Demo Publik Streamlit

Versi demonstrasi ini menggunakan kembali empat halaman dashboard pada aplikasi deployment lokal. Seluruh log, akun, referensi, waktu, nilai, dan skor dibuat secara sintetis dalam memori oleh `demo_data.py`. Aplikasi tidak membaca dataset, database, skor perusahaan, atau environment variable `NORTON_DATA_ROOT`.

## Isi folder

| File | Kegunaan |
| --- | --- |
| `app.py` | Entrypoint empat halaman beserta filter kanal, status, tanggal, model, dan threshold. |
| `demo_data.py` | Generator deterministik data serta ringkasan simulasi. |
| `requirements.txt` | Dependensi runtime khusus aplikasi publik. |
| `.python-version` | Deklarasi versi pengembangan Python 3.12. |
| `.streamlit/config.toml` | Konfigurasi headless dan penonaktifan statistik penggunaan. |
| `.gitignore` | Mengabaikan environment lokal dan secrets. |

Generator memakai seed 2026 dan membentuk 128 log, 16 akun, serta 64 referensi fiktif pada Januari 2030. Label IF, ECOD, dan LOF menunjukkan skor simulasi untuk memperagakan UI. Tidak ada pelatihan model atau klaim performa aktual Norton. Tabel agreement dihitung dari simulasi; tabel stabilitas kosong karena eksperimen stabilitas tidak dijalankan.

## Menjalankan aplikasi

Gunakan environment Python 3.12 dan jalankan dari root repository, sama seperti working directory Streamlit Community Cloud:

```bash
python -m pip install -r deployment-aplikasi/cloud-demo/requirements.txt
python -m streamlit run deployment-aplikasi/cloud-demo/app.py
```

Buka alamat lokal yang dicetak Streamlit. Tidak diperlukan file dataset, secret, database, atau akses ke folder Kecerdasan Bisnis. Jika generator menghasilkan data kosong, aplikasi menampilkan pesan bahwa data demonstrasi belum tersedia.

## Pengujian

Environment pengujian memerlukan pytest dari requirements aplikasi deployment. Jalankan dari root repository:

```bash
python -m pip install -r deployment-aplikasi/requirements.txt
python -m compileall -q deployment-aplikasi/cloud-demo deployment-aplikasi/tests deployment-aplikasi/scripts
python -m pytest deployment-aplikasi/tests -q
python deployment-aplikasi/scripts/smoke_cloud_demo.py
```

Enam belas kasus khusus cloud-demo melengkapi 12 kasus aplikasi deployment lokal. Pengujian memeriksa empat halaman, filter, perubahan threshold/model, konteks akun, determinisme generator, kondisi data kosong, serta isolasi dari CSV dan environment data privat. Smoke test menjalankan server dari root repository dan menghentikannya setelah pemeriksaan HTTP.

## Pengaturan Streamlit Community Cloud

| Pengaturan | Nilai |
| --- | --- |
| Repository | `Madeysszz/Kecerdasan_Bisnis_dan_Deployment_App_MBKMKonversi` |
| Branch | `main` |
| Main file path | `deployment-aplikasi/cloud-demo/app.py` |
| Python di Advanced settings | `3.12` |
| Dependency file | `deployment-aplikasi/cloud-demo/requirements.txt`, ditemukan di sebelah entrypoint. |
| Secrets | Kosong; demo tidak membutuhkan kredensial. |

Pilih Python 3.12 secara eksplisit pada Advanced settings. `.python-version` mendokumentasikan target pengembangan dan tidak menggantikan pengaturan tersebut. Pada Streamlit 1.66.1, konfigurasi khusus aplikasi dapat ditempatkan di `.streamlit` di sebelah entrypoint, sehingga tidak perlu mengubah konfigurasi aplikasi lain dalam repository.

Repository harus tetap private. Jangan mengubah visibilitas repository untuk melakukan deployment. Aplikasi dari repository private dapat memerlukan pengaturan akses aplikasi tersendiri; pemilik akun perlu menyetujui pengaturan tersebut apabila ingin URL dapat dibuka publik.

Hosting belum diverifikasi dan belum ada URL publik yang dinyatakan berhasil. Pemeriksaan browser otomatis dihentikan karena URL aktif Windows tidak dapat diverifikasi. [Dokumentasi deployment](../docs/STREAMLIT_CLOUD_DEPLOYMENT.md) berisi hasil pengujian, status CI, langkah manual, serta daftar bukti BAB IV.

Rujukan: [organisasi file Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization), [dependensi aplikasi](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies), dan [pengaturan deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

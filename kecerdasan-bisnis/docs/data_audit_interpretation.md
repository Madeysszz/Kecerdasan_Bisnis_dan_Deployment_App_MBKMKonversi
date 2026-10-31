# Interpretasi Audit Data Norton

Dokumen ini menjelaskan batas interpretasi hasil audit tiga berkas CSV yang tersedia.
Angka merujuk pada snapshot sumber, bukan pengukuran langsung terhadap sistem produksi.
Seluruh temuan disajikan secara agregat tanpa data pribadi, kredensial, atau identifier asli.

## 1. Cakupan dan satuan analisis

Dataset terdiri atas log cobrandgen, log retail, dan katalog package.
Log cobrandgen memuat 14.083 baris dan 28 kolom; log retail memuat 178 baris dan 23 kolom.
Katalog package memuat 90 baris dan 16 kolom.
Kolom pertama cobrandgen tidak memiliki nama pada header dan harus diberi nama teknis yang terdokumentasi.

Baris log tidak dapat langsung disamakan dengan transaksi bisnis yang berbeda.
Cobrandgen memiliki 9.763 transaction_id berbeda, sedangkan retail memiliki 51.
Pada cobrandgen terdapat 3.808 kelompok transaksi berulang; pada retail terdapat 6 kelompok.
Dalam setiap kelompok berulang, customer_id, pricing_id, dan price tetap sama.
Seluruh kelompok berulang mempunyai nilai subscription_expired_at yang bervariasi.
Pola ini konsisten dengan kemungkinan pembaruan langganan atau pencatatan riwayat.
Namun, makna tersebut belum dapat dipastikan tanpa dokumentasi proses pembentukan log.

Tidak ditemukan duplikasi seluruh baris pada ketiga berkas.
Pengulangan transaction_id bukan alasan yang cukup untuk menghapus baris atau menandainya sebagai fraud.
Analisis harus membedakan jumlah baris, jumlah transaksi berbeda, dan jumlah pelanggan berbeda.
Agregasi pelanggan harus mempertahankan kanal asal sampai cakupan identifier lintas kanal dikonfirmasi.

## 2. Status dan tanggal langganan

Cobrandgen memuat 9.270 ACTIVE, 4.806 CANCEL, 1 PENDING, dan 6 FAILED.
Retail memuat 16 ACTIVE, 152 CANCEL, dan 10 PENDING.
Angka tersebut adalah jumlah baris menurut status, bukan jumlah pelanggan atau transaksi final.
Sebanyak 3.758 kelompok transaksi cobrandgen dan 5 kelompok retail memuat ACTIVE sekaligus CANCEL.
Karena itu, proporsi CANCEL pada baris tidak dapat langsung disebut tingkat churn pelanggan.
Status akhir transaksi memerlukan aturan pengurutan dan pemilihan kejadian yang disepakati pemilik data.

Tepat 3 baris CANCEL cobrandgen tidak mempunyai subscription_cancel_date.
Seluruh 152 baris CANCEL retail mempunyai tanggal tersebut.
Ketiga kasus cobrandgen merupakan ketidaksesuaian yang perlu ditelusuri, bukan bukti tindakan curang.
Kemungkinan penyebab meliputi aturan pembatalan tertentu, kolom yang belum diperbarui, atau kekurangan ekspor.

Terdapat 4.545 baris cobrandgen dan 127 baris retail dengan start_date sebelum created_at.
Terdapat 1.804 baris cobrandgen dan 1 baris retail dengan cancel_date setelah expired_at.
Kedua pola membutuhkan penjelasan tentang pembaruan, masa tenggang, dan waktu pencatatan log.
Tidak ditemukan updated_at sebelum created_at, expired_at sebelum start_date, atau cancel_date sebelum start_date.
Ketiadaan pelanggaran tersebut hanya menunjukkan konsistensi pada pemeriksaan yang dilakukan.

## 3. Normalisasi waktu dan interval nol

Timestamp memakai urutan hari/bulan/tahun, zona waktu +00, dan presisi yang terlihat sampai detik.
Sebagian besar timestamp mengandung literal `.-1f`, yang tidak sesuai dengan representasi waktu standar.
Literal tersebut dinormalisasi secara terbatas sebelum parsing; nilai sumber tidak ditimpa.
Offset +00 juga harus dikenali secara eksplisit, bukan diganti dengan asumsi zona waktu komputer.
Seluruh timestamp nonkosong berhasil diparse dengan aturan tersebut.
Keberhasilan parsing tidak memastikan bahwa waktu mencerminkan waktu kejadian bisnis yang sesungguhnya.

Jendela created_at cobrandgen adalah 11 Mei sampai 7 Agustus 2026 dalam UTC.
Jendela created_at retail adalah 18 September 2025 sampai 2 Agustus 2026 dalam UTC.
Perbandingan volume kanal harus mempertimbangkan perbedaan jendela observasi ini.
Jika pelaporan memakai WIB, seluruh timestamp harus dikonversi secara konsisten sebelum agregasi harian.

Interval antarbaris dihitung setelah pengurutan created_at untuk setiap pelanggan di masing-masing kanal.
Cobrandgen mempunyai 4.798 pasangan berurutan dan tidak mempunyai interval nol.
Retail mempunyai 137 pasangan berurutan, termasuk 13 pasangan dengan interval nol detik.
Sebanyak 35 pasangan cobrandgen dan 66 pasangan retail mempunyai interval paling lama 60 detik.
Hitungan paling lama 60 detik tersebut mencakup interval nol.
Kesamaan waktu dapat berasal dari pencatatan serentak, proses batch, atau keterbatasan presisi.
Interval nol merupakan kandidat pemeriksaan proses dan tidak dengan sendirinya membuktikan transaksi otomatis.

## 4. Harga dan batas interpretasi pendapatan

Price cobrandgen mempunyai 11 nilai berbeda, dengan rentang 1.000 sampai 500.000.
Price retail mempunyai 8 nilai berbeda, dengan rentang 0 sampai 500.000; 8 baris bernilai nol.
Satuan mata uang, perlakuan pajak, diskon, promosi, dan pengembalian dana belum terdokumentasi.
Harga nol dapat merupakan kondisi sah atau masalah data; pembedaannya memerlukan aturan bisnis.
Harga tinggi juga harus dibandingkan dengan paket dan periode layanan sebelum disebut tidak wajar.

Jumlah nominal price adalah 210.997.000 pada cobrandgen dan 4.293.900 pada retail.
Penjumlahan ini hanya statistik kolom log dan tidak boleh dilabeli sebagai pendapatan terkonfirmasi.
Pengulangan transaksi, pembatalan, status pending, dan ketiadaan bukti pembayaran menghalangi interpretasi tersebut.
Bahkan pemilihan satu baris per transaksi belum menjamin bahwa nilai yang tersisa benar-benar tertagih.
Pengukuran pendapatan membutuhkan sumber pembayaran, aturan pengakuan, serta penanganan refund yang sah.

## 5. Relasi package dan keterbatasan atribut

Package_name, skup, dan pricing pada log cobrandgen seluruhnya kosong.
Log retail tidak menyediakan atribut paket langsung yang cukup untuk menghubungkan katalog.
Pricing_id pada kedua log tidak memiliki kecocokan exact dengan id, name, code, spku, atau norton_name package.
Dengan demikian, tidak ada relasi langsung ke package yang tervalidasi dari berkas yang tersedia.
Hasil tersebut tidak membuktikan bahwa relasi bisnis tidak ada; tabel pricing atau pemetaan kemungkinan diperlukan.
Kesamaan harga, nama yang mendekati, atau durasi tidak boleh digunakan untuk membangun relasi faktual tanpa validasi.

Id dan code package unik, tetapi name, spku, serta norton_name tidak seluruhnya unik.
Sebanyak 11 dari 90 paket memiliki deleted_at; histori paket yang dihapus perlu dipertahankan bila relevan.
Seluruh duration_type bernilai day, tetapi pemetaan durasi ke log belum tersedia.
Aturan harga per paket dan penyimpangan durasi belum dapat dievaluasi secara andal.

Email retail seluruhnya kosong; puid cobrandgen hanya mempunyai satu nilai nonkosong yang berbeda.
Ip tersedia pada 2.000 baris cobrandgen dan 27 baris retail, dengan hanya dua nilai berbeda per kanal.
User_agent yang terisi juga hanya mempunyai satu nilai berbeda per kanal.
Atribut tersebut belum memadai untuk menyimpulkan identitas perangkat, lokasi, atau perilaku jaringan pelanggan.
Kredensial, kode penukaran, dan data pribadi harus dikecualikan dari publikasi hasil dan contoh data terbuka.

## 6. Prioritas konfirmasi kepada pemilik data

1. Tetapkan grain setiap baris dan alasan satu transaction_id dapat menghasilkan beberapa expiry serta status.
2. Jelaskan apakah created_at adalah waktu kejadian, waktu pemrosesan, atau waktu penyisipan log.
3. Dokumentasikan siklus status, aturan pembatalan, masa tenggang, dan tiga CANCEL tanpa tanggal pembatalan.
4. Sediakan kamus data, tabel pricing, serta hubungan pricing ke package yang dapat diuji.
5. Konfirmasikan mata uang, arti price, pembayaran berhasil, refund, promosi, dan kebijakan pengakuan pendapatan.
6. Jelaskan ekspor timestamp `.-1f`, presisi waktu, interval nol, serta cakupan dan retensi data tiap kanal.
7. Pastikan kunci pelanggan, kelengkapan atribut jaringan, dan ketersediaan label hasil investigasi yang sah.

## 7. Insight bisnis yang dapat dipertanggungjawabkan

Snapshot memperlihatkan perbedaan besar volume dan konsentrasi pengulangan antarkanal.
Retail memiliki jauh lebih sedikit transaksi berbeda daripada baris, sehingga perilaku beberapa transaksi sangat dominan.
Pemantauan operasional dapat memprioritaskan konsistensi status, kelengkapan tanggal, dan pencatatan berulang.
Temuan tersebut mendukung perbaikan kualitas data dan penentuan objek investigasi awal.
Dataset ini belum mendukung estimasi kerugian fraud, pendapatan bersih, churn final, atau akurasi deteksi fraud.
Sinyal anomali yang kelak dibentuk harus dibedakan dari label fraud dan dinilai bersama konteks bisnis.

## 8. Status pekerjaan

Dokumen ini mencatat hasil tahap audit yang diselesaikan sebelum implementasi lanjutan.
Pipeline fitur, mart analitik terpisah, tiga model, evaluasi retrospektif, penjelasan statistik, dan dashboard telah ditambahkan setelah audit.
Hasil eksperimen dan status validasinya tersedia pada `../outputs/reports/model_comparison_report.md` serta `../outputs/reports/pipeline_validation.json`.
Konfirmasi semantik tetap diperlukan sebelum hasil snapshot dipakai untuk keputusan operasional atau klaim deteksi fraud.

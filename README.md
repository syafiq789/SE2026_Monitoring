# SE2026 Monitoring

Dashboard Monitoring Sensus Ekonomi 2026 untuk BPS Kabupaten Banyuwangi. Aplikasi menggabungkan frontend Jinja2/Bootstrap dan backend Flask dalam satu project, menggunakan MySQL/MariaDB Laragon sebagai satu-satunya database aplikasi.

## Fitur

- Autentikasi berbasis session dengan role `admin` dan `user`.
- Satu alur upload: Excel XLSX atau CSV data mentah SLS.
- Excel hanya memproses sheet `sls` (case-insensitive dan mengabaikan spasi); tersedia fallback deteksi kolom.
- Normalisasi kolom, penjagaan nol di depan, validasi angka nonnegatif, dan deteksi duplikasi konflik.
- Import transaksional: data monitoring lama tetap aman jika validasi atau insert gagal.
- Monitoring SLS, PCL, PML, dan Kecamatan dari satu sumber data.
- Dashboard delapan metrik dan tujuh grafik dengan data dari API internal.
- Filter bertingkat Kecamatan → Desa/PML/PCL dan PML → PCL.
- Export CSV/Excel mengikuti filter, khusus Admin.
- Riwayat upload, manajemen user, dan API Bearer Token yang disimpan sebagai hash.
- **[Fitur TA] Peta Spasial (WebGIS Banyuwangi):** Visualisasi sebaran progres lapangan 25 kecamatan menggunakan Leaflet.js dengan klasifikasi warna status (Optimal, Moderat, Perlu Akselerasi) dan filter interaktif.
- **[Fitur TA] Koordinasi Lapangan & Pengingat WhatsApp:** Generator pesan pengingat otomatis berbasis capaian *real-time* untuk PCL/PML via WhatsApp 1-Klik serta filter petugas prioritas percepatan (<50%).
- **[Fitur TA] Audit Trail & Activity Log:** Pencatatan otomatis riwayat aksi sensitif (login, upload sensus, ekspor data, dan tindak lanjut petugas) untuk tata kelola keamanan sistem.
- Error handler ramah pengguna dan log aplikasi berotasi.
- Tampilan responsif dengan tema coklat, oranye, emas, cream, dan putih.

## Rumus utama

```text
Sudah Upload = min(max(total - OPEN - DRAFT, 0), total)
Belum Upload = max(total - Sudah Upload, 0)
Progress = Sudah Upload / Total × 100
```

Progress agregat selalu dihitung sebagai `SUM(processed) / SUM(total)`, bukan rata-rata persentase baris.

## Persiapan Laragon

1. Jalankan Laragon dan klik **Start All**.
2. Import [database.sql](database.sql) melalui HeidiSQL atau phpMyAdmin. Script membuat database `se2026_monitoring`, seluruh tabel, index, foreign key, dan lima view.
3. Salin `.env.example` menjadi `.env`. Ganti `SECRET_KEY=replace-with-a-random-secret` dengan kunci acak unik (minimal 32 byte; misalnya hasil `python -c "import secrets; print(secrets.token_hex(32))"`). Aplikasi menolak kunci kosong atau kunci demo lama. Nilai environment deployment mengungguli `.env`. Konfigurasi database default sesuai MySQL Laragon:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=se2026_monitoring
DB_USER=root
DB_PASSWORD=
```

Jika akun root Anda memiliki password, isi `DB_PASSWORD`. Jangan commit file `.env`.

## Instalasi dan menjalankan aplikasi

Buka terminal di folder project:

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python seed_users.py
python app.py
```

`requirements.txt` memakai Pandas 2.2.3 secara otomatis pada Python 3.13 (seperti runtime Laragon terbaru) karena versi itu menyediakan dukungan/wheel Python 3.13; Python 3.12 ke bawah tetap memakai versi 2.2.2 sesuai spesifikasi.

Buka `http://127.0.0.1:5000`.

## Konfigurasi deployment dan perubahan keamanan

- Registrasi publik hanya membuat role `user`. Set `ALLOW_PUBLIC_REGISTER=False` untuk menutup registrasi; admin baru dibuat oleh admin melalui `/admin/register`.
- Database adalah otoritas akun. Cookie lama tidak akan membuat ulang akun yang sudah dihapus. Login ulang diperlukan setelah perubahan kunci sesi. Jika kunci demo pernah digunakan, rotasi `SECRET_KEY` untuk membatalkan cookie lama dan tinjau akun admin yang sudah terdaftar.
- Aplikasi tidak lagi membuat tabel/akun default pada setiap request. Inisialisasi skema melalui `database.sql` atau `python seed_users.py` secara eksplisit sebelum menjalankan server. `seed_users.py` menyediakan akun demo untuk pengembangan; nonaktifkan/ganti akun tersebut sebelum operasional.
- **Vercel memerlukan `DATABASE_URL` menuju database MySQL/MariaDB eksternal persisten dan `SECRET_KEY` unik.** Fallback SQLite `/tmp` dan penyalinan ulang database bawaan dihapus. Deploy tanpa konfigurasi tersebut akan ditolak. Cadangkan dan migrasikan data lama ke database persisten sebelum rollout; file `/tmp` bukan penyimpanan lintas instance. File upload/ekspor pada Vercel tetap sementara.
- CSV kosong setelah normalisasi ditolak. Semua penghitung wajib bilangan bulat nonnegatif hingga 2147483647; input salah tidak diubah diam-diam menjadi nol. Perbedaan penugasan untuk kunci SLS geografis yang sama adalah konflik, bukan record tambahan.
- Setiap artifact ekspor memiliki nama unik. Nilai identitas berawalan formula diberi awalan apostrof agar tetap berupa teks di CSV/XLSX.

## Akun awal

| Role | Username | Email | Password |
|---|---|---|---|
| Admin | `admin` | `admin@se2026.local` | `admin123` |
| User | `user` | `user@se2026.local` | `user123` |

Untuk penggunaan operasional, buat akun Admin baru dengan password kuat lalu nonaktifkan akun awal. Password disimpan menggunakan hash Werkzeug; password asli tidak pernah disimpan di database.

## Format file upload

Admin membuka **Upload Data SLS** dan memilih satu file `.xlsx` atau `.csv` (maksimum 32 MB).

Untuk Excel, sistem:

1. Mencari sheet bernama `sls` tanpa membedakan besar-kecil huruf dan spasi tepi.
2. Jika tidak ditemukan, mencari sheet dengan seluruh kolom wajib.
3. Membaca hanya sheet yang terpilih dan mengabaikan sheet pivot/formula lainnya.

Kolom wajib setelah mapping:

```text
kec_code, kec_name, desa_code, desa_name, subsls_code, subsls_name,
PCL, PML, total, OPEN, DRAFT
```

Kolom `prov`, `kab`, `kec_code`, `desa_code`, dan `subsls_code` dibaca sebagai string. Panjangnya dinormalisasi berturut-turut menjadi 2, 2, 3, 3, dan 6 digit tanpa mengubah nilai kosong menjadi nol.

Jika kunci `prov-kab-kec_code-desa_code-subsls_code` sama:

- baris identik dilewati dan dicatat;
- nilai berbeda menghentikan import sebelum data lama dihapus.

## Hak akses

| Fitur | Admin | User |
|---|:---:|:---:|
| Dashboard dan seluruh monitoring | Ya | Ya |
| Filter, pencarian, sorting, pagination | Ya | Ya |
| Upload dan export | Ya | Tidak |
| Riwayat upload | Ya | Tidak |
| Manajemen pengguna/Admin | Ya | Tidak |
| Pembuatan dan pencabutan API token | Ya | Tidak |

Hak akses selalu diperiksa backend; menyembunyikan tombol pada UI bukan satu-satunya pengamanan.

## API

API internal memerlukan session login:

```text
GET /api/dashboard-data
GET /api/chart-data
GET /api/filter-data?kec_code=010&pml_id=1
```

Admin dapat membuat Bearer Token melalui menu **API Token** (`/admin/api-tokens`), dengan nama dan masa berlaku 1–365 hari, serta mencabutnya dari halaman yang sama. Token terikat pada admin aktif yang membuatnya; token kedaluwarsa, dicabut, atau milik pengguna nonaktif/turun role ditolak. Nilai token hanya ditampilkan sekali.

```text
GET /api/v1/dashboard
GET /api/v1/monitoring/sls?page=1&per_page=100
Authorization: Bearer se2026_xxxxx
```

Respons API SLS berisi `data`, `total`, `page` dan `per_page`. API Bearer tidak menerima cookie login sebagai pengganti token.

Parameter filter API SLS: `kec_code`, `desa_code`, `pml_id`, `pcl_id`, `status`, `progress_min`, dan `progress_max`. `per_page` dibatasi maksimum 1.000.

## Pengujian

```powershell
python -m pytest -q
```

Suite regresi juga menguji penolakan admin publik, flag registrasi, revokasi akun/token, impor kosong/angka invalid/duplikasi penugasan, rollback, formula ekspor, artifact unik, dan endpoint API Bearer.

Pengujian mencakup empat kasus rumus wajib, kondisi `OPEN + DRAFT > total`, mapping nama kolom, akses role, pemilihan sheet `sls`, pengabaian kolom kosong, penjagaan nol di depan, CSV, kolom wajib, dan duplikasi konflik.

## Struktur project

```text
SE2026_Monitoring/
├── app.py, config.py, extensions.py, seed_users.py
├── database.sql, requirements.txt, .env.example
├── models/       # model ORM users, wilayah, SLS, riwayat, token
├── routes/       # auth, dashboard, monitoring, upload, export, user, API
├── services/     # import, agregasi, export, autentikasi, token
├── utils/        # decorator, mapping, validasi, perhitungan, helper
├── templates/    # seluruh halaman Jinja2
├── static/       # CSS dan JavaScript
├── uploads/      # file sumber tersimpan (tidak masuk Git)
├── exports/      # hasil export (tidak masuk Git)
└── tests/        # pengujian otomatis
```

## Pemecahan masalah

- **Tidak dapat terhubung ke database:** pastikan Laragon/MySQL aktif, database sudah diimport, dan nilai `.env` benar.
- **Sheet SLS tidak ditemukan:** pastikan nama sheet `sls` atau semua kolom wajib tersedia pada salah satu sheet.
- **Kolom wajib tidak ditemukan:** pesan aplikasi menampilkan kolom yang terbaca dan yang hilang.
- **Import gagal:** data lama di-rollback. Detail teknis tersimpan di `se2026.log` tanpa menampilkan kredensial database pada halaman.
- **Asset CDN tidak tampil:** aplikasi tetap berfungsi, tetapi Bootstrap, Font Awesome, DataTables, dan Chart.js membutuhkan koneksi internet pada browser untuk tampilan/interaksi lengkap.

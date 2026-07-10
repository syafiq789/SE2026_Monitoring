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
3. Salin `.env.example` menjadi `.env`. Konfigurasi default sudah sesuai MySQL Laragon:

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

Admin dapat membuat Bearer Token melalui menu **API Token**. Nilai token hanya ditampilkan sekali.

```text
GET /api/v1/dashboard
GET /api/v1/monitoring/sls?page=1&per_page=100
Authorization: Bearer se2026_xxxxx
```

Parameter filter API SLS: `kec_code`, `desa_code`, `pml_id`, `pcl_id`, `status`, `progress_min`, dan `progress_max`. `per_page` dibatasi maksimum 1.000.

## Pengujian

```powershell
python -m pytest -q
```

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

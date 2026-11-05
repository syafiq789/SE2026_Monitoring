"""
Paket Modul Services (Business Logic Layer)
Sistem Informasi Monitoring SE2026 BPS Kabupaten Banyuwangi

Menampung seluruh logika bisnis, pemrosesan komputasi berat, dan manipulasi data:
- upload_service: Parsing cepat Excel/CSV (Calamine) & import database transaksional
- monitoring_service: Agregasi 8 KPI, rekapitulasi PML, PCL, dan 25 Kecamatan
- followup_service: Deteksi petugas prioritas (<50%) & generator pesan WhatsApp
- gis_service: Pengolahan koordinat spasial 25 kecamatan & metrik lapangan
- export_service: Generator file laporan terformat .xlsx (OpenPyXL) dan .csv
- activity_service: Perekaman audit trail ke tabel activity_logs
- auth_service: Manajemen sesi autentikasi dan pemulihan snapshot serverless
"""

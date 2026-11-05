"""
Paket Modul Routes (Controller)
Sistem Informasi Monitoring SE2026 BPS Kabupaten Banyuwangi

Menampung seluruh Flask Blueprint untuk memisahkan penanganan URL per fitur:
- auth_routes: Autentikasi sesi (Login, Register, Logout)
- dashboard_routes: Halaman ringkasan eksekutif (8 KPI & Grafik)
- monitoring_routes: Pemantauan 4 level (SLS, PCL, PML, Kecamatan)
- gis_routes: Visualisasi geospasial WebGIS 25 Kecamatan
- followup_routes: Koordinasi lapangan & pengingat WhatsApp
- upload_routes: Pipeline unggah data SLS Excel/CSV
- export_routes: Pusat unduh laporan CSV & Excel terformat
- user_routes: Manajemen pengguna & hak akses role Admin
- log_routes: Audit trail riwayat aktivitas keamanan sistem
- api_routes: Endpoint REST API JSON internal & eksternal
"""

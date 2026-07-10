CREATE DATABASE IF NOT EXISTS se2026_monitoring
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE se2026_monitoring;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP VIEW IF EXISTS view_monitoring_kecamatan;
DROP VIEW IF EXISTS view_monitoring_pml;
DROP VIEW IF EXISTS view_monitoring_pcl;
DROP VIEW IF EXISTS view_monitoring_sls;
DROP VIEW IF EXISTS view_dashboard_summary;

CREATE TABLE IF NOT EXISTS users (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nama_lengkap VARCHAR(150) NOT NULL,
  username VARCHAR(80) NOT NULL,
  email VARCHAR(150) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin','user') NOT NULL DEFAULT 'user',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_username (username),
  UNIQUE KEY uq_users_email (email),
  KEY idx_users_role_active (role, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kecamatan (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  prov_code VARCHAR(2) NOT NULL,
  kab_code VARCHAR(2) NOT NULL,
  kec_code VARCHAR(3) NOT NULL,
  kec_name VARCHAR(150) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_kecamatan_wilayah (prov_code, kab_code, kec_code),
  KEY idx_kecamatan_code (kec_code),
  KEY idx_kecamatan_name (kec_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pml (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  kecamatan_id INT UNSIGNED NOT NULL,
  email_pml VARCHAR(150) NOT NULL DEFAULT '',
  nama_pml VARCHAR(150) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_pml_wilayah_identitas (kecamatan_id, email_pml, nama_pml),
  KEY idx_pml_kecamatan (kecamatan_id),
  KEY idx_pml_nama (nama_pml),
  CONSTRAINT fk_pml_kecamatan FOREIGN KEY (kecamatan_id) REFERENCES kecamatan(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pcl (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  kecamatan_id INT UNSIGNED NOT NULL,
  pml_id INT UNSIGNED NOT NULL,
  email_pcl VARCHAR(150) NOT NULL DEFAULT '',
  username_pcl VARCHAR(100) NOT NULL DEFAULT '',
  nama_pcl VARCHAR(150) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_pcl_wilayah_identitas (kecamatan_id, pml_id, email_pcl, username_pcl, nama_pcl),
  KEY idx_pcl_kecamatan (kecamatan_id),
  KEY idx_pcl_pml (pml_id),
  KEY idx_pcl_nama (nama_pcl),
  CONSTRAINT fk_pcl_kecamatan FOREIGN KEY (kecamatan_id) REFERENCES kecamatan(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_pcl_pml FOREIGN KEY (pml_id) REFERENCES pml(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sls (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  kecamatan_id INT UNSIGNED NOT NULL,
  pml_id INT UNSIGNED NOT NULL,
  pcl_id INT UNSIGNED NOT NULL,
  prov_code VARCHAR(2) NOT NULL,
  kab_code VARCHAR(2) NOT NULL,
  desa_code VARCHAR(3) NOT NULL,
  desa_name VARCHAR(150) NOT NULL,
  subsls_code VARCHAR(6) NOT NULL,
  subsls_name VARCHAR(200) NOT NULL,
  sls_key VARCHAR(50) NOT NULL,
  approved_by_pengawas INT UNSIGNED NOT NULL DEFAULT 0,
  completed_by_admin_kabupaten INT UNSIGNED NOT NULL DEFAULT 0,
  draft_count INT UNSIGNED NOT NULL DEFAULT 0,
  edited_by_admin_kabupaten INT UNSIGNED NOT NULL DEFAULT 0,
  edited_by_pengawas INT UNSIGNED NOT NULL DEFAULT 0,
  open_count INT UNSIGNED NOT NULL DEFAULT 0,
  rejected_by_admin_kabupaten INT UNSIGNED NOT NULL DEFAULT 0,
  rejected_by_pengawas INT UNSIGNED NOT NULL DEFAULT 0,
  revoked_by_admin_kabupaten INT UNSIGNED NOT NULL DEFAULT 0,
  revoked_by_pengawas INT UNSIGNED NOT NULL DEFAULT 0,
  submitted_by_pencacah INT UNSIGNED NOT NULL DEFAULT 0,
  submitted_respondent INT UNSIGNED NOT NULL DEFAULT 0,
  total_target INT UNSIGNED NOT NULL DEFAULT 0,
  processed_count INT UNSIGNED NOT NULL DEFAULT 0,
  remaining_count INT UNSIGNED NOT NULL DEFAULT 0,
  progress DECIMAL(6,2) UNSIGNED NOT NULL DEFAULT 0.00,
  progress_status VARCHAR(30) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_sls_key (sls_key),
  KEY idx_sls_kecamatan (kecamatan_id),
  KEY idx_sls_pml (pml_id),
  KEY idx_sls_pcl (pcl_id),
  KEY idx_sls_desa (desa_code),
  KEY idx_sls_subsls (subsls_code),
  KEY idx_sls_progress_status (progress_status),
  CONSTRAINT fk_sls_kecamatan FOREIGN KEY (kecamatan_id) REFERENCES kecamatan(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_sls_pml FOREIGN KEY (pml_id) REFERENCES pml(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_sls_pcl FOREIGN KEY (pcl_id) REFERENCES pcl(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT chk_sls_progress CHECK (progress >= 0 AND progress <= 100),
  CONSTRAINT chk_sls_counts CHECK (processed_count <= total_target AND remaining_count <= total_target)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS upload_history (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id INT UNSIGNED NULL,
  original_filename VARCHAR(255) NOT NULL,
  stored_filename VARCHAR(255) NOT NULL,
  processed_sheet VARCHAR(100) NULL,
  file_type VARCHAR(10) NOT NULL,
  file_size BIGINT UNSIGNED NOT NULL DEFAULT 0,
  source_rows INT UNSIGNED NOT NULL DEFAULT 0,
  imported_rows INT UNSIGNED NOT NULL DEFAULT 0,
  skipped_rows INT UNSIGNED NOT NULL DEFAULT 0,
  duplicate_rows INT UNSIGNED NOT NULL DEFAULT 0,
  warning_count INT UNSIGNED NOT NULL DEFAULT 0,
  total_kecamatan INT UNSIGNED NOT NULL DEFAULT 0,
  total_pml INT UNSIGNED NOT NULL DEFAULT 0,
  total_pcl INT UNSIGNED NOT NULL DEFAULT 0,
  total_sls INT UNSIGNED NOT NULL DEFAULT 0,
  total_target BIGINT UNSIGNED NOT NULL DEFAULT 0,
  total_processed BIGINT UNSIGNED NOT NULL DEFAULT 0,
  total_remaining BIGINT UNSIGNED NOT NULL DEFAULT 0,
  progress DECIMAL(6,2) UNSIGNED NOT NULL DEFAULT 0.00,
  status ENUM('processing','success','failed') NOT NULL,
  message TEXT NULL,
  uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_upload_user (user_id),
  KEY idx_upload_status_time (status, uploaded_at),
  CONSTRAINT fk_upload_user FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS api_tokens (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id INT UNSIGNED NOT NULL,
  name VARCHAR(100) NOT NULL,
  token_prefix VARCHAR(16) NOT NULL,
  token_hash CHAR(64) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  expires_at DATETIME NULL,
  last_used_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_api_token_hash (token_hash),
  KEY idx_api_token_user (user_id),
  KEY idx_api_token_prefix_active (token_prefix, is_active),
  CONSTRAINT fk_api_token_user FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

CREATE OR REPLACE VIEW view_dashboard_summary AS
SELECT
  COUNT(DISTINCT k.id) AS total_kecamatan,
  COUNT(DISTINCT pm.id) AS total_pml,
  COUNT(DISTINCT pc.id) AS total_pcl,
  COUNT(DISTINCT s.id) AS total_sls,
  COALESCE(SUM(s.total_target), 0) AS total_target,
  COALESCE(SUM(s.processed_count), 0) AS total_processed,
  COALESCE(SUM(s.remaining_count), 0) AS total_remaining,
  COALESCE(ROUND(SUM(s.processed_count) / NULLIF(SUM(s.total_target), 0) * 100, 2), 0) AS progress
FROM sls s
LEFT JOIN kecamatan k ON k.id = s.kecamatan_id
LEFT JOIN pml pm ON pm.id = s.pml_id
LEFT JOIN pcl pc ON pc.id = s.pcl_id;

CREATE OR REPLACE VIEW view_monitoring_sls AS
SELECT s.id, k.kec_code, k.kec_name, s.desa_code, s.desa_name, s.subsls_code, s.subsls_name,
       pm.nama_pml, pc.nama_pcl, s.total_target, s.open_count, s.draft_count,
       s.processed_count, s.remaining_count, s.approved_by_pengawas, s.progress, s.progress_status,
       s.completed_by_admin_kabupaten, s.edited_by_admin_kabupaten, s.edited_by_pengawas,
       s.rejected_by_admin_kabupaten, s.rejected_by_pengawas,
       s.revoked_by_admin_kabupaten, s.revoked_by_pengawas,
       s.submitted_by_pencacah, s.submitted_respondent
FROM sls s
JOIN kecamatan k ON k.id = s.kecamatan_id
JOIN pml pm ON pm.id = s.pml_id
JOIN pcl pc ON pc.id = s.pcl_id;

CREATE OR REPLACE VIEW view_monitoring_pcl AS
SELECT k.kec_code, k.kec_name, pm.nama_pml, pc.id AS pcl_id, pc.nama_pcl,
       COUNT(DISTINCT s.id) AS jumlah_sls,
       SUM(s.total_target) AS total_target, SUM(s.open_count) AS open_count,
       SUM(s.draft_count) AS draft_count, SUM(s.processed_count) AS processed_count,
       SUM(s.remaining_count) AS remaining_count, SUM(s.approved_by_pengawas) AS approved_count,
       COALESCE(ROUND(SUM(s.processed_count) / NULLIF(SUM(s.total_target), 0) * 100, 2), 0) AS progress
FROM sls s JOIN kecamatan k ON k.id=s.kecamatan_id JOIN pml pm ON pm.id=s.pml_id JOIN pcl pc ON pc.id=s.pcl_id
GROUP BY k.kec_code, k.kec_name, pm.nama_pml, pc.id, pc.nama_pcl;

CREATE OR REPLACE VIEW view_monitoring_pml AS
SELECT k.kec_code, k.kec_name, pm.id AS pml_id, pm.nama_pml,
       COUNT(DISTINCT pc.id) AS jumlah_pcl, COUNT(DISTINCT s.id) AS jumlah_sls,
       SUM(s.total_target) AS total_target, SUM(s.open_count) AS open_count,
       SUM(s.draft_count) AS draft_count, SUM(s.processed_count) AS processed_count,
       SUM(s.remaining_count) AS remaining_count, SUM(s.approved_by_pengawas) AS approved_count,
       COALESCE(ROUND(SUM(s.processed_count) / NULLIF(SUM(s.total_target), 0) * 100, 2), 0) AS progress
FROM sls s JOIN kecamatan k ON k.id=s.kecamatan_id JOIN pml pm ON pm.id=s.pml_id JOIN pcl pc ON pc.id=s.pcl_id
GROUP BY k.kec_code, k.kec_name, pm.id, pm.nama_pml;

CREATE OR REPLACE VIEW view_monitoring_kecamatan AS
SELECT k.id AS kecamatan_id, k.kec_code, k.kec_name,
       COUNT(DISTINCT pm.id) AS jumlah_pml, COUNT(DISTINCT pc.id) AS jumlah_pcl,
       COUNT(DISTINCT s.id) AS jumlah_sls, SUM(s.total_target) AS total_target,
       SUM(s.open_count) AS open_count, SUM(s.draft_count) AS draft_count,
       SUM(s.processed_count) AS processed_count, SUM(s.remaining_count) AS remaining_count,
       SUM(s.approved_by_pengawas) AS approved_count,
       COALESCE(ROUND(SUM(s.processed_count) / NULLIF(SUM(s.total_target), 0) * 100, 2), 0) AS progress
FROM sls s JOIN kecamatan k ON k.id=s.kecamatan_id JOIN pml pm ON pm.id=s.pml_id JOIN pcl pc ON pc.id=s.pcl_id
GROUP BY k.id, k.kec_code, k.kec_name;


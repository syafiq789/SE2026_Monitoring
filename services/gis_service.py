from services.monitoring_service import get_kecamatan_rows

# Titik koordinat sentroid 25 Kecamatan di Kabupaten Banyuwangi (Jawa Timur)
BANYUWANGI_KECAMATAN_COORDINATES = {
    "010": {"name": "Pesanggaran", "lat": -8.5714, "lng": 114.0518},
    "020": {"name": "Bangorejo", "lat": -8.4901, "lng": 114.1678},
    "030": {"name": "Purwoharjo", "lat": -8.5029, "lng": 114.2259},
    "040": {"name": "Tegaldlimo", "lat": -8.5441, "lng": 114.3415},
    "050": {"name": "Muncar", "lat": -8.4385, "lng": 114.3328},
    "060": {"name": "Cluring", "lat": -8.4357, "lng": 114.2274},
    "070": {"name": "Gambiran", "lat": -8.4124, "lng": 114.1481},
    "080": {"name": "Srono", "lat": -8.3975, "lng": 114.2762},
    "090": {"name": "Genteng", "lat": -8.3654, "lng": 114.1539},
    "100": {"name": "Glenmore", "lat": -8.3061, "lng": 114.0531},
    "110": {"name": "Kalibaru", "lat": -8.2917, "lng": 113.9872},
    "120": {"name": "Singojuruh", "lat": -8.3045, "lng": 114.2391},
    "130": {"name": "Rogojampi", "lat": -8.3072, "lng": 114.2965},
    "140": {"name": "Kabat", "lat": -8.2796, "lng": 114.3312},
    "150": {"name": "Glagah", "lat": -8.2091, "lng": 114.3168},
    "160": {"name": "Banyuwangi", "lat": -8.2192, "lng": 114.3692},
    "170": {"name": "Giri", "lat": -8.1887, "lng": 114.3541},
    "180": {"name": "Wongsorejo", "lat": -7.9543, "lng": 114.4021},
    "190": {"name": "Songgon", "lat": -8.2435, "lng": 114.1863},
    "200": {"name": "Sempu", "lat": -8.3371, "lng": 114.1648},
    "210": {"name": "Kalipuro", "lat": -8.1367, "lng": 114.3857},
    "220": {"name": "Siliragung", "lat": -8.5524, "lng": 114.1352},
    "230": {"name": "Tegalsari", "lat": -8.4412, "lng": 114.1287},
    "240": {"name": "Licin", "lat": -8.2185, "lng": 114.2571},
    "250": {"name": "Blimbingsari", "lat": -8.3241, "lng": 114.3582},
}


def _get_status_color(progress: float):
    if progress >= 80.0:
        return "#25835b"  # Hijau (Selesai/Hampir Selesai)
    if progress >= 50.0:
        return "#dba63a"  # Emas/Kuning (On Track)
    return "#bf3f32"  # Merah (Perlu Perhatian Khusus)


def get_gis_monitoring_data():
    """
    Menggabungkan data monitoring kecamatan dari database dengan koordinat geospasial
    untuk dirender di Peta Interaktif Leaflet.js.
    """
    kec_rows = get_kecamatan_rows()

    gis_features = []
    total_target = 0
    total_processed = 0
    high_count = 0
    medium_count = 0
    low_count = 0

    # Petakan hasil baris monitoring kecamatan
    db_by_code = {row["kec_code"]: row for row in kec_rows}

    for code, coords in BANYUWANGI_KECAMATAN_COORDINATES.items():
        db_data = db_by_code.get(code)
        if db_data:
            target = db_data.get("total_target", 0)
            processed = db_data.get("processed_count", 0)
            remaining = db_data.get("remaining_count", 0)
            open_c = db_data.get("open_count", 0)
            draft_c = db_data.get("draft_count", 0)
            sls_c = db_data.get("jumlah_sls", 0)
            pml_c = db_data.get("jumlah_pml", 0)
            pcl_c = db_data.get("jumlah_pcl", 0)
            progress = float(db_data.get("progress", 0.0))
            name = db_data.get("kec_name", coords["name"])
        else:
            target = 0
            processed = 0
            remaining = 0
            open_c = 0
            draft_c = 0
            sls_c = 0
            pml_c = 0
            pcl_c = 0
            progress = 0.0
            name = coords["name"]

        total_target += target
        total_processed += processed

        if progress >= 80.0:
            high_count += 1
            status_label = "Optimal (≥80%)"
        elif progress >= 50.0:
            medium_count += 1
            status_label = "Moderat (50-79%)"
        else:
            low_count += 1
            status_label = "Perlu Percepatan (<50%)"

        gis_features.append({
            "kec_code": code,
            "kec_name": name,
            "lat": coords["lat"],
            "lng": coords["lng"],
            "jumlah_sls": sls_c,
            "jumlah_pml": pml_c,
            "jumlah_pcl": pcl_c,
            "total_target": target,
            "processed_count": processed,
            "remaining_count": remaining,
            "open_count": open_c,
            "draft_count": draft_c,
            "progress": progress,
            "status_label": status_label,
            "color": _get_status_color(progress),
        })

    # Urutkan berdasarkan progress untuk leaderboard spasial
    sorted_features = sorted(gis_features, key=lambda x: x["progress"], reverse=True)
    overall_progress = round((total_processed / total_target * 100), 2) if total_target > 0 else 0.0

    return {
        "features": gis_features,
        "leaderboard_top": sorted_features[:5],
        "leaderboard_bottom": sorted_features[-5:][::-1],
        "summary": {
            "total_kecamatan": len(BANYUWANGI_KECAMATAN_COORDINATES),
            "total_target": total_target,
            "total_processed": total_processed,
            "overall_progress": overall_progress,
            "high_progress_count": high_count,
            "medium_progress_count": medium_count,
            "low_progress_count": low_count,
            "center": [-8.2192, 114.3692],
            "zoom": 10,
        },
    }

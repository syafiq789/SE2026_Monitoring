from urllib.parse import quote

from sqlalchemy import distinct, func

from extensions import db
from models.monitoring import Kecamatan, PCL, PML, SLS
from services.monitoring_service import filter_options
from utils.calculations import aggregate_progress


def classify_priority(progress: float, draft_count: int = 0, pending_approval: int = 0) -> dict:
    """
    Menentukan tingkat prioritas tindak lanjut petugas berdasarkan progres dan antrean dokumen.
    """
    if progress <= 0:
        return {
            "key": "belum_mulai",
            "label": "Belum Mulai (0%)",
            "badge": "danger",
            "priority_order": 1,
        }
    if progress < 50:
        return {
            "key": "kritis",
            "label": "Perlu Akselerasi (<50%)",
            "badge": "danger",
            "priority_order": 2,
        }
    if progress < 80 or draft_count > 0 or pending_approval > 0:
        return {
            "key": "moderat",
            "label": "Perlu Dorongan (50-79%)",
            "badge": "warning",
            "priority_order": 3,
        }
    if progress < 100:
        return {
            "key": "hampir_selesai",
            "label": "Hampir Selesai (80-99%)",
            "badge": "info",
            "priority_order": 4,
        }
    return {
        "key": "selesai",
        "label": "Selesai (100%)",
        "badge": "success",
        "priority_order": 5,
    }


def build_pcl_reminder_message(row: dict) -> str:
    """
    Membuat teks pesan pengingat otomatis (WhatsApp / Email) untuk petugas PCL.
    """
    nama_pcl = row.get("nama_pcl", "Rekan PCL")
    kec_name = row.get("kec_name", "-")
    nama_pml = row.get("nama_pml", "-")
    jumlah_sls = row.get("jumlah_sls", 0)
    total_target = row.get("total_target", 0)
    processed_count = row.get("processed_count", 0)
    remaining_count = row.get("remaining_count", 0)
    open_count = row.get("open_count", 0)
    draft_count = row.get("draft_count", 0)
    rejected_count = row.get("rejected_count", 0)
    progress = float(row.get("progress") or 0.0)

    catatan_tambahan = []
    if draft_count > 0:
        catatan_tambahan.append(f"terdapat *{draft_count} dokumen masih berstatus DRAFT* yang perlu segera disubmit")
    if open_count > 0:
        catatan_tambahan.append(f"*{open_count} target masih berstatus OPEN*")
    if rejected_count > 0:
        catatan_tambahan.append(f"*{rejected_count} dokumen REJECTED* yang perlu diperbaiki")

    detail_catatan = (
        "Catatan khusus: " + ", serta ".join(catatan_tambahan) + ".\n\n"
        if catatan_tambahan
        else ""
    )

    return (
        f"Halo Yth. Rekan PCL SE2026 *{nama_pcl}*\n"
        f"Wilayah: Kec. *{kec_name}* (PML: {nama_pml})\n\n"
        f"Berdasarkan pantauan Dashboard Monitoring Sensus Ekonomi 2026 BPS Kabupaten Banyuwangi, "
        f"berikut ringkasan progres pencacahan Anda saat ini:\n"
        f"• Jumlah Wilayah: *{jumlah_sls} SLS*\n"
        f"• Total Target: *{total_target} usaha*\n"
        f"• Sudah Diunggah: *{processed_count} usaha*\n"
        f"• Belum Diunggah: *{remaining_count} usaha* (OPEN: {open_count} | DRAFT: {draft_count})\n"
        f"• Capaian Progres: *{progress:.2f}%*\n\n"
        f"{detail_catatan}"
        f"Mohon segera melakukan sinkronisasi/unggah hasil pencacahan terbaru dan berkoordinasi "
        f"dengan PML (*{nama_pml}*) apabila terdapat kendala di lapangan.\n\n"
        f"Terima kasih atas dedikasi dan kerja samanya.\n"
        f"— *Tim Monitoring SE2026 BPS Kabupaten Banyuwangi*"
    )


def build_pml_reminder_message(row: dict) -> str:
    """
    Membuat teks pesan pengingat otomatis (WhatsApp / Email) untuk pengawas PML.
    """
    nama_pml = row.get("nama_pml", "Rekan PML")
    kec_name = row.get("kec_name", "-")
    jumlah_pcl = row.get("jumlah_pcl", 0)
    jumlah_sls = row.get("jumlah_sls", 0)
    total_target = row.get("total_target", 0)
    processed_count = row.get("processed_count", 0)
    remaining_count = row.get("remaining_count", 0)
    approved_count = row.get("approved_count", 0)
    pending_approval = max(processed_count - approved_count, 0)
    draft_count = row.get("draft_count", 0)
    progress = float(row.get("progress") or 0.0)

    return (
        f"Halo Yth. Rekan PML SE2026 *{nama_pml}*\n"
        f"Wilayah Pengawasan: Kec. *{kec_name}*\n\n"
        f"Berdasarkan pantauan Dashboard Monitoring Sensus Ekonomi 2026 BPS Kabupaten Banyuwangi, "
        f"berikut rekapitulasi progres tim Anda:\n"
        f"• Cakupan Tim: *{jumlah_pcl} PCL* ({jumlah_sls} SLS)\n"
        f"• Total Target: *{total_target} usaha*\n"
        f"• Sudah Diunggah PCL: *{processed_count} usaha* ({progress:.2f}%)\n"
        f"• Belum Diunggah PCL: *{remaining_count} usaha* (DRAFT tertahan: {draft_count})\n"
        f"• Sudah Approved PML: *{approved_count} usaha*\n"
        f"• Menunggu Pemeriksaan/Approval PML: *{pending_approval} usaha*\n\n"
        f"Mohon melakukan pendampingan pada PCL yang progresnya masih di bawah target "
        f"serta mempercepat proses pemeriksaan/approval dokumen yang telah disubmit.\n\n"
        f"Terima kasih atas kerja samanya.\n"
        f"— *Tim Monitoring SE2026 BPS Kabupaten Banyuwangi*"
    )


def build_kecamatan_broadcast_message(kec_label: str, pcl_rows: list) -> str:
    """
    Membuat pesan rekap broadcast untuk ditempelkan ke Grup WhatsApp Kecamatan/Koordinasi.
    """
    total_pcl = len(pcl_rows)
    if total_pcl == 0:
        return "Belum ada data petugas untuk ditampilkan pada filter ini."

    total_target = sum(r.get("total_target", 0) for r in pcl_rows)
    total_processed = sum(r.get("processed_count", 0) for r in pcl_rows)
    total_remaining = sum(r.get("remaining_count", 0) for r in pcl_rows)
    total_draft = sum(r.get("draft_count", 0) for r in pcl_rows)
    overall_progress = aggregate_progress(total_target, total_processed)

    prioritas_list = [r for r in pcl_rows if float(r.get("progress") or 0) < 100]
    prioritas_list.sort(key=lambda item: (float(item.get("progress") or 0), -int(item.get("remaining_count") or 0)))

    lines = [
        f"📢 *REKAP MONITORING SE2026 - {kec_label.upper()}*",
        f"BPS Kabupaten Banyuwangi",
        "",
        f"📊 *Ringkasan Capaian Wilayah:*",
        f"• Jumlah PCL Terpantau: *{total_pcl} petugas*",
        f"• Total Target: *{total_target} usaha*",
        f"• Sudah Upload: *{total_processed} usaha* (*{overall_progress:.2f}%*)",
        f"• Sisa Belum Upload: *{total_remaining} usaha* (Tertahan di DRAFT: *{total_draft}*)",
        "",
    ]

    if prioritas_list:
        lines.append("⚠️ *Daftar Petugas Prioritas Tindak Lanjut (Top 10):*")
        for idx, item in enumerate(prioritas_list[:10], start=1):
            lines.append(
                f"{idx}. *{item['nama_pcl']}* (PML: {item['nama_pml']}) — "
                f"*{item['progress']:.2f}%* | Sisa: {item['remaining_count']} (Draft: {item['draft_count']})"
            )
        lines.append("")

    lines.append(
        "Mohon kepada rekan-rekan PCL yang masih memiliki sisa target maupun dokumen berstatus *DRAFT* "
        "untuk segera melakukan sinkronisasi/submit, serta rekan PML untuk mendampingi dan melakukan approval. Terima kasih. 🙏"
    )
    return "\n".join(lines)


def get_followup_data(filters: dict = None) -> dict:
    """
    Mengambil data lengkap tindak lanjut untuk PCL dan PML beserta pesan pengingat otomatis.
    """
    filters = filters or {}
    kec_code = str(filters.get("kec_code") or "").strip()
    pml_id = filters.get("pml_id")
    role_type = str(filters.get("role_type") or "pcl").strip().lower()
    if role_type not in {"pcl", "pml"}:
        role_type = "pcl"
    priority_filter = str(filters.get("priority") or "").strip().lower()
    search_query = str(filters.get("q") or "").strip().lower()

    # Query agregasi PCL lengkap dengan email & dokumen ditolak
    pcl_query = (
        db.session.query(
            PCL.id.label("id"),
            PCL.pml_id.label("pml_id"),
            Kecamatan.kec_code,
            Kecamatan.kec_name,
            PML.nama_pml,
            PML.email_pml,
            PCL.nama_pcl,
            PCL.email_pcl,
            PCL.username_pcl,
            func.count(distinct(SLS.id)).label("jumlah_sls"),
            func.coalesce(func.sum(SLS.total_target), 0).label("total_target"),
            func.coalesce(func.sum(SLS.open_count), 0).label("open_count"),
            func.coalesce(func.sum(SLS.draft_count), 0).label("draft_count"),
            func.coalesce(func.sum(SLS.processed_count), 0).label("processed_count"),
            func.coalesce(func.sum(SLS.remaining_count), 0).label("remaining_count"),
            func.coalesce(func.sum(SLS.approved_by_pengawas), 0).label("approved_count"),
            func.coalesce(
                func.sum(
                    func.coalesce(SLS.rejected_by_pengawas, 0)
                    + func.coalesce(SLS.rejected_by_admin_kabupaten, 0)
                ),
                0,
            ).label("rejected_count"),
        )
        .select_from(SLS)
        .join(Kecamatan, SLS.kecamatan_id == Kecamatan.id)
        .join(PML, SLS.pml_id == PML.id)
        .join(PCL, SLS.pcl_id == PCL.id)
    )

    if kec_code:
        pcl_query = pcl_query.filter(Kecamatan.kec_code == kec_code)
    if pml_id:
        pcl_query = pcl_query.filter(SLS.pml_id == pml_id)

    pcl_query = pcl_query.group_by(
        PCL.id,
        PCL.pml_id,
        Kecamatan.kec_code,
        Kecamatan.kec_name,
        PML.nama_pml,
        PML.email_pml,
        PCL.nama_pcl,
        PCL.email_pcl,
        PCL.username_pcl,
    )

    pcl_rows = []
    for raw in pcl_query.all():
        item = dict(raw._mapping)
        for k in (
            "jumlah_sls",
            "total_target",
            "open_count",
            "draft_count",
            "processed_count",
            "remaining_count",
            "approved_count",
            "rejected_count",
        ):
            item[k] = int(item.get(k) or 0)
        item["pending_approval"] = max(item["processed_count"] - item["approved_count"], 0)
        item["progress"] = aggregate_progress(item["total_target"], item["processed_count"])
        item["priority"] = classify_priority(
            item["progress"],
            draft_count=item["draft_count"],
            pending_approval=item["pending_approval"],
        )
        item["reminder_message"] = build_pcl_reminder_message(item)
        item["wa_url"] = f"https://wa.me/?text={quote(item['reminder_message'])}"
        subject = quote(f"[SE2026 BPS Banyuwangi] Pengingat Progres Pencacahan - {item['nama_pcl']}")
        body = quote(item["reminder_message"])
        item["mailto_url"] = f"mailto:{item.get('email_pcl') or ''}?subject={subject}&body={body}"
        pcl_rows.append(item)

    # Query agregasi PML
    pml_query = (
        db.session.query(
            PML.id.label("id"),
            Kecamatan.kec_code,
            Kecamatan.kec_name,
            PML.nama_pml,
            PML.email_pml,
            func.count(distinct(PCL.id)).label("jumlah_pcl"),
            func.count(distinct(SLS.id)).label("jumlah_sls"),
            func.coalesce(func.sum(SLS.total_target), 0).label("total_target"),
            func.coalesce(func.sum(SLS.open_count), 0).label("open_count"),
            func.coalesce(func.sum(SLS.draft_count), 0).label("draft_count"),
            func.coalesce(func.sum(SLS.processed_count), 0).label("processed_count"),
            func.coalesce(func.sum(SLS.remaining_count), 0).label("remaining_count"),
            func.coalesce(func.sum(SLS.approved_by_pengawas), 0).label("approved_count"),
            func.coalesce(
                func.sum(
                    func.coalesce(SLS.rejected_by_pengawas, 0)
                    + func.coalesce(SLS.rejected_by_admin_kabupaten, 0)
                ),
                0,
            ).label("rejected_count"),
        )
        .select_from(SLS)
        .join(Kecamatan, SLS.kecamatan_id == Kecamatan.id)
        .join(PML, SLS.pml_id == PML.id)
        .join(PCL, SLS.pcl_id == PCL.id)
    )

    if kec_code:
        pml_query = pml_query.filter(Kecamatan.kec_code == kec_code)
    if pml_id:
        pml_query = pml_query.filter(SLS.pml_id == pml_id)

    pml_query = pml_query.group_by(
        PML.id,
        Kecamatan.kec_code,
        Kecamatan.kec_name,
        PML.nama_pml,
        PML.email_pml,
    )

    pml_rows = []
    for raw in pml_query.all():
        item = dict(raw._mapping)
        for k in (
            "jumlah_pcl",
            "jumlah_sls",
            "total_target",
            "open_count",
            "draft_count",
            "processed_count",
            "remaining_count",
            "approved_count",
            "rejected_count",
        ):
            item[k] = int(item.get(k) or 0)
        item["pending_approval"] = max(item["processed_count"] - item["approved_count"], 0)
        item["progress"] = aggregate_progress(item["total_target"], item["processed_count"])
        item["priority"] = classify_priority(
            item["progress"],
            draft_count=item["draft_count"],
            pending_approval=item["pending_approval"],
        )
        item["reminder_message"] = build_pml_reminder_message(item)
        item["wa_url"] = f"https://wa.me/?text={quote(item['reminder_message'])}"
        subject = quote(f"[SE2026 BPS Banyuwangi] Evaluasi & Pengingat Pengawasan PML - {item['nama_pml']}")
        body = quote(item["reminder_message"])
        item["mailto_url"] = f"mailto:{item.get('email_pml') or ''}?subject={subject}&body={body}"
        pml_rows.append(item)

    # Ringkasan metrik tindak lanjut
    summary = {
        "pcl_belum_mulai": sum(1 for r in pcl_rows if r["progress"] <= 0),
        "pcl_kritis": sum(1 for r in pcl_rows if 0 < r["progress"] < 50),
        "total_draft_tertahan": sum(r["draft_count"] for r in pcl_rows),
        "total_pending_approval": sum(r["pending_approval"] for r in pml_rows),
        "total_pcl": len(pcl_rows),
        "total_pml": len(pml_rows),
    }

    active_rows = pcl_rows if role_type == "pcl" else pml_rows

    if priority_filter:
        if priority_filter == "draft":
            active_rows = [r for r in active_rows if r["draft_count"] > 0]
        elif priority_filter == "pending_approval":
            active_rows = [r for r in active_rows if r["pending_approval"] > 0]
        else:
            active_rows = [r for r in active_rows if r["priority"]["key"] == priority_filter]

    if search_query:
        active_rows = [
            r
            for r in active_rows
            if search_query in str(r.get("nama_pcl") or "").lower()
            or search_query in str(r.get("nama_pml") or "").lower()
            or search_query in str(r.get("kec_name") or "").lower()
            or search_query in str(r.get("email_pcl") or "").lower()
            or search_query in str(r.get("email_pml") or "").lower()
        ]

    # Urutkan dari progres terendah & beban sisa tertinggi agar yang paling butuh perhatian di atas
    active_rows.sort(
        key=lambda item: (
            item["priority"]["priority_order"],
            float(item.get("progress") or 0),
            -int(item.get("remaining_count") or 0),
        )
    )

    options = filter_options(kec_code, pml_id)
    kec_label = "Seluruh Kecamatan"
    if kec_code:
        for k in options["kecamatan"]:
            if k["code"] == kec_code:
                kec_label = f"Kecamatan {k['name']} ({k['code']})"
                break

    broadcast_text = build_kecamatan_broadcast_message(kec_label, pcl_rows)

    return {
        "rows": active_rows,
        "summary": summary,
        "filter_options": options,
        "filters": {
            "kec_code": kec_code,
            "pml_id": pml_id,
            "role_type": role_type,
            "priority": priority_filter,
            "q": filters.get("q") or "",
        },
        "kec_label": kec_label,
        "broadcast_text": broadcast_text,
        "broadcast_wa_url": f"https://wa.me/?text={quote(broadcast_text)}",
    }


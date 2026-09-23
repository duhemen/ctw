"""Inisialisasi database CTW + seed data lengkap Fase 2A."""
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.database import SessionLocal, init_db, engine, Base
from core import models


def seed_regions(db):
    """Seed hierarki wilayah: 3 provinsi, kabupaten/kota, kecamatan, kelurahan."""
    data = [
        # Jawa Barat
        ("32", "Jawa Barat", "provinsi", None, -6.9, 107.6),
        ("32.71", "Kota Bogor", "kabupaten", "32", -6.595, 106.816),
        ("32.71.01", "Bogor Tengah", "kecamatan", "32.71", -6.59, 106.80),
        ("32.71.01.1001", "Pabaton", "kelurahan", "32.71.01", -6.59, 106.80),
        ("32.71.01.1002", "Cibogor", "kelurahan", "32.71.01", -6.59, 106.80),
        ("32.71.02", "Bogor Utara", "kecamatan", "32.71", -6.57, 106.80),
        ("32.71.02.1001", "Cibuluh", "kelurahan", "32.71.02", -6.57, 106.80),
        ("32.73", "Kota Bandung", "kabupaten", "32", -6.917, 107.619),
        ("32.73.02", "Sumur Bandung", "kecamatan", "32.73", -6.917, 107.619),
        ("32.73.02.1001", "Braga", "kelurahan", "32.73.02", -6.917, 107.619),
        ("32.01", "Kabupaten Bogor", "kabupaten", "32", -6.48, 106.85),
        ("32.01.01", "Cibinong", "kecamatan", "32.01", -6.48, 106.85),
        ("32.01.01.1001", "Cibinong", "kelurahan", "32.01.01", -6.48, 106.85),
        ("32.01.01.1002", "Cirimekar", "kelurahan", "32.01.01", -6.48, 106.85),
        ("32.01.03", "Citeureup", "kecamatan", "32.01", -6.48, 106.87),
        ("32.01.03.1001", "Puspanegara", "kelurahan", "32.01.03", -6.48, 106.87),

        # Kalimantan Tengah
        ("62", "Kalimantan Tengah", "provinsi", None, -1.68, 113.38),
        ("62.03", "Kabupaten Kapuas", "kabupaten", "62", -3.01, 114.39),
        ("62.03.01", "Selat", "kecamatan", "62.03", -3.01, 114.39),
        ("62.03.01.1001", "Selat Dalam", "kelurahan", "62.03.01", -3.01, 114.39),
        ("62.71", "Kota Palangka Raya", "kabupaten", "62", -2.21, 113.91),
        ("62.71.01", "Pahandut", "kecamatan", "62.71", -2.21, 113.91),
        ("62.71.01.1001", "Pahandut", "kelurahan", "62.71.01", -2.21, 113.91),

        # Riau
        ("14", "Riau", "provinsi", None, 0.5, 101.45),
        ("14.05", "Kabupaten Pelalawan", "kabupaten", "14", 0.4, 101.95),
        ("14.05.02", "Pangkalan Kerinci", "kecamatan", "14.05", 0.4, 101.95),
        ("14.05.02.1001", "Pangkalan Kerinci Kota", "kelurahan", "14.05.02", 0.4, 101.95),
    ]
    for code, name, level, parent, lat, lng in data:
        if not db.query(models.Region).filter_by(code=code).first():
            db.add(models.Region(code=code, name=name, level=level,
                                 parent_code=parent, latitude=lat, longitude=lng))


def seed_providers(db):
    data = [
        dict(name="PT Karya Nusantara", npwp="01.234.567.8-901.000",
             siujk_number="SIUJK/001/2020", classification="Besar",
             qualification="B1", address="Jl. Sudirman No. 45, Bandung",
             region_code="32.73", contact_person="Budi Santoso",
             phone="022-1234567", email="info@karyanusantara.co.id"),
        dict(name="PT Bangun Persada", npwp="02.345.678.9-012.000",
             siujk_number="SIUJK/002/2019", classification="Menengah",
             qualification="M1", address="Jl. Merdeka No. 12, Palangka Raya",
             region_code="62.71", contact_person="Siti Aminah",
             phone="0536-223344", email="contact@bangunpersada.co.id"),
        dict(name="PT Tani Makmur", npwp="03.456.789.0-123.000",
             siujk_number="SIUJK/003/2021", classification="Menengah",
             qualification="M1", address="Jl. Trans Kalimantan Km 5, Kapuas",
             region_code="62.03", contact_person="Ahmad Yusuf",
             phone="0513-556677", email="admin@tanimakmur.co.id"),
        dict(name="PT Rekayasa Utama", npwp="04.567.890.1-234.000",
             siujk_number="SIUJK/004/2018", classification="Besar",
             qualification="B1", address="Jl. Gatot Subroto No. 8, Jakarta",
             region_code="32", contact_person="Rina Wati",
             phone="021-99887766", email="office@rekayasa-utama.co.id"),
    ]
    providers = []
    for d in data:
        if not db.query(models.Provider).filter_by(name=d["name"]).first():
            p = models.Provider(**d)
            db.add(p)
            providers.append(p)
    db.flush()
    return providers


def seed_projects(db, providers):
    by_name = {p.name: p for p in providers}
    data = [
        dict(
            name="Jalan Nasional Trans-Sumatra",
            description="Pembangunan jalan lintas Sumatera segmen Riau-Jambi, termasuk perkerasan dan drainase.",
            region_code="14.05.02.1001", address="Km 45, Pangkalan Kerinci, Pelalawan",
            latitude=0.4, longitude=101.95, status="Berjalan",
            contract_number="SPK/001/PPK-SUM/2024", contract_value=850000.0,
            contract_start=date(2024, 1, 15), contract_end=date(2027, 1, 14),
            duration_days=1095, is_multi_year=True,
            funding_source="APBN", fiscal_year=2024, risk_level="Tinggi",
            progress_physical=42.5, progress_financial=38.0, time_work_percent=60.0,
            progress_updated_at=datetime.utcnow(),
            provider_id=by_name["PT Karya Nusantara"].id,
            supervisor_id=by_name["PT Rekayasa Utama"].id,
        ),
        dict(
            name="Jembatan Barito",
            description="Rehabilitasi jembatan penghubung Kalimantan Selatan-Tengah.",
            region_code="62.03.01.1001", address="DAS Barito, Kapuas",
            latitude=-3.01, longitude=114.39, status="Selesai",
            contract_number="SPK/002/PPK-KALTENG/2024", contract_value=420000.0,
            contract_start=date(2024, 3, 1), contract_end=date(2025, 2, 28),
            duration_days=365, is_multi_year=False,
            funding_source="APBD", fiscal_year=2024, risk_level="Rendah",
            progress_physical=100.0, progress_financial=100.0, time_work_percent=100.0,
            progress_updated_at=datetime.utcnow(),
            provider_id=by_name["PT Bangun Persada"].id,
        ),
        dict(
            name="Irigasi Gambut Kalimantan",
            description="Sistem irigasi lahan gambut 500 ha di Kapuas.",
            region_code="62.03.01.1001", address="Blok C, Kapuas",
            latitude=-3.02, longitude=114.40, status="Berjalan",
            contract_number="SPK/003/PPK-KALTENG/2024", contract_value=610000.0,
            contract_start=date(2024, 6, 1), contract_end=date(2026, 5, 31),
            duration_days=730, is_multi_year=True,
            funding_source="DAK", fiscal_year=2024, risk_level="Sedang",
            progress_physical=35.0, progress_financial=32.0, time_work_percent=40.0,
            progress_updated_at=datetime.utcnow(),
            provider_id=by_name["PT Tani Makmur"].id,
        ),
        dict(
            name="Revitalisasi Pasar Cibinong",
            description="Revitalisasi pasar rakyat menjadi pasar modern.",
            region_code="32.01.01.1001", address="Jl. Raya Cibinong No. 1, Bogor",
            latitude=-6.48, longitude=106.85, status="Berjalan",
            contract_number="SPK/004/PPK-JABAR/2024", contract_value=95000.0,
            contract_start=date(2024, 4, 1), contract_end=date(2025, 3, 31),
            duration_days=365, is_multi_year=False,
            funding_source="APBD", fiscal_year=2024, risk_level="Sedang",
            progress_physical=58.0, progress_financial=55.0, time_work_percent=65.0,
            progress_updated_at=datetime.utcnow(),
            provider_id=by_name["PT Karya Nusantara"].id,
        ),
    ]

    projects = []
    for d in data:
        if not db.query(models.Project).filter_by(name=d["name"]).first():
            p = models.Project(**d)
            db.add(p)
            projects.append(p)
    db.flush()
    return projects


def seed_schedules(db, projects):
    """Kurva S sederhana untuk setiap proyek."""
    templates = {
        "Jalan Nasional Trans-Sumatra": [(25, 22), (50, 45), (75, 68), (100, 42.5)],
        "Jembatan Barito": [(30, 32), (60, 65), (85, 88), (100, 100)],
        "Irigasi Gambut Kalimantan": [(20, 18), (45, 40), (70, 60), (90, 35)],
        "Revitalisasi Pasar Cibinong": [(35, 38), (65, 60), (85, 58), (100, 0)],
    }
    periods = ["Q1", "Q2", "Q3", "Q4"]
    for p in projects:
        if not p.schedules and p.name in templates:
            for period, (plan, actual) in zip(periods, templates[p.name]):
                db.add(models.ProjectSchedule(project_id=p.id, period=period,
                                              planned_percent=plan, actual_percent=actual))


def seed_milestones(db, projects):
    templates = {
        "Jalan Nasional Trans-Sumatra": [
            ("Persiapan & Mobilitas", date(2024, 1, 15), date(2024, 2, 10), "Done", 100, ""),
            ("Land Clearing", date(2024, 3, 1), date(2024, 5, 20), "Done", 100, ""),
            ("Perkerasan Lapis Pondasi", date(2024, 6, 1), date(2024, 9, 30), "In Progress", 45, ""),
            ("Perkerasan Permukaan", date(2024, 10, 1), date(2024, 12, 31), "Pending", 0, ""),
            ("Finishing & Serah Terima", date(2027, 1, 1), None, "Pending", 0, ""),
        ],
        "Jembatan Barito": [
            ("Survey & Desain", date(2024, 3, 1), date(2024, 3, 20), "Done", 100, ""),
            ("Perbaikan Struktur Bawah", date(2024, 4, 1), date(2024, 8, 31), "Done", 100, ""),
            ("Perbaikan Struktur Atas", date(2024, 9, 1), date(2025, 1, 15), "Done", 100, ""),
            ("Serah Terima", date(2025, 2, 28), date(2025, 2, 28), "Done", 100, ""),
        ],
        "Irigasi Gambut Kalimantan": [
            ("Survey & Desain", date(2024, 6, 1), date(2024, 7, 15), "Done", 100, ""),
            ("Pembuatan Saluran Primer", date(2024, 7, 16), date(2024, 11, 30), "In Progress", 60, ""),
            ("Pembuatan Saluran Sekunder", date(2024, 12, 1), date(2025, 4, 30), "Pending", 0, ""),
            ("Pintu Air & Bangunan Pelengkap", date(2025, 5, 1), date(2025, 10, 31), "Pending", 0, ""),
            ("Uji Fungsi & Serah Terima", date(2026, 5, 31), None, "Pending", 0, ""),
        ],
        "Revitalisasi Pasar Cibinong": [
            ("Pembongkaran Bangunan Lama", date(2024, 4, 1), date(2024, 5, 15), "Done", 100, ""),
            ("Pondasi & Struktur", date(2024, 5, 16), date(2024, 9, 30), "In Progress", 70, ""),
            ("Arsitektur & MEP", date(2024, 10, 1), date(2025, 1, 31), "Pending", 0, ""),
            ("Finishing & Serah Terima", date(2025, 3, 31), None, "Pending", 0, ""),
        ],
    }
    for p in projects:
        if not p.milestones and p.name in templates:
            for name, tgt, act, status, prog, notes in templates[p.name]:
                db.add(models.ProjectMilestone(project_id=p.id, name=name,
                                               target_date=tgt, actual_date=act,
                                               status=status, progress=prog, notes=notes))


def seed_photos(db, projects):
    """Gunakan placeholder image dari placehold.co agar render tanpa file lokal."""
    def ph(text, color="3b82f6"):
        return f"https://placehold.co/600x400/{color}/ffffff?text={text.replace(' ', '+')}"

    templates = {
        "Jalan Nasional Trans-Sumatra": [
            ("Kondisi awal lokasi", "awal", "1e40af"),
            ("Land clearing selesai", "progress", "3b82f6"),
            ("Lapis pondasi 45%", "progress", "60a5fa"),
            ("Pekerjaan drainase", "progress", "93c5fd"),
        ],
        "Jembatan Barito": [
            ("Kondisi sebelum rehab", "awal", "1e40af"),
            ("Perbaikan pilar", "progress", "3b82f6"),
            ("Serah terima", "serah_terima", "22c55e"),
        ],
        "Irigasi Gambut Kalimantan": [
            ("Kondisi lahan gambut", "awal", "1e40af"),
            ("Saluran primer 60%", "progress", "3b82f6"),
            ("Pintu air sementara", "progress", "93c5fd"),
        ],
        "Revitalisasi Pasar Cibinong": [
            ("Pasar lama sebelum dibongkar", "awal", "1e40af"),
            ("Pondasi selesai", "progress", "3b82f6"),
            ("Struktur lantai 2", "progress", "60a5fa"),
            ("Tampak depan progres", "progress", "93c5fd"),
        ],
    }
    for p in projects:
        if not p.photos and p.name in templates:
            for caption, cat, color in templates[p.name]:
                db.add(models.ProjectPhoto(project_id=p.id,
                                           file_path=ph(caption, color),
                                           caption=caption, category=cat))


def seed_blacklist(db, providers):
    by_name = {p.name: p for p in providers}
    if db.query(models.Blacklist).count() == 0:
        db.add(models.Blacklist(
            provider_id=by_name["PT Rekayasa Utama"].id,
            reason="Terbukti melakukan wanprestasi pada 2 paket pekerjaan tahun 2023 dengan "
                   "keterlambatan melebihi 60 hari tanpa alasan force majeure.",
            category="Wanprestasi",
            regulation_ref="Perpres 16/2018 Pasal 78 ayat (1) huruf a",
            decision_by="LPSE Provinsi Jawa Barat",
            decision_number="SK/BL/2024/0123",
            start_date=date(2024, 8, 1),
            end_date=date(2026, 7, 31),
            status="Aktif",
            document_url="https://example.com/sk-blacklist-0123.pdf",
        ))


def main():
    print("=== Inisialisasi database CTW Fase 2A ===")
    Base.metadata.drop_all(bind=engine)  # reset bersih
    init_db()
    print("[OK] Tabel dibuat ulang.")

    db = SessionLocal()
    try:
        print("Seeding regions...")
        seed_regions(db)
        db.flush()

        print("Seeding providers...")
        providers = seed_providers(db)

        print("Seeding projects...")
        projects = seed_projects(db, providers)

        print("Seeding schedules...")
        seed_schedules(db, projects)

        print("Seeding milestones...")
        seed_milestones(db, projects)

        print("Seeding photos...")
        seed_photos(db, projects)

        print("Seeding blacklist...")
        seed_blacklist(db, providers)

        db.commit()
        print("[OK] Semua seed data tersimpan.")

        print(f"   Regions   : {db.query(models.Region).count()}")
        print(f"   Providers : {db.query(models.Provider).count()}")
        print(f"   Projects  : {db.query(models.Project).count()}")
        print(f"   Schedules : {db.query(models.ProjectSchedule).count()}")
        print(f"   Milestones: {db.query(models.ProjectMilestone).count()}")
        print(f"   Photos    : {db.query(models.ProjectPhoto).count()}")
        print(f"   Blacklist : {db.query(models.Blacklist).count()}")
    finally:
        db.close()

    print("\nLangkah berikutnya:")
    print("  uvicorn server.main:app --reload --port 8000")


if __name__ == "__main__":
    main()

"""
Fix pasca-impor wilayah:
1. Inspeksi 143 orphan - lihat di level apa & kenapa
2. Update region_code proyek seed CTW ke format spatianomics (tanpa titik)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from core.database import SessionLocal
from core.models import Region, Project

SEP = "=" * 70


def section(t):
    print(f"\n{SEP}\n  {t}\n{SEP}")


def inspect_orphan(db):
    section("1. INSPEKSI 143 ORPHAN")
    rows = db.execute(text("""
        SELECT level, COUNT(*) AS cnt
        FROM regions
        WHERE parent_code IS NOT NULL
          AND parent_code NOT IN (SELECT code FROM regions)
        GROUP BY level
    """)).fetchall()
    print("\n  Orphan per level:")
    for lvl, cnt in rows:
        print(f"    {str(lvl):15s} : {cnt:>4}")

    print("\n  Sample 10 orphan (kode, nama, level, parent_kode):")
    samples = db.execute(text("""
        SELECT code, name, level, parent_code
        FROM regions
        WHERE parent_code IS NOT NULL
          AND parent_code NOT IN (SELECT code FROM regions)
        LIMIT 10
    """)).fetchall()
    for c, n, l, p in samples:
        print(f"    • {c:15s} | {n[:40]:40s} | {l:10s} | parent={p}")


def fix_project_regions(db):
    section("2. UPDATE REGION_CODE PROYEK SEED")

    # Mapping manual: nama proyek -> kata kunci wilayah yang dicari
    # Format: (nama_proyek, provinsi, kabupaten/kota, kecamatan, kelurahan/desa)
    targets = [
        {
            "project": "Jalan Nasional Trans-Sumatra",
            "prov": "Riau",
            "kab": "Pelalawan",
            "kec": "Pangkalan Kerinci",
            "kel": None,  # pilih level kecamatan
            "use_level": "kecamatan",
        },
        {
            "project": "Jembatan Barito",
            "prov": "Kalimantan Tengah",
            "kab": "Kapuas",
            "kec": "Selat",
            "kel": None,
            "use_level": "kecamatan",
        },
        {
            "project": "Irigasi Gambut Kalimantan",
            "prov": "Kalimantan Tengah",
            "kab": "Kapuas",
            "kec": "Selat",
            "kel": None,
            "use_level": "kecamatan",
        },
        {
            "project": "Revitalisasi Pasar Cibinong",
            "prov": "Jawa Barat",
            "kab": "Bogor",  # Kabupaten Bogor (bukan Kota)
            "kec": "Cibinong",
            "kel": None,
            "use_level": "kecamatan",
        },
    ]

    for t in targets:
        proj = db.query(Project).filter(Project.name == t["project"]).first()
        if not proj:
            print(f"  [!] Proyek tidak ditemukan: {t['project']}")
            continue

        # Cari kode wilayah berdasarkan hierarki nama
        prov = db.query(Region).filter(
            Region.level == "provinsi",
            Region.name.ilike(f"%{t['prov']}%"),
        ).first()
        if not prov:
            print(f"  [!] Provinsi tidak ditemukan: {t['prov']}")
            continue

        kab = db.query(Region).filter(
            Region.level == "kabupaten",
            Region.parent_code == prov.code,
            Region.name.ilike(f"%{t['kab']}%"),
        ).first()
        if not kab:
            print(f"  [!] Kabupaten tidak ditemukan: {t['kab']} (parent {prov.code})")
            continue

        kec = db.query(Region).filter(
            Region.level == "kecamatan",
            Region.parent_code == kab.code,
            Region.name.ilike(f"%{t['kec']}%"),
        ).first() if t.get("kec") else None

        # Tentukan kode final
        if t["use_level"] == "kecamatan" and kec:
            new_code = kec.code
            path = f"{prov.name} > {kab.name} > {kec.name}"
        elif t["use_level"] == "kabupaten":
            new_code = kab.code
            path = f"{prov.name} > {kab.name}"
        else:
            new_code = kab.code
            path = f"{prov.name} > {kab.name}"

        old_code = proj.region_code
        proj.region_code = new_code
        print(f"  [OK] {t['project']}")
        print(f"       Kode lama : {old_code}")
        print(f"       Kode baru : {new_code}")
        print(f"       Path      : {path}")

    db.commit()


def verify(db):
    section("3. VERIFIKASI")

    print("\n  Region per level:")
    stats = db.execute(text("""
        SELECT level, COUNT(*) FROM regions GROUP BY level ORDER BY 2 DESC
    """)).fetchall()
    for lvl, cnt in stats:
        print(f"    {str(lvl):15s} : {cnt:>7}")

    print("\n  Proyek CTW & wilayah barunya:")
    projects = db.query(Project).all()
    for p in projects:
        reg = db.query(Region).filter(Region.code == p.region_code).first()
        reg_name = reg.name if reg else "❌ TIDAK DITEMUKAN"
        print(f"    • {p.name[:40]:40s}")
        print(f"      region_code = {p.region_code}")
        print(f"      wilayah     = {reg_name}")

    print("\n  Orphan tersisa:")
    orphan = db.execute(text("""
        SELECT COUNT(*) FROM regions
        WHERE parent_code IS NOT NULL
          AND parent_code NOT IN (SELECT code FROM regions)
    """)).scalar()
    print(f"    {orphan} baris (tidak fatal - wilayah baru hasil pemekaran)")


def main():
    print("=" * 70)
    print("  FIX WILAYAH & SEED PROYEK CTW")
    print("=" * 70)

    db = SessionLocal()
    try:
        inspect_orphan(db)
        fix_project_regions(db)
        verify(db)
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

    print("\n" + SEP)
    print("  SELESAI")
    print(SEP)
    print("Langkah berikutnya:")
    print("  uvicorn server.main:app --reload --port 8000")
    print("  → Coba pilih: Riau > Pelalawan > Pangkalan Kerinci")
    print("  → Proyek Trans-Sumatra harus muncul!")


if __name__ == "__main__":
    main()
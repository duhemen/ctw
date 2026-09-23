"""Debug: cek kenapa proyek baru tidak muncul di dashboard."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import extract, or_, and_
from core.database import SessionLocal
from core.models import Project, Region


SEP = "=" * 70
def section(t):
    print(f"\n{SEP}\n  {t}\n{SEP}")


def main():
    db = SessionLocal()
    try:
        section("SEMUA PROYEK DI DATABASE")
        projects = db.query(Project).order_by(Project.created_at.desc()).all()
        print(f"\nTotal: {len(projects)} proyek\n")

        for p in projects:
            print(f"ID {p.id}: {p.name}")
            print(f"  Status       : {p.status}")
            print(f"  Risk         : {p.risk_level}")
            print(f"  Region code  : {p.region_code}")
            print(f"  Lat/Lng      : {p.latitude}, {p.longitude}")
            print(f"  Kontrak      : {p.contract_start} s/d {p.contract_end}")
            print(f"  Multi-year   : {p.is_multi_year}")
            print(f"  Progress     : {p.progress_physical}%")
            print(f"  Created      : {p.created_at}")
            print()

        section("VALIDASI SETIAP PROYEK")

        current_year = 2026
        for p in projects:
            issues = []

            # Cek 1: status
            if p.status != "Berjalan":
                issues.append(f"❌ Status '{p.status}' bukan 'Berjalan' (dashboard filter hanya tampilkan Berjalan)")

            # Cek 2: koordinat valid
            if not p.latitude or not (-90 <= p.latitude <= 90):
                issues.append(f"❌ Latitude tidak valid: {p.latitude} (harus -90 s/d 90)")
            if not p.longitude or not (-180 <= p.longitude <= 180):
                issues.append(f"❌ Longitude tidak valid: {p.longitude} (harus -180 s/d 180)")

            # Cek 3: region code match
            if p.region_code:
                region = db.query(Region).filter(Region.code == p.region_code).first()
                if not region:
                    issues.append(f"❌ Region code '{p.region_code}' tidak ada di tabel regions")
                else:
                    print(f"  ℹ️  Proyek '{p.name}' → wilayah: {region.name} ({region.level})")
            else:
                issues.append("⚠️  Region code kosong")

            # Cek 4: filter tahun (multi-year OR dalam rentang)
            if not p.is_multi_year:
                if not p.contract_start or not p.contract_end:
                    issues.append("❌ Tanggal kontrak kosong (tidak akan lolos filter tahun)")
                else:
                    if not (p.contract_start.year <= current_year <= p.contract_end.year):
                        issues.append(
                            f"❌ Tahun {current_year} di luar rentang kontrak "
                            f"({p.contract_start.year}-{p.contract_end.year})"
                        )

            if issues:
                print(f"  Proyek #{p.id} '{p.name}':")
                for iss in issues:
                    print(f"    {iss}")
                print()
            else:
                print(f"  ✅ Proyek #{p.id} '{p.name}' valid (harusnya muncul)")

        section("SIMULASI QUERY DASHBOARD - PAPUA PEGUNUNGAN")

        # Simulasi query seperti di /api/dashboard
        region_code = "94"  # Kode Papua Pegunungan mungkin 94 atau 95
        papua_regions = db.query(Region).filter(
            Region.name.ilike("%Papua Pegunungan%")
        ).all()
        print("\nWilayah dengan nama 'Papua Pegunungan':")
        for r in papua_regions:
            print(f"  {r.code} | {r.name} | level={r.level} | parent={r.parent_code}")
            region_code = r.code

        if papua_regions:
            print(f"\nQuery dengan region_code = '{region_code}':")
            q = db.query(Project).filter(Project.region_code.like(f"{region_code}%"))
            print(f"  Step 1 (region filter): {q.count()} proyek")

            q2 = q.filter(Project.status == "Berjalan")
            print(f"  Step 2 (status='Berjalan'): {q2.count()} proyek")

            q3 = q2.filter(or_(
                Project.is_multi_year == True,
                and_(
                    extract("year", Project.contract_start) <= current_year,
                    extract("year", Project.contract_end) >= current_year,
                ),
            ))
            print(f"  Step 3 (tahun={current_year}): {q3.count()} proyek")

            if q3.count() == 0 and q.count() > 0:
                print("\n  ⚠️  Ada proyek di wilayah ini, tapi ter-exclude oleh filter lanjutan.")
                print("     Cek list issue di atas untuk tahu penyebabnya.")

        section("CEK WILAYAH YANG BARU DIINPUT")

        # Cek proyek paling baru
        newest = db.query(Project).order_by(Project.created_at.desc()).first()
        if newest:
            print(f"\nProyek terbaru: '{newest.name}' (ID {newest.id})")
            print(f"  Region code: {newest.region_code}")
            if newest.region_code:
                reg = db.query(Region).filter(Region.code == newest.region_code).first()
                if reg:
                    print(f"  Wilayah     : {reg.name} ({reg.level})")
                    # Trace up
                    path = []
                    current = reg
                    while current:
                        path.insert(0, f"{current.name} ({current.level})")
                        if not current.parent_code:
                            break
                        current = db.query(Region).filter(Region.code == current.parent_code).first()
                    print(f"  Hierarki    : {' > '.join(path)}")
                else:
                    print(f"  ❌ Tidak ada di tabel regions!")

    finally:
        db.close()


if __name__ == "__main__":
    main()
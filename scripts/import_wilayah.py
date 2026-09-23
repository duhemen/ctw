"""
Impor wilayah lengkap dari data/spatianomics.db ke tabel regions CTW.
Read-only pada sumber, destructive pada tabel regions (akan di-reset).
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, insert, func, text
from core.database import SessionLocal, init_db
from core.models import Region

SPATIANOMICS_DB = ROOT / "data" / "spatianomics.db"

# Normalisasi nama level
LEVEL_MAP = {
    "provinsi": "provinsi",
    "province": "provinsi",
    "kabupaten": "kabupaten",
    "kota": "kabupaten",
    "kabupaten/kota": "kabupaten",
    "kab.": "kabupaten",
    "kota.": "kabupaten",
    "kecamatan": "kecamatan",
    "kec.": "kecamatan",
    "kelurahan": "kelurahan",
    "desa": "kelurahan",
    "kelurahan/desa": "kelurahan",
    "kel.": "kelurahan",
    "desa.": "kelurahan",
}


def normalize_level(lvl):
    if not lvl:
        return None
    return LEVEL_MAP.get(str(lvl).strip().lower(), str(lvl).strip().lower())


def main():
    print("=" * 70)
    print("  IMPOR WILAYAH DARI spatianomics.db → CTW regions")
    print("=" * 70)

    if not SPATIANOMICS_DB.exists():
        print(f"\n[ERROR] File tidak ditemukan: {SPATIANOMICS_DB}")
        print("Pastikan file sudah diletakkan di: data/spatianomics.db")
        return

    size_mb = SPATIANOMICS_DB.stat().st_size / 1024 / 1024
    print(f"\n[1/5] Membuka {SPATIANOMICS_DB.name} ({size_mb:.0f} MB)...")
    src = sqlite3.connect(f"file:{SPATIANOMICS_DB}?mode=ro", uri=True)

    # Statistik sumber
    print("\n[2/5] Analisis data sumber...")
    try:
        rows_level = src.execute(
            "SELECT level, COUNT(*) FROM wilayah GROUP BY level ORDER BY 2 DESC"
        ).fetchall()
        for lvl, cnt in rows_level:
            print(f"      {str(lvl):25s} : {cnt:>7} baris")
        total = src.execute("SELECT COUNT(*) FROM wilayah").fetchone()[0]
        print(f"      {'TOTAL':25s} : {total:>7} baris")
    except Exception as e:
        print(f"[ERROR] Gagal baca tabel wilayah: {e}")
        return

    # Format kode: cek apakah pakai titik
    sample_prov = src.execute(
        "SELECT kode, nama FROM wilayah WHERE level='provinsi' ORDER BY kode LIMIT 3"
    ).fetchall()
    sample_kab = src.execute(
        "SELECT kode, nama, parent_kode FROM wilayah WHERE level='kabupaten' ORDER BY kode LIMIT 3"
    ).fetchall()
    sample_kec = src.execute(
        "SELECT kode, nama, parent_kode FROM wilayah WHERE level='kecamatan' ORDER BY kode LIMIT 3"
    ).fetchall()
    sample_kel = src.execute(
        "SELECT kode, nama, parent_kode FROM wilayah WHERE level IN ('kelurahan','desa') ORDER BY kode LIMIT 3"
    ).fetchall()

    print("\n      Sample format kode:")
    print(f"        Provinsi  : {sample_prov}")
    print(f"        Kabupaten : {sample_kab}")
    print(f"        Kecamatan : {sample_kec}")
    print(f"        Kelurahan : {sample_kel}")

    # Baca semua baris
    print("\n[3/5] Membaca semua baris wilayah...")
    rows = src.execute("""
        SELECT kode, nama, level, parent_kode, latitude, longitude
        FROM wilayah
        WHERE kode IS NOT NULL
          AND nama IS NOT NULL
          AND TRIM(kode) != ''
          AND TRIM(nama) != ''
        ORDER BY LENGTH(kode), kode
    """).fetchall()
    src.close()
    print(f"      {len(rows)} baris siap diimpor.")

    # Insert ke CTW
    print("\n[4/5] Insert ke tabel regions CTW...")
    init_db()
    db = SessionLocal()
    try:
        # Clear data lama
        deleted = db.execute(delete(Region)).rowcount
        if deleted:
            print(f"      Menghapus {deleted} baris lama (seed data)")
        db.commit()

        # Bulk insert per batch
        BATCH = 5000
        inserted = 0
        for i in range(0, len(rows), BATCH):
            batch = rows[i:i + BATCH]
            data = []
            for kode, nama, lvl, parent, lat, lng in batch:
                data.append({
                    "code": str(kode).strip(),
                    "name": str(nama).strip(),
                    "level": normalize_level(lvl),
                    "parent_code": str(parent).strip() if parent else None,
                    "latitude": float(lat) if lat is not None else None,
                    "longitude": float(lng) if lng is not None else None,
                })
            db.execute(insert(Region), data)
            db.flush()
            inserted += len(batch)
            print(f"      {inserted:>7}/{len(rows)}")
        db.commit()
        print(f"      [OK] {inserted} baris diimpor.")

        # Verifikasi
        print("\n[5/5] VERIFIKASI")
        print("      Distribusi per level:")
        stats = db.query(Region.level, func.count(Region.code)).group_by(Region.level).all()
        for lvl, cnt in stats:
            print(f"        {str(lvl):20s} : {cnt:>7}")
        total_db = db.query(func.count(Region.code)).scalar()
        print(f"        {'TOTAL':20s} : {total_db:>7}")

        # Cek hierarki
        print("\n      Cek integritas hierarki:")
        orphan = db.execute(text("""
            SELECT COUNT(*) FROM regions
            WHERE parent_code IS NOT NULL
              AND parent_code NOT IN (SELECT code FROM regions)
        """)).scalar()
        print(f"        Wilayah tanpa parent (orphan): {orphan}")

        # Cek apakah kode seed CTW masih ada
        print("\n      Cek kode dari seed CTW sebelumnya:")
        seed_codes = [
            "14.05.02.1001", "1405021001",
            "62.03.01.1001", "6203011001",
            "32.01.01.1001", "3201011001",
        ]
        found = db.query(Region.code, Region.name).filter(Region.code.in_(seed_codes)).all()
        if found:
            print(f"        [OK] Ditemukan {len(found)}:")
            for c, n in found:
                print(f"          • {c} → {n}")
        else:
            print("        [WARN] Tidak ada kode seed yang cocok!")
            print("        Format kode dari spatianomics mungkin berbeda.")
            print("        Sample kode kelurahan dari DB baru:")
            sample_new = db.query(Region.code, Region.name).filter(
                Region.level == "kelurahan"
            ).limit(3).all()
            for c, n in sample_new:
                print(f"          • {c} → {n}")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

    print("\n" + "=" * 70)
    print("  SELESAI")
    print("=" * 70)
    print("Langkah berikutnya:")
    print("  uvicorn server.main:app --reload --port 8000")
    print("  → Refresh browser, dropdown wilayah sekarang lengkap 38 provinsi!")


if __name__ == "__main__":
    main()
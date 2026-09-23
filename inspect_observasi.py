"""Inspeksi tabel observasi di spatianomics.db."""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "spatianomics.db"
SEP = "=" * 70


def section(t):
    print(f"\n{SEP}\n  {t}\n{SEP}")


def main():
    if not DB.exists():
        print(f"❌ File tidak ditemukan: {DB}")
        return

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    cur = con.cursor()

    # ============ CUSTOM VARIABLE ============
    section("1. TABEL custom_variable (20 baris)")
    cur.execute("SELECT * FROM custom_variable LIMIT 5")
    cols = [d[0] for d in cur.description]
    print(f"Kolom: {cols}\n")
    for row in cur.fetchall():
        print(f"  • {row}")

    print("\n-- Semua variabel (kode + nama) --")
    cur.execute("SELECT kode, nama, level_target, tipe, severity_weight, is_active FROM custom_variable ORDER BY kode")
    for row in cur.fetchall():
        print(f"  {row[0]:20s} | {row[1][:40]:40s} | {row[2] or '-':12s} | {row[3] or '-':10s} | w={row[4]} | active={row[5]}")

    # ============ FIELD OBSERVATION ============
    section("2. TABEL field_observation (15 baris)")
    cur.execute("SELECT * FROM field_observation LIMIT 3")
    cols = [d[0] for d in cur.description]
    print(f"Kolom: {cols}\n")
    for row in cur.fetchall():
        print(f"  • {row}\n")

    print("-- Ringkasan field_observation --")
    cur.execute("""
        SELECT
            variable_kode,
            COUNT(*) as cnt,
            AVG(nilai) as avg_nilai,
            MIN(nilai) as min_nilai,
            MAX(nilai) as max_nilai
        FROM field_observation
        GROUP BY variable_kode
        ORDER BY cnt DESC
    """)
    print(f"\n  {'Variabel':20s} | {'Count':>5s} | {'Avg':>10s} | {'Min':>10s} | {'Max':>10s}")
    print(f"  {'-'*20} | {'-'*5} | {'-'*10} | {'-'*10} | {'-'*10}")
    for row in cur.fetchall():
        print(f"  {row[0]:20s} | {row[1]:>5} | {row[2]:>10.2f} | {row[3]:>10.2f} | {row[4]:>10.2f}")

    # ============ WILAYAH REFERENCED ============
    section("3. WILAYAH YANG DIRUJUK field_observation")
    cur.execute("""
        SELECT fo.wilayah_kode, w.nama, w.level, COUNT(*) as cnt
        FROM field_observation fo
        LEFT JOIN wilayah w ON w.kode = fo.wilayah_kode
        GROUP BY fo.wilayah_kode
        ORDER BY cnt DESC
        LIMIT 20
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:15s} | {row[1] or '?':40s} | {row[2] or '?':12s} | {row[3]} obs")

    # ============ SAMPLE DATA LENGKAP ============
    section("4. SAMPLE 5 BARIS LENGKAP field_observation")
    cur.execute("""
        SELECT id, wilayah_kode, variable_kode, nilai, catatan,
               latitude, longitude, observer, verified, timestamp
        FROM field_observation
        ORDER BY id DESC
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"\n  ID {row[0]}:")
        print(f"    Wilayah    : {row[1]}")
        print(f"    Variabel   : {row[2]}")
        print(f"    Nilai      : {row[3]}")
        print(f"    Catatan    : {row[4]}")
        print(f"    Koordinat  : {row[5]}, {row[6]}")
        print(f"    Observer   : {row[7]}")
        print(f"    Verified   : {row[8]}")
        print(f"    Timestamp  : {row[9]}")

    con.close()

    section("SELESAI")
    print("Copy-paste seluruh output ini ke chat.")


if __name__ == "__main__":
    main()
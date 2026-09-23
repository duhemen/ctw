"""Inspeksi sumber data wilayah CTW. Read-only, tidak mengubah apa pun."""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
DATA = ROOT / "data"

SEP = "=" * 70


def section(title):
    print(f"\n{SEP}\n  {title}\n{SEP}")


def peek_sql(path, n_lines=40):
    """Cetak n baris pertama dari file .sql."""
    print(f"\n--- {path.name} ({path.stat().st_size / 1024 / 1024:.1f} MB) ---")
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                if i >= n_lines:
                    break
                print(line.rstrip()[:200])
    except Exception as e:
        print(f"  [ERROR] {e}")


def inspect_sqlite(db_path):
    """Buka SQLite dan tampilkan semua tabel + skema + row count."""
    print(f"\n--- {db_path.name} ({db_path.stat().st_size / 1024 / 1024:.1f} MB) ---")
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = con.cursor()

        cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY name")
        objects = cur.fetchall()

        print(f"  Total objek: {len(objects)}")
        for name, obj_type in objects:
            try:
                cur.execute(f'SELECT COUNT(*) FROM "{name}"')
                count = cur.fetchone()[0]
            except Exception:
                count = "?"
            print(f"  • [{obj_type}] {name:40s} rows={count}")

        # Schema
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table'")
        schemas = cur.fetchall()
        print("\n  --- Skema (5 tabel pertama) ---")
        for (sql,) in schemas[:5]:
            if sql:
                print(f"  {sql[:400]}")
                print()

        # Auto-detect tabel wilayah
        wilayah_candidates = []
        for name, _ in objects:
            low = name.lower()
            if any(k in low for k in ["wilayah", "region", "provinsi", "kabupaten", "kecamatan", "kelurahan", "boundaries", "adm"]):
                wilayah_candidates.append(name)

        if wilayah_candidates:
            print(f"\n  🎯 Kandidat tabel wilayah: {wilayah_candidates}")
            for tbl in wilayah_candidates[:3]:
                print(f"\n  --- Sample 3 baris dari '{tbl}' ---")
                try:
                    cur.execute(f'SELECT * FROM "{tbl}" LIMIT 3')
                    cols = [d[0] for d in cur.description]
                    print(f"  Kolom: {cols}")
                    for row in cur.fetchall():
                        # Truncate kolom panjang (mis. geom)
                        short = tuple(
                            (str(v)[:60] + "..." if isinstance(v, (str, bytes)) and len(str(v)) > 60 else v)
                            for v in row
                        )
                        print(f"    {short}")
                except Exception as e:
                    print(f"    [ERROR] {e}")

        con.close()
    except Exception as e:
        print(f"  [ERROR] {e}")


def inspect_folder(folder):
    if not folder.exists():
        return
    files = list(folder.iterdir())
    print(f"\n--- {folder.name}/ ({len(files)} file) ---")
    for f in files[:10]:
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name:50s} {size_kb:>10.1f} KB")
    if len(files) > 10:
        print(f"  ... dan {len(files) - 10} file lain")


def main():
    section("1. STRUCTURE DATA/RAW")
    if RAW.exists():
        for f in sorted(RAW.iterdir()):
            if f.is_file():
                print(f"  {f.name:40s} {f.stat().st_size / 1024 / 1024:>10.2f} MB")
            else:
                print(f"  {f.name + '/':40s} (folder)")

    section("2. PEEK SQL FILES")
    for name in ["ddl_wilayah_boundaries.sql", "wilayah.sql", "wilayah_level_1_2.sql"]:
        p = RAW / name
        if p.exists():
            peek_sql(p, n_lines=40)

    section("3. SQLITE - spatianomics.db")
    db = DATA / "spatianomics.db"
    if db.exists():
        inspect_sqlite(db)

    section("4. SQLITE - client_cache.db")
    db2 = DATA / "client_cache.db"
    if db2.exists():
        inspect_sqlite(db2)

    section("5. FOLDER PROV/KAB/KEC/KEL")
    for sub in ["prov", "kab", "kec", "kel"]:
        inspect_folder(RAW / sub)

    section("6. GEOJSON HEAD")
    for name in ["boundaries_provinsi.geojson", "boundaries_kabupaten.geojson"]:
        p = RAW / name
        if p.exists():
            print(f"\n--- {name} ({p.stat().st_size / 1024:.0f} KB) ---")
            with open(p, encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= 3:
                        break
                    print(line.rstrip()[:500])

    section("SELESAI")
    print("Silakan copy-paste seluruh output ini ke chat.")


if __name__ == "__main__":
    main()
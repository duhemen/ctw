"""Impor data observasi dari spatianomics.db ke CTW."""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.database import SessionLocal, init_db
from core.models import ObservationVariable, Observation

SPATIANOMICS = ROOT / "data" / "spatianomics.db"


def classify_severity(score):
    if score >= 0.8:
        return "tinggi"
    if score >= 0.5:
        return "sedang"
    return "rendah"


def main():
    print("=" * 70)
    print("  IMPOR OBSERVASI DARI spatianomics.db")
    print("=" * 70)

    if not SPATIANOMICS.exists():
        print(f"[ERROR] {SPATIANOMICS} tidak ditemukan")
        return

    init_db()
    con = sqlite3.connect(f"file:{SPATIANOMICS}?mode=ro", uri=True)
    cur = con.cursor()

    # ============ IMPORT VARIABLES ============
    print("\n[1/3] Import variabel observasi...")
    cur.execute("""
        SELECT kode, nama, deskripsi, level_target, tipe,
               severity_weight, is_active, is_approved
        FROM custom_variable
        ORDER BY kode
    """)
    variables = cur.fetchall()
    print(f"     Ditemukan {len(variables)} variabel dari spatianomics")

    db = SessionLocal()
    try:
        # Clear existing (idempotent)
        db.query(ObservationVariable).delete()
        db.commit()

        inserted_var = 0
        for v in variables:
            db.add(ObservationVariable(
                kode=v[0], nama=v[1], deskripsi=v[2] or "",
                level_target=v[3] or "", tipe=v[4] or "boolean",
                severity_weight=float(v[5] or 0.5),
                is_active=bool(v[6]), is_approved=bool(v[7]),
            ))
            inserted_var += 1
        db.commit()
        print(f"     [OK] {inserted_var} variabel tersimpan")

        # ============ IMPORT OBSERVATIONS ============
        print("\n[2/3] Import data observasi lapangan...")
        cur.execute("""
            SELECT wilayah_kode, variable_kode, nilai, catatan, foto_path,
                   latitude, longitude, observer, verified, verified_by,
                   rejected, rejection_reason, timestamp
            FROM field_observation
            ORDER BY id
        """)
        observations = cur.fetchall()
        print(f"     Ditemukan {len(observations)} observasi dari spatianomics")

        # Clear existing
        db.query(Observation).delete()
        db.commit()

        # Map variable -> weight
        weights = {v[0]: float(v[5] or 0.5) for v in variables}

        inserted_obs = 0
        for o in observations:
            var_kode = o[1]
            nilai = float(o[2] or 0.0)
            weight = weights.get(var_kode, 0.5)
            score = weight * nilai

            # Parse timestamp
            ts = o[12]
            try:
                ts_dt = datetime.fromisoformat(ts) if ts else datetime.utcnow()
            except Exception:
                ts_dt = datetime.utcnow()

            db.add(Observation(
                wilayah_kode=o[0], variable_kode=var_kode,
                nilai=nilai, catatan=o[3] or "",
                foto_path=o[4] or "",
                latitude=float(o[5]) if o[5] is not None else None,
                longitude=float(o[6]) if o[6] is not None else None,
                observer=o[7] or "", verified=bool(o[8]),
                verified_by=o[9] or "", rejected=bool(o[10]),
                rejection_reason=o[11] or "",
                timestamp=ts_dt,
                severity_score=score,
                severity_level=classify_severity(score),
            ))
            inserted_obs += 1
        db.commit()
        print(f"     [OK] {inserted_obs} observasi tersimpan")

        # ============ STATS ============
        print("\n[3/3] Verifikasi")
        print(f"     Total variabel  : {db.query(ObservationVariable).count()}")
        print(f"     Total observasi : {db.query(Observation).count()}")

        print("\n     Distribusi severity:")
        for lvl in ["rendah", "sedang", "tinggi"]:
            cnt = db.query(Observation).filter(Observation.severity_level == lvl).count()
            print(f"       {lvl:10s} : {cnt}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        con.close()

    print("\n" + "=" * 70)
    print("  SELESAI!")
    print("=" * 70)


if __name__ == "__main__":
    main()

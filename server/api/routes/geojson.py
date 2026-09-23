"""Endpoint GeoJSON batas wilayah - ambil dari spatianomics.db on-demand."""
import json
import sqlite3
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/regions", tags=["GeoJSON"])

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SPATIANOMICS_DB = ROOT / "data" / "spatianomics.db"
CACHE_DIR = ROOT / "data" / "processed" / "geojson_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Tolerance simplify per level (derajat)
SIMPLIFY_TOLERANCE = {
    "provinsi": 0.05,
    "kabupaten": 0.02,
    "kecamatan": 0.01,
    "kelurahan": 0.005,
}

# Memory cache
_MEM_CACHE = {}


def _read_geojson_from_db(code: str) -> Optional[dict]:
    """Baca raw geojson dari spatianomics.db (read-only)."""
    if not SPATIANOMICS_DB.exists():
        return None
    try:
        con = sqlite3.connect(f"file:{SPATIANOMICS_DB}?mode=ro", uri=True)
        cur = con.cursor()
        row = cur.execute(
            "SELECT geojson FROM wilayah WHERE kode = ? LIMIT 1", (code,)
        ).fetchone()
        con.close()
        if not row or not row[0]:
            return None
        gj = json.loads(row[0])
        return gj
    except Exception as e:
        print(f"[geojson] error baca {code}: {e}")
        return None


def _simplify(geojson: dict, tolerance: float) -> dict:
    """Simplify pakai shapely. Fallback ke raw kalau gagal."""
    if tolerance <= 0:
        return geojson
    try:
        from shapely.geometry import shape, mapping
        from shapely import simplify as shp_simplify

        geom = shape(geojson)
        simplified = shp_simplify(geom, tolerance, preserve_topology=True)
        return mapping(simplified)
    except Exception as e:
        print(f"[geojson] simplify fail, pakai raw: {e}")
        return geojson


def _cache_path(code: str) -> Path:
    return CACHE_DIR / f"{code}.json"


def get_geojson_simplified(code: str, level: Optional[str] = None) -> Optional[dict]:
    """Ambil geojson ter-simplify dengan cache memori + disk."""
    if code in _MEM_CACHE:
        return _MEM_CACHE[code]

    cache_file = _cache_path(code)
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            _MEM_CACHE[code] = data
            return data
        except Exception:
            pass

    raw = _read_geojson_from_db(code)
    if not raw:
        return None

    tol = SIMPLIFY_TOLERANCE.get(level or "provinsi", 0.02)
    simplified = _simplify(raw, tol)

    _MEM_CACHE[code] = simplified
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(simplified, f)
    except Exception:
        pass

    return simplified


@router.get("/{code}/geojson")
async def region_geojson(code: str, level: Optional[str] = Query(None)):
    """GeoJSON batas satu wilayah."""
    gj = get_geojson_simplified(code, level)
    if not gj:
        raise HTTPException(status_code=404, detail=f"GeoJSON tidak ditemukan untuk {code}")
    return JSONResponse(gj)


@router.get("/geojson/collection")
async def collection_geojson(
    parent_code: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
):
    """FeatureCollection dari semua child region di bawah parent_code."""
    if not SPATIANOMICS_DB.exists():
        raise HTTPException(status_code=500, detail="spatianomics.db tidak ditemukan")

    con = sqlite3.connect(f"file:{SPATIANOMICS_DB}?mode=ro", uri=True)
    cur = con.cursor()

    if level and not parent_code:
        rows = cur.execute(
            "SELECT kode, nama, level FROM wilayah WHERE level = ? ORDER BY kode",
            (level,),
        ).fetchall()
    elif parent_code and level:
        rows = cur.execute(
            "SELECT kode, nama, level FROM wilayah WHERE parent_kode = ? AND level = ? ORDER BY kode",
            (parent_code, level),
        ).fetchall()
    elif parent_code:
        rows = cur.execute(
            "SELECT kode, nama, level FROM wilayah WHERE parent_kode = ? ORDER BY kode",
            (parent_code,),
        ).fetchall()
    else:
        con.close()
        raise HTTPException(status_code=400, detail="Perlu parameter parent_code atau level")

    con.close()

    features = []
    for kode, nama, lvl in rows:
        gj = get_geojson_simplified(kode, lvl)
        if not gj:
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "code": kode,
                "name": nama,
                "level": lvl,
            },
            "geometry": gj,
        })

    return JSONResponse({
        "type": "FeatureCollection",
        "features": features,
    })

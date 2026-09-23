"""API observasi lapangan."""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Observation, ObservationVariable, Region

router = APIRouter(prefix="/api", tags=["Observations"])


def _serialize_obs(o: Observation, variable: Optional[ObservationVariable] = None, region: Optional[Region] = None):
    return {
        "id": o.id,
        "wilayah_kode": o.wilayah_kode,
        "wilayah_name": region.name if region else None,
        "variable_kode": o.variable_kode,
        "variable_name": variable.nama if variable else o.variable_kode,
        "nilai": o.nilai,
        "catatan": o.catatan,
        "latitude": o.latitude,
        "longitude": o.longitude,
        "observer": o.observer,
        "verified": o.verified,
        "severity_score": o.severity_score,
        "severity_level": o.severity_level,
        "timestamp": o.timestamp.isoformat() if o.timestamp else None,
    }


@router.get("/observations")
async def list_observations(
    region_code: Optional[str] = Query(None),
    variable_kode: Optional[str] = Query(None),
    severity: Optional[str] = Query(None, description="rendah|sedang|tinggi"),
    verified_only: bool = Query(False),
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db),
):
    """Daftar observasi, filter by wilayah, variabel, severity."""
    q = db.query(Observation)
    if region_code:
        q = q.filter(Observation.wilayah_kode.like(f"{region_code}%"))
    if variable_kode:
        q = q.filter(Observation.variable_kode == variable_kode)
    if severity:
        q = q.filter(Observation.severity_level == severity)
    if verified_only:
        q = q.filter(Observation.verified == True)
    obs = q.order_by(Observation.timestamp.desc()).limit(limit).all()

    # Preload names
    var_map = {v.kode: v for v in db.query(ObservationVariable).all()}
    reg_map = {r.code: r for r in db.query(Region).filter(
        Region.code.in_(set(o.wilayah_kode for o in obs))
    ).all()}

    return [_serialize_obs(o, var_map.get(o.variable_kode), reg_map.get(o.wilayah_kode)) for o in obs]


@router.get("/observations/variables")
async def list_variables(db: Session = Depends(get_db)):
    """Katalog 20 variabel observasi."""
    variables = db.query(ObservationVariable).filter(ObservationVariable.is_active == True).order_by(ObservationVariable.nama).all()
    return [
        {
            "kode": v.kode, "nama": v.nama, "deskripsi": v.deskripsi,
            "level_target": v.level_target, "tipe": v.tipe,
            "severity_weight": v.severity_weight,
        }
        for v in variables
    ]


@router.get("/observations/stats")
async def observation_stats(
    region_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Statistik agregat observasi."""
    q = db.query(Observation)
    if region_code:
        q = q.filter(Observation.wilayah_kode.like(f"{region_code}%"))

    total = q.count()
    by_severity = {}
    for lvl in ["rendah", "sedang", "tinggi"]:
        by_severity[lvl] = q.filter(Observation.severity_level == lvl).count()

    by_variable = (
        db.query(Observation.variable_kode, func.count(Observation.id))
        .filter(Observation.wilayah_kode.like(f"{region_code}%") if region_code else True)
        .group_by(Observation.variable_kode)
        .all()
    )
    var_map = {v.kode: v.nama for v in db.query(ObservationVariable).all()}

    return {
        "total": total,
        "by_severity": by_severity,
        "by_variable": [
            {"kode": vk, "nama": var_map.get(vk, vk), "count": cnt}
            for vk, cnt in by_variable
        ],
        "verified_count": q.filter(Observation.verified == True).count(),
    }


@router.get("/projects/{project_id}/nearby_observations")
async def nearby_observations(
    project_id: int,
    radius_km: float = Query(10.0, le=100),
    db: Session = Depends(get_db),
):
    """Observasi dalam radius X km dari proyek."""
    from core.models import Project
    import math

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return []

    # Bounding box approximation
    lat, lng = project.latitude, project.longitude
    deg_per_km = 1.0 / 111.0
    lat_min = lat - radius_km * deg_per_km
    lat_max = lat + radius_km * deg_per_km
    lng_min = lng - radius_km * deg_per_km / math.cos(math.radians(lat))
    lng_max = lng + radius_km * deg_per_km / math.cos(math.radians(lat))

    obs = db.query(Observation).filter(
        Observation.latitude.between(lat_min, lat_max),
        Observation.longitude.between(lng_min, lng_max),
    ).all()

    # Hitung jarak tepat
    result = []
    var_map = {v.kode: v for v in db.query(ObservationVariable).all()}
    reg_map = {r.code: r for r in db.query(Region).filter(
        Region.code.in_(set(o.wilayah_kode for o in obs))
    ).all()}

    for o in obs:
        if o.latitude is None or o.longitude is None:
            continue
        dlat = (o.latitude - lat) * 111.0
        dlng = (o.longitude - lng) * 111.0 * math.cos(math.radians(lat))
        dist = math.sqrt(dlat * dlat + dlng * dlng)
        if dist <= radius_km:
            item = _serialize_obs(o, var_map.get(o.variable_kode), reg_map.get(o.wilayah_kode))
            item["distance_km"] = round(dist, 2)
            result.append(item)

    result.sort(key=lambda x: x["distance_km"])
    return result

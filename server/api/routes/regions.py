"""API hierarki wilayah + search."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from core.models import Region

router = APIRouter(prefix="/api/regions", tags=["Regions"])


@router.get("")
async def list_regions(
    level: Optional[str] = Query(None),
    parent_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Region)
    if level:
        q = q.filter(Region.level == level)
    if parent_code:
        q = q.filter(Region.parent_code == parent_code)
    regions = q.order_by(Region.name).all()
    return [
        {
            "code": r.code,
            "name": r.name,
            "level": r.level,
            "parent_code": r.parent_code,
            "latitude": r.latitude,
            "longitude": r.longitude,
        }
        for r in regions
    ]


@router.get("/search")
async def search_regions(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
):
    """Search wilayah di semua level berdasarkan nama."""
    results = (
        db.query(Region)
        .filter(Region.name.ilike(f"%{q}%"))
        .order_by(Region.level, Region.name)
        .limit(limit)
        .all()
    )
    return [
        {
            "code": r.code,
            "name": r.name,
            "level": r.level,
            "parent_code": r.parent_code,
            "latitude": r.latitude,
            "longitude": r.longitude,
        }
        for r in results
    ]


@router.get("/{code}/path")
async def region_path(code: str, db: Session = Depends(get_db)):
    """Ambil hierarki lengkap dari kode wilayah (bottom-up)."""
    path = []
    current = db.query(Region).filter(Region.code == code).first()
    while current:
        path.insert(0, {
            "code": current.code,
            "name": current.name,
            "level": current.level,
            "latitude": current.latitude,
            "longitude": current.longitude,
        })
        if not current.parent_code:
            break
        current = db.query(Region).filter(Region.code == current.parent_code).first()
    return {"path": path}

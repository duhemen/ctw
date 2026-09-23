"""API proyek: dashboard stats, list, detail."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, and_, extract
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Project, Provider, Blacklist, Region, Feedback

router = APIRouter(prefix="/api", tags=["Projects"])

# Status yang dianggap "aktif" (muncul di dashboard default)
ACTIVE_STATUSES = ["Berjalan", "Perencanaan", "Ditunda"]
ALL_STATUSES = ["Berjalan", "Perencanaan", "Selesai", "Ditunda", "Dibatalkan"]


def _project_to_summary(p: Project):
    return {
        "id": p.id,
        "name": p.name,
        "lat": p.latitude,
        "lng": p.longitude,
        "status": p.status,
        "risk": p.risk_level,
        "provider": p.provider.name if p.provider else None,
        "contract_value": p.contract_value,
        "progress_physical": p.progress_physical,
        "region": p.region.name if p.region else None,
        "is_multi_year": p.is_multi_year,
    }


@router.get("/dashboard")
async def dashboard_stats(
    region_code: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    status: Optional[str] = Query("aktif", description="aktif | semua | Berjalan | Perencanaan | Selesai | Ditunda"),
    db: Session = Depends(get_db),
):
    """Stats untuk dashboard, terfilter wilayah, tahun, dan status."""
    if not region_code:
        return {
            "active": False,
            "total_projects": 0,
            "total_budget": 0,
            "total_budget_str": "-",
            "active_audits": 0,
            "public_reports": 0,
            "projects": [],
            "budget_data": {"labels": ["Q1", "Q2", "Q3", "Q4"], "values": [0, 0, 0, 0]},
            "risk_distribution": {"labels": ["Rendah", "Sedang", "Tinggi"], "values": [0, 0, 0]},
            "status_distribution": {"Berjalan": 0, "Perencanaan": 0, "Selesai": 0, "Ditunda": 0},
        }

    current_year = year or datetime.now().year

    # Base query: filter wilayah
    q = db.query(Project).filter(Project.region_code.like(f"{region_code}%"))

    # Filter status
    if status == "aktif" or not status:
        # Default: semua kecuali Dibatalkan & Selesai
        q = q.filter(Project.status.in_(["Berjalan", "Perencanaan", "Ditunda"]))
    elif status == "semua":
        q = q.filter(Project.status != "Dibatalkan")
    elif status in ALL_STATUSES:
        q = q.filter(Project.status == status)
    else:
        q = q.filter(Project.status.in_(["Berjalan", "Perencanaan", "Ditunda"]))

    # Filter tahun: multi-year selalu tampil, non-multi-year harus dalam rentang
    if year:
        q = q.filter(or_(
            Project.is_multi_year == True,  # noqa: E712
            Project.contract_start.is_(None),
            Project.contract_end.is_(None),
            and_(
                extract("year", Project.contract_start) <= current_year,
                extract("year", Project.contract_end) >= current_year,
            ),
        ))

    projects = q.all()

    total_budget = sum(p.contract_value or 0 for p in projects)
    if total_budget >= 1_000_000:
        budget_str = f"Rp {total_budget / 1_000_000:.1f} T"
    elif total_budget >= 1_000:
        budget_str = f"Rp {total_budget / 1_000:.0f} M"
    else:
        budget_str = f"Rp {total_budget:.0f} jt"

    risk_count = {"Rendah": 0, "Sedang": 0, "Tinggi": 0}
    for p in projects:
        if p.risk_level in risk_count:
            risk_count[p.risk_level] += 1

    status_count = {"Berjalan": 0, "Perencanaan": 0, "Selesai": 0, "Ditunda": 0}
    for p in projects:
        if p.status in status_count:
            status_count[p.status] += 1

    budget_data = {
        "labels": ["Q1", "Q2", "Q3", "Q4"],
        "values": [int(total_budget * 0.15), int(total_budget * 0.25),
                   int(total_budget * 0.30), int(total_budget * 0.30)],
    }

    active_audits = db.query(Feedback).filter(Feedback.feedback_type == "audit").count()
    public_reports = db.query(Feedback).filter(Feedback.feedback_type == "publik").count()

    return {
        "active": True,
        "region_code": region_code,
        "year": current_year,
        "status_filter": status,
        "total_projects": len(projects),
        "total_budget": total_budget,
        "total_budget_str": budget_str,
        "active_audits": active_audits,
        "public_reports": public_reports,
        "projects": [_project_to_summary(p) for p in projects],
        "budget_data": budget_data,
        "risk_distribution": {
            "labels": list(risk_count.keys()),
            "values": list(risk_count.values()),
        },
        "status_distribution": status_count,
    }


@router.get("/projects/{project_id}/detail")
async def project_detail(project_id: int, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    region_path = []
    r = p.region
    while r:
        region_path.insert(0, {"code": r.code, "name": r.name, "level": r.level})
        r = db.query(Region).filter(Region.code == r.parent_code).first() if r.parent_code else None

    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "address": p.address,
        "region_path": region_path,
        "latitude": p.latitude,
        "longitude": p.longitude,
        "status": p.status,
        "risk_level": p.risk_level,
        "provider": {
            "id": p.provider.id, "name": p.provider.name,
            "classification": p.provider.classification,
            "qualification": p.provider.qualification,
            "npwp": p.provider.npwp, "phone": p.provider.phone,
            "email": p.provider.email,
        } if p.provider else None,
        "supervisor": {
            "id": p.supervisor.id, "name": p.supervisor.name,
        } if p.supervisor else None,
        "contract": {
            "number": p.contract_number, "value": p.contract_value,
            "start": p.contract_start.isoformat() if p.contract_start else None,
            "end": p.contract_end.isoformat() if p.contract_end else None,
            "duration_days": p.duration_days, "is_multi_year": p.is_multi_year,
            "funding_source": p.funding_source, "fiscal_year": p.fiscal_year,
        },
        "progress": {
            "physical": p.progress_physical, "financial": p.progress_financial,
            "time_work": p.time_work_percent,
            "updated_at": p.progress_updated_at.isoformat() if p.progress_updated_at else None,
        },
        "schedules": [
            {"period": s.period, "planned": s.planned_percent, "actual": s.actual_percent}
            for s in p.schedules
        ],
        "milestones": [
            {"name": m.name,
             "target_date": m.target_date.isoformat() if m.target_date else None,
             "actual_date": m.actual_date.isoformat() if m.actual_date else None,
             "status": m.status, "progress": m.progress, "notes": m.notes}
            for m in p.milestones
        ],
        "photos": [
            {"id": ph.id, "url": ph.file_path, "caption": ph.caption, "category": ph.category}
            for ph in p.photos
        ],
    }

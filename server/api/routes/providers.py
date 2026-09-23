"""API penyedia jasa & blacklist."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Provider, Blacklist, Project

router = APIRouter(prefix="/api", tags=["Providers"])


@router.get("/providers")
async def list_providers(
    region_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Daftar penyedia. Jika region_code diisi, filter penyedia yang punya proyek di wilayah itu."""
    q = db.query(Provider)

    if region_code:
        # Cari provider yang punya proyek di wilayah region_code
        provider_ids = (
            db.query(Project.provider_id)
            .filter(Project.region_code.like(f"{region_code}%"))
            .filter(Project.provider_id.isnot(None))
            .distinct()
            .all()
        )
        ids = [pid for (pid,) in provider_ids]
        if not ids:
            return []
        q = q.filter(Provider.id.in_(ids))

    providers = q.order_by(Provider.name).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "npwp": p.npwp,
            "siujk_number": p.siujk_number,
            "classification": p.classification,
            "qualification": p.qualification,
            "address": p.address,
            "region": p.region.name if p.region else None,
            "contact_person": p.contact_person,
            "phone": p.phone,
            "email": p.email,
            "is_blacklisted": len([b for b in p.blacklist_entries if b.status == "Aktif"]) > 0,
        }
        for p in providers
    ]


@router.get("/blacklist")
async def list_blacklist(db: Session = Depends(get_db)):
    entries = db.query(Blacklist).order_by(Blacklist.start_date.desc()).all()
    return [
        {
            "id": b.id,
            "provider_id": b.provider_id,
            "provider_name": b.provider.name if b.provider else "-",
            "reason": b.reason,
            "category": b.category,
            "regulation_ref": b.regulation_ref,
            "decision_by": b.decision_by,
            "decision_number": b.decision_number,
            "start_date": b.start_date.isoformat() if b.start_date else None,
            "end_date": b.end_date.isoformat() if b.end_date else None,
            "status": b.status,
            "document_url": b.document_url,
        }
        for b in entries
    ]

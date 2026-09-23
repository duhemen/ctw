"""Admin panel: login, dashboard, CRUD."""
from pathlib import Path
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import User, Project, Provider, Blacklist, Region, Feedback
from core.auth import (
    verify_password, hash_password, login_user, logout_user, get_current_user,
)
from core.csrf import verify_csrf
from core.rate_limit import limiter
from core.utils import utcnow

router = APIRouter(prefix="/admin", tags=["Admin"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
from core.templating import get_templates
templates = get_templates()


def require_user(request: Request):
    return get_current_user(request)


def _parse_date(s: str):
    if not s or not s.strip():
        return None
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except Exception:
        return None


def _parse_float(s, default=0.0):
    try:
        return float(str(s).strip()) if s else default
    except Exception:
        return default


def _parse_int(s, default=0):
    try:
        return int(str(s).strip()) if s else default
    except Exception:
        return default


# ---------- LOGIN ----------
@router.get("/login")
async def login_page(request: Request, next: str = "/admin/"):
    return templates.TemplateResponse(request, "admin/login.html", {
        "title": "Login Admin - CTW",
        "next": next,
        "error": None,
    })


@router.post("/login")
@limiter.limit("5/minute")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/admin/"),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(request, "admin/login.html", {
            "title": "Login Admin - CTW",
            "next": next,
            "error": "Username atau password salah. Coba lagi.",
        }, status_code=401)

    login_user(request, user.id, user.username)
    return RedirectResponse(url=next or "/admin/", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    logout_user(request)
    return RedirectResponse(url="/admin/login", status_code=303)


# ---------- DASHBOARD ----------
@router.get("/")
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login?next=/admin/", status_code=303)
    stats = {
        "projects": db.query(Project).count(),
        "providers": db.query(Provider).count(),
        "blacklist": db.query(Blacklist).filter(Blacklist.status == "Aktif").count(),
        "feedbacks": db.query(Feedback).count(),
        "regions": db.query(Region).count(),
        "users": db.query(User).count(),
    }
    recent_projects = db.query(Project).order_by(Project.created_at.desc()).limit(5).all()
    recent_feedbacks = db.query(Feedback).order_by(Feedback.created_at.desc()).limit(5).all()
    return templates.TemplateResponse(request, "admin/dashboard.html", {
        "title": "Admin Dashboard - CTW",
        "user": user, "stats": stats,
        "recent_projects": recent_projects, "recent_feedbacks": recent_feedbacks,
        "active_page": "dashboard",
    })


# ============================================================
# PROYEK
# ============================================================

@router.get("/projects")
async def projects_list(request: Request, db: Session = Depends(get_db)):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login?next=/admin/projects", status_code=303)
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return templates.TemplateResponse(request, "admin/projects.html", {
        "title": "Kelola Proyek - CTW",
        "user": user, "projects": projects, "active_page": "projects", "mode": "list",
    })


@router.get("/projects/new")
async def project_new(request: Request, db: Session = Depends(get_db)):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    providers = db.query(Provider).order_by(Provider.name).all()
    regions = db.query(Region).filter(Region.level == "kecamatan").order_by(Region.name).limit(500).all()
    return templates.TemplateResponse(request, "admin/project_form.html", {
        "title": "Tambah Proyek - CTW",
        "user": user, "project": None, "providers": providers, "regions": regions,
        "active_page": "projects", "mode": "create",
    })


@router.post("/projects/new")
async def project_create(
    request: Request,
    name: str = Form(...), description: str = Form(""),
    region_code: str = Form(""), address: str = Form(""),
    latitude: float = Form(...), longitude: float = Form(...),
    status: str = Form("Berjalan"),
    contract_number: str = Form(""), contract_value: float = Form(0),
    contract_start: str = Form(""), contract_end: str = Form(""),
    duration_days: int = Form(0), is_multi_year: str = Form(""),
    funding_source: str = Form(""), fiscal_year: int = Form(0),
    risk_level: str = Form("Sedang"),
    progress_physical: float = Form(0), progress_financial: float = Form(0),
    time_work_percent: float = Form(0),
    provider_id: str = Form(""), supervisor_id: str = Form(""),
    csrf_token: str = Form(""),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    p = Project(
        name=name.strip(), description=description.strip(),
        region_code=region_code.strip() or None, address=address.strip(),
        latitude=latitude, longitude=longitude, status=status,
        contract_number=contract_number.strip(), contract_value=contract_value,
        contract_start=_parse_date(contract_start), contract_end=_parse_date(contract_end),
        duration_days=duration_days, is_multi_year=(is_multi_year == "on"),
        funding_source=funding_source.strip(), fiscal_year=fiscal_year or None,
        risk_level=risk_level,
        progress_physical=progress_physical, progress_financial=progress_financial,
        time_work_percent=time_work_percent, progress_updated_at=utcnow(),
        provider_id=_parse_int(provider_id) or None, supervisor_id=_parse_int(supervisor_id) or None,
    )
    db.add(p); db.commit()
    return RedirectResponse("/admin/projects?success=created", status_code=303)


@router.get("/projects/{project_id}/edit")
async def project_edit(project_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Proyek tidak ditemukan")
    providers = db.query(Provider).order_by(Provider.name).all()
    regions = db.query(Region).filter(Region.level == "kecamatan").order_by(Region.name).limit(500).all()
    return templates.TemplateResponse(request, "admin/project_form.html", {
        "title": "Edit Proyek - CTW",
        "user": user, "project": project, "providers": providers, "regions": regions,
        "active_page": "projects", "mode": "edit",
    })


@router.post("/projects/{project_id}/edit")
async def project_update(
    project_id: int, request: Request,
    name: str = Form(...), description: str = Form(""),
    region_code: str = Form(""), address: str = Form(""),
    latitude: float = Form(...), longitude: float = Form(...),
    status: str = Form("Berjalan"),
    contract_number: str = Form(""), contract_value: float = Form(0),
    contract_start: str = Form(""), contract_end: str = Form(""),
    duration_days: int = Form(0), is_multi_year: str = Form(""),
    funding_source: str = Form(""), fiscal_year: int = Form(0),
    risk_level: str = Form("Sedang"),
    progress_physical: float = Form(0), progress_financial: float = Form(0),
    time_work_percent: float = Form(0),
    provider_id: str = Form(""), supervisor_id: str = Form(""),
    csrf_token: str = Form(""),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(404)
    p.name = name.strip(); p.description = description.strip()
    p.region_code = region_code.strip() or None; p.address = address.strip()
    p.latitude = latitude; p.longitude = longitude; p.status = status
    p.contract_number = contract_number.strip(); p.contract_value = contract_value
    p.contract_start = _parse_date(contract_start); p.contract_end = _parse_date(contract_end)
    p.duration_days = duration_days; p.is_multi_year = (is_multi_year == "on")
    p.funding_source = funding_source.strip(); p.fiscal_year = fiscal_year or None
    p.risk_level = risk_level
    p.progress_physical = progress_physical; p.progress_financial = progress_financial
    p.time_work_percent = time_work_percent; p.progress_updated_at = utcnow()
    p.provider_id = _parse_int(provider_id) or None
    p.supervisor_id = _parse_int(supervisor_id) or None
    db.commit()
    return RedirectResponse("/admin/projects?success=updated", status_code=303)


@router.post("/projects/{project_id}/delete")
async def project_delete(
    project_id: int, request: Request,
    csrf_token: str = Form(""),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    p = db.query(Project).filter(Project.id == project_id).first()
    if p:
        db.delete(p); db.commit()
    return RedirectResponse("/admin/projects?success=deleted", status_code=303)


# ============================================================
# PENYEDIA
# ============================================================

@router.get("/providers")
async def providers_list(request: Request, db: Session = Depends(get_db)):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login?next=/admin/providers", status_code=303)
    providers = db.query(Provider).order_by(Provider.name).all()
    return templates.TemplateResponse(request, "admin/providers.html", {
        "title": "Kelola Penyedia - CTW",
        "user": user, "providers": providers, "active_page": "providers", "mode": "list",
    })


@router.get("/providers/new")
async def provider_new(request: Request, db: Session = Depends(get_db)):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    regions = db.query(Region).filter(Region.level == "kabupaten").order_by(Region.name).limit(500).all()
    return templates.TemplateResponse(request, "admin/provider_form.html", {
        "title": "Tambah Penyedia - CTW",
        "user": user, "provider": None, "regions": regions,
        "active_page": "providers", "mode": "create",
    })


@router.post("/providers/new")
async def provider_create(
    request: Request,
    name: str = Form(...), npwp: str = Form(""), siujk_number: str = Form(""),
    classification: str = Form(""), qualification: str = Form(""),
    address: str = Form(""), region_code: str = Form(""),
    contact_person: str = Form(""), phone: str = Form(""), email: str = Form(""),
    csrf_token: str = Form(""),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    p = Provider(
        name=name.strip(), npwp=npwp.strip(), siujk_number=siujk_number.strip(),
        classification=classification.strip(), qualification=qualification.strip(),
        address=address.strip(), region_code=region_code.strip() or None,
        contact_person=contact_person.strip(), phone=phone.strip(), email=email.strip(),
    )
    db.add(p); db.commit()
    return RedirectResponse("/admin/providers?success=created", status_code=303)


@router.get("/providers/{provider_id}/edit")
async def provider_edit(provider_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(404)
    regions = db.query(Region).filter(Region.level == "kabupaten").order_by(Region.name).limit(500).all()
    return templates.TemplateResponse(request, "admin/provider_form.html", {
        "title": "Edit Penyedia - CTW",
        "user": user, "provider": provider, "regions": regions,
        "active_page": "providers", "mode": "edit",
    })


@router.post("/providers/{provider_id}/edit")
async def provider_update(
    provider_id: int, request: Request,
    name: str = Form(...), npwp: str = Form(""), siujk_number: str = Form(""),
    classification: str = Form(""), qualification: str = Form(""),
    address: str = Form(""), region_code: str = Form(""),
    contact_person: str = Form(""), phone: str = Form(""), email: str = Form(""),
    csrf_token: str = Form(""),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    p = db.query(Provider).filter(Provider.id == provider_id).first()
    if not p:
        raise HTTPException(404)
    p.name = name.strip(); p.npwp = npwp.strip(); p.siujk_number = siujk_number.strip()
    p.classification = classification.strip(); p.qualification = qualification.strip()
    p.address = address.strip(); p.region_code = region_code.strip() or None
    p.contact_person = contact_person.strip(); p.phone = phone.strip(); p.email = email.strip()
    db.commit()
    return RedirectResponse("/admin/providers?success=updated", status_code=303)


@router.post("/providers/{provider_id}/delete")
async def provider_delete(
    provider_id: int, request: Request,
    csrf_token: str = Form(""),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    p = db.query(Provider).filter(Provider.id == provider_id).first()
    if p:
        db.delete(p); db.commit()
    return RedirectResponse("/admin/providers?success=deleted", status_code=303)


# ============================================================
# BLACKLIST
# ============================================================

@router.get("/blacklist")
async def blacklist_list(request: Request, db: Session = Depends(get_db)):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login?next=/admin/blacklist", status_code=303)
    entries = db.query(Blacklist).order_by(Blacklist.start_date.desc()).all()
    return templates.TemplateResponse(request, "admin/blacklist.html", {
        "title": "Kelola Blacklist - CTW",
        "user": user, "entries": entries, "active_page": "blacklist", "mode": "list",
    })


@router.get("/blacklist/new")
async def blacklist_new(request: Request, db: Session = Depends(get_db)):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    providers = db.query(Provider).order_by(Provider.name).all()
    return templates.TemplateResponse(request, "admin/blacklist_form.html", {
        "title": "Tambah Blacklist - CTW",
        "user": user, "entry": None, "providers": providers,
        "active_page": "blacklist", "mode": "create",
    })


@router.post("/blacklist/new")
async def blacklist_create(
    request: Request,
    provider_id: int = Form(...), reason: str = Form(...),
    category: str = Form("Lainnya"), regulation_ref: str = Form(""),
    decision_by: str = Form(""), decision_number: str = Form(""),
    start_date: str = Form(""), end_date: str = Form(""),
    status: str = Form("Aktif"), document_url: str = Form(""),
    csrf_token: str = Form(""),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    entry = Blacklist(
        provider_id=provider_id, reason=reason.strip(), category=category,
        regulation_ref=regulation_ref.strip(), decision_by=decision_by.strip(),
        decision_number=decision_number.strip(),
        start_date=_parse_date(start_date), end_date=_parse_date(end_date),
        status=status, document_url=document_url.strip(),
    )
    db.add(entry); db.commit()
    return RedirectResponse("/admin/blacklist?success=created", status_code=303)


@router.get("/blacklist/{entry_id}/edit")
async def blacklist_edit(entry_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    entry = db.query(Blacklist).filter(Blacklist.id == entry_id).first()
    if not entry:
        raise HTTPException(404)
    providers = db.query(Provider).order_by(Provider.name).all()
    return templates.TemplateResponse(request, "admin/blacklist_form.html", {
        "title": "Edit Blacklist - CTW",
        "user": user, "entry": entry, "providers": providers,
        "active_page": "blacklist", "mode": "edit",
    })


@router.post("/blacklist/{entry_id}/edit")
async def blacklist_update(
    entry_id: int, request: Request,
    provider_id: int = Form(...), reason: str = Form(...),
    category: str = Form("Lainnya"), regulation_ref: str = Form(""),
    decision_by: str = Form(""), decision_number: str = Form(""),
    start_date: str = Form(""), end_date: str = Form(""),
    status: str = Form("Aktif"), document_url: str = Form(""),
    csrf_token: str = Form(""),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    entry = db.query(Blacklist).filter(Blacklist.id == entry_id).first()
    if not entry:
        raise HTTPException(404)
    entry.provider_id = provider_id; entry.reason = reason.strip()
    entry.category = category; entry.regulation_ref = regulation_ref.strip()
    entry.decision_by = decision_by.strip(); entry.decision_number = decision_number.strip()
    entry.start_date = _parse_date(start_date); entry.end_date = _parse_date(end_date)
    entry.status = status; entry.document_url = document_url.strip()
    db.commit()
    return RedirectResponse("/admin/blacklist?success=updated", status_code=303)


@router.post("/blacklist/{entry_id}/delete")
async def blacklist_delete(
    entry_id: int, request: Request,
    csrf_token: str = Form(""),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    entry = db.query(Blacklist).filter(Blacklist.id == entry_id).first()
    if entry:
        db.delete(entry); db.commit()
    return RedirectResponse("/admin/blacklist?success=deleted", status_code=303)


# ============================================================
# FEEDBACK
# ============================================================

@router.get("/feedback")
async def feedback_list(request: Request, db: Session = Depends(get_db)):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login?next=/admin/feedback", status_code=303)
    items = db.query(Feedback).order_by(Feedback.created_at.desc()).all()
    return templates.TemplateResponse(request, "admin/feedback.html", {
        "title": "Kelola Feedback - CTW",
        "user": user, "items": items, "active_page": "feedback", "mode": "list",
    })


@router.post("/feedback/{item_id}/status")
async def feedback_update_status(
    item_id: int, request: Request,
    status: str = Form(...),
    csrf_token: str = Form(""),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    item = db.query(Feedback).filter(Feedback.id == item_id).first()
    if item:
        item.status = status
        db.commit()
    return RedirectResponse("/admin/feedback?success=updated", status_code=303)

"""Admin: upload & kelola foto dokumentasi proyek."""
import re
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, File, UploadFile, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import PHOTO_DIR, MAX_PHOTO_SIZE_MB, ALLOWED_IMAGE_EXT
from core.database import get_db
from core.models import Project, ProjectPhoto
from core.auth import get_current_user
from core.csrf import verify_csrf
from core.utils import utcnow

router = APIRouter(prefix="/admin", tags=["Admin Photos"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
from core.templating import get_templates
templates = get_templates()


def _require_user(request: Request):
    return get_current_user(request)


def _safe_filename(name: str) -> str:
    name = Path(name).name
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    return name[:100]


@router.get("/projects/{project_id}/photos")
async def project_photos_page(project_id: int, request: Request, db: Session = Depends(get_db)):
    user = _require_user(request)
    if not user:
        return RedirectResponse(f"/admin/login?next=/admin/projects/{project_id}/photos", status_code=303)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404)
    photos = db.query(ProjectPhoto).filter(ProjectPhoto.project_id == project_id).order_by(
        ProjectPhoto.taken_at.desc()
    ).all()
    return templates.TemplateResponse(request, "admin/photos.html", {
        "title": f"Foto Proyek: {project.name}",
        "user": user, "project": project, "photos": photos, "active_page": "projects",
    })


@router.post("/projects/{project_id}/photos/upload")
async def photo_upload(
    project_id: int, request: Request,
    caption: str = Form(""), category: str = Form("progress"),
    photo: UploadFile = File(...),
    csrf_token: str = Form(""),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    user = _require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404)
    ext = Path(photo.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise HTTPException(400, f"Format tidak didukung: {', '.join(sorted(ALLOWED_IMAGE_EXT))}")
    contents = await photo.read()
    size_mb = len(contents) / 1024 / 1024
    if size_mb > MAX_PHOTO_SIZE_MB:
        raise HTTPException(400, f"Ukuran maks {MAX_PHOTO_SIZE_MB} MB")
    project_dir = PHOTO_DIR / str(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(photo.filename)
    timestamp = utcnow().strftime("%Y%m%d%H%M%S")
    final_name = f"{timestamp}_{safe_name}"
    file_path = project_dir / final_name
    with open(file_path, "wb") as f:
        f.write(contents)
    url_path = f"/uploads/photos/{project_id}/{final_name}"
    entry = ProjectPhoto(
        project_id=project_id, file_path=url_path,
        caption=caption.strip() or safe_name, category=category or "progress",
        taken_at=utcnow(),
    )
    db.add(entry); db.commit()
    return RedirectResponse(f"/admin/projects/{project_id}/photos?success=uploaded", status_code=303)


@router.post("/projects/{project_id}/photos/{photo_id}/delete")
async def photo_delete(
    project_id: int, photo_id: int, request: Request,
    csrf_token: str = Form(""),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    user = _require_user(request)
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    photo = db.query(ProjectPhoto).filter(
        ProjectPhoto.id == photo_id, ProjectPhoto.project_id == project_id,
    ).first()
    if not photo:
        raise HTTPException(404)
    if photo.file_path.startswith("/uploads/"):
        relative = photo.file_path.replace("/uploads/", "", 1)
        disk_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "uploads" / relative
        try:
            if disk_path.exists():
                disk_path.unlink()
        except Exception as e:
            print(f"[photo delete] {e}")
    db.delete(photo); db.commit()
    return RedirectResponse(f"/admin/projects/{project_id}/photos?success=deleted", status_code=303)

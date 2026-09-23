"""Route feedback 3 pilar."""
from pathlib import Path
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Feedback, Project
from core.csrf import verify_csrf
from core.rate_limit import limiter
from core.utils import utcnow

router = APIRouter(prefix="/feedback", tags=["Feedback"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
from core.templating import get_templates
templates = get_templates()
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

VALID_TYPES = {"audit", "inspeksi", "publik"}
TYPE_LABEL = {"audit": "Hasil Audit", "inspeksi": "Hasil Inspeksi", "publik": "Laporan Publik"}


@router.get("/")
async def feedback_home(request: Request, db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.name).all()
    recent = db.query(Feedback).order_by(Feedback.created_at.desc()).limit(10).all()
    return templates.TemplateResponse(request, "feedback.html", {
        "title": "Feedback Publik - CTW",
        "projects": projects, "recent_feedbacks": recent, "type_labels": TYPE_LABEL,
    })


@router.post("/submit")
@limiter.limit("10/minute")
async def submit_feedback(
    request: Request,
    project_id: int = Form(...),
    feedback_type: str = Form(...),
    reporter_name: str = Form("Anonim"),
    reporter_contact: str = Form(""),
    title: str = Form(...),
    content: str = Form(...),
    attachment: UploadFile | None = File(None),
    csrf_token: str = Form(""),
    _csrf: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    if feedback_type not in VALID_TYPES:
        raise HTTPException(400, "Tipe tidak valid")
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Proyek tidak ditemukan")
    if len(title.strip()) < 5 or len(content.strip()) < 10:
        raise HTTPException(400, "Judul minimal 5 char, isi minimal 10 char")

    attachment_path = ""
    if attachment and attachment.filename:
        safe = f"{utcnow().strftime('%Y%m%d%H%M%S')}_{attachment.filename}"
        fp = UPLOAD_DIR / safe
        with open(fp, "wb") as f:
            f.write(await attachment.read())
        attachment_path = str(fp)

    db.add(Feedback(
        project_id=project_id, feedback_type=feedback_type,
        reporter_name=reporter_name or "Anonim", reporter_contact=reporter_contact,
        title=title.strip(), content=content.strip(), attachment_path=attachment_path,
    ))
    db.commit()
    return RedirectResponse(url="/feedback/?success=1", status_code=303)

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from sqlalchemy.orm import Session
import secrets

from config import ENABLE_DOCS, IS_PROD, SESSION_SECRET, UPLOAD_DIR
from core.database import init_db, get_db
from core.models import Project
from core.auth import get_current_user
from core.csrf import get_csrf_token
from core.rate_limit import setup_rate_limit, limiter
from server.api.routes import feedback as feedback_router
from server.api.routes import regions as regions_router
from server.api.routes import projects as projects_router
from server.api.routes import providers as providers_router
from server.api.routes import geojson as geojson_router
from server.api.routes import admin as admin_router
from server.api.routes import admin_photos as admin_photos_router
from server.api.routes import observations as observations_router

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifespan (pengganti @app.on_event)."""
    init_db()
    yield


app_kwargs = {
    "title": "Construction Transparency Watch",
    "lifespan": lifespan,
}
if ENABLE_DOCS:
    app_kwargs.update({
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
    })
else:
    app_kwargs.update({
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    })

app = FastAPI(**app_kwargs)

# Rate limiting
setup_rate_limit(app)

# Session middleware
secret = SESSION_SECRET or secrets.token_urlsafe(32)
app.add_middleware(
    SessionMiddleware,
    secret_key=secret,
    session_cookie="ctw_session",
    max_age=86400,
    same_site="lax",
    https_only=IS_PROD,
)

# Static & uploads
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

from core.templating import get_templates
templates = get_templates()

# Expose csrf_token ke SEMUA template


# ==== Routers ====
app.include_router(feedback_router.router)
app.include_router(regions_router.router)
app.include_router(projects_router.router)
app.include_router(providers_router.router)
app.include_router(geojson_router.router)
app.include_router(admin_router.router)
app.include_router(admin_photos_router.router)
app.include_router(observations_router.router)


@app.get("/admin/docs", include_in_schema=False)
async def admin_docs(request: Request):
    user = get_current_user(request)
    if not user:
        return Response(status_code=302, headers={"Location": "/admin/login?next=/admin/docs"})
    return get_swagger_ui_html(
        openapi_url="/admin/openapi.json",
        title="CTW API Docs (Admin)",
    )


@app.get("/admin/openapi.json", include_in_schema=False)
async def admin_openapi(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login dulu")
    return get_openapi(title=app.title, version="0.1.0", routes=app.routes)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "dashboard.html", {
        "title": "Construction Transparency Watch",
    })


@app.get("/api/projects")
@limiter.limit("60/minute")
async def api_projects(request: Request, db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return {
        "projects": [
            {"id": p.id, "name": p.name, "lat": p.latitude, "lng": p.longitude}
            for p in projects
        ]
    }

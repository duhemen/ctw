"""Singleton Jinja2Templates dengan globals CSRF."""
from pathlib import Path
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "server" / "templates"

_instance = None


def get_templates() -> Jinja2Templates:
    """Return singleton Jinja2Templates dengan globals sudah di-set."""
    global _instance
    if _instance is None:
        _instance = Jinja2Templates(directory=TEMPLATES_DIR)
        from core.csrf import get_csrf_token
        _instance.env.globals["get_csrf_token"] = get_csrf_token
    return _instance

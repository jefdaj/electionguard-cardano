from fastapi import Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

TEMPLATES_DIR = str(Path(__file__).resolve().parent / "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

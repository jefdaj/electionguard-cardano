from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from egc_app.server.deps import templates

router = APIRouter(prefix="")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request, name='index.html', context={},
    )

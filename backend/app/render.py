from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .main import app

STATIC_DIR = Path(__file__).resolve().parents[1] / 'static'
ASSETS_DIR = STATIC_DIR / 'assets'

if ASSETS_DIR.exists():
    app.mount('/assets', StaticFiles(directory=ASSETS_DIR), name='assets')


@app.get('/', include_in_schema=False)
def render_index():
    index = STATIC_DIR / 'index.html'
    if not index.exists():
        raise HTTPException(503, 'Frontend não foi compilado')
    return FileResponse(index)


@app.get('/{full_path:path}', include_in_schema=False)
def render_spa(full_path: str):
    if full_path.startswith('api/'):
        raise HTTPException(404, 'Rota não encontrada')
    candidate = (STATIC_DIR / full_path).resolve()
    try:
        candidate.relative_to(STATIC_DIR.resolve())
    except ValueError:
        raise HTTPException(404, 'Arquivo não encontrado')
    if candidate.is_file():
        return FileResponse(candidate)
    index = STATIC_DIR / 'index.html'
    if not index.exists():
        raise HTTPException(503, 'Frontend não foi compilado')
    return FileResponse(index)

import json
import secrets
import time
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, Request, Response, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, text
from . import config as cfg
from .db import get_db, User, Tenant, Session, Document, Chunk, History, Audit, now
from .security import current_user, admin, verify_password, hash_password, token_hash, throttle, audit
from .services import ingest, get_document, visible, remove_document, answer, revalidate, NOT_FOUND

app = FastAPI(title='Busca documental', docs_url='/api/docs' if cfg.MODE == 'demo' else None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=[cfg.ORIGIN], allow_credentials=True, allow_methods=['GET', 'POST', 'DELETE'], allow_headers=['Content-Type'])
DUMMY_PASSWORD = hash_password(secrets.token_urlsafe(32))


class UploadBodyLimit:
    """Cap actual received bytes, including chunked multipart uploads."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        total = 0

        async def limited_receive():
            nonlocal total
            message = await receive()
            if message['type'] == 'http.request':
                total += len(message.get('body', b''))
                if total > cfg.MAX_UPLOAD + 65536:
                    raise HTTPException(413, 'Arquivo excede o limite')
            return message
        await self.app(scope, limited_receive, send)


app.add_middleware(UploadBodyLimit)


@app.middleware('http')
async def security_headers(request: Request, call_next):
    if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'} and request.headers.get('origin') != cfg.ORIGIN:
        return JSONResponse({'detail': 'Origem da requisição não autorizada'}, status_code=403)
    length = request.headers.get('content-length', '0')
    if not length.isdigit() or int(length) > cfg.MAX_UPLOAD + 65536:
        return JSONResponse({'detail': 'Arquivo excede o limite'}, status_code=413)
    response = await call_next(request)
    response.headers.update({'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY', 'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer', 'Content-Security-Policy': "default-src 'none'; frame-ancestors 'none'"})
    return response


@app.get('/api/health')
def health(db=Depends(get_db)):
    db.execute(text('SELECT 1'))
    return {'status': 'ok'}


@app.get('/api/config')
def config():
    return {'demo': cfg.MODE == 'demo', 'search': 'textual demonstrativa' if cfg.PROVIDER == 'none' else 'semântica', 'retention_days': cfg.RETENTION_DAYS}


class Login(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


@app.post('/api/login')
def login(body: Login, request: Request, response: Response, db=Depends(get_db)):
    email = body.email.strip().lower()
    throttle('login-user:' + email, 10, 300)
    throttle('login-ip:' + (request.client.host if request.client else 'unknown'), 60, 300)
    user = db.scalar(select(User).where(User.email == email))
    valid = verify_password(body.password, user.password if user else DUMMY_PASSWORD)
    if not user or not valid:
        db.add(Audit(action='auth.failed'))
        db.commit()
        raise HTTPException(401, 'E-mail ou senha inválidos')
    old = request.cookies.get('session')
    if old:
        db.execute(delete(Session).where(Session.token_hash == token_hash(old)))
    token = secrets.token_urlsafe(32)
    db.add(Session(token_hash=token_hash(token), user_id=user.id, expires_at=now() + timedelta(hours=8)))
    audit(db, user, 'auth.login')
    db.commit()
    response.set_cookie('session', token, httponly=True, secure=cfg.SECURE_COOKIE, samesite='strict', max_age=28800, path='/')
    return {'ok': True}


@app.post('/api/logout')
def logout(request: Request, response: Response, user=Depends(current_user), db=Depends(get_db)):
    db.execute(delete(Session).where(Session.token_hash == token_hash(request.cookies.get('session', ''))))
    audit(db, user, 'auth.logout')
    db.commit()
    response.delete_cookie('session', path='/')
    return {'ok': True}


@app.get('/api/me')
def me(user=Depends(current_user), db=Depends(get_db)):
    return {'email': user.email, 'role': user.role, 'tenant': db.get(Tenant, user.tenant_id).name}


def document_view(doc):
    return {'id': doc.id, 'name': doc.name, 'status': doc.status, 'error': doc.error, 'pages': doc.pages, 'visibility': doc.visibility, 'created_at': doc.created_at, 'expires_at': doc.expires_at}


@app.get('/api/documents')
def documents(user=Depends(current_user), db=Depends(get_db)):
    return [document_view(d) for d in db.scalars(select(Document).where(*visible(user)).order_by(Document.created_at.desc()))]


@app.post('/api/documents')
def upload(file: UploadFile = File(...), visibility: str = Form('team'), user=Depends(admin), db=Depends(get_db)):
    throttle('upload:' + user.id, 20, 300)
    if visibility not in {'team', 'admin'}:
        raise HTTPException(422, 'Visibilidade inválida')
    raw = file.file.read(cfg.MAX_UPLOAD + 1)
    return document_view(ingest(db, user, file.filename or 'documento', raw, visibility))


@app.delete('/api/documents/{doc_id}')
def delete_document(doc_id: str, user=Depends(admin), db=Depends(get_db)):
    remove_document(db, user, get_document(db, user, doc_id))
    return {'ok': True}


@app.get('/api/documents/{doc_id}/source')
def document_source(doc_id: str, page: int = 1, user=Depends(current_user), db=Depends(get_db)):
    doc = get_document(db, user, doc_id)
    if doc.status != 'ready' or page < 1 or page > doc.pages:
        raise HTTPException(404, 'Página indisponível')
    chunks = db.scalars(select(Chunk).where(Chunk.document_id == doc.id, Chunk.tenant_id == user.tenant_id, Chunk.page == page)).all()
    audit(db, user, 'source.opened', doc.id)
    db.commit()
    return {'document': doc.name, 'page': page, 'pages': doc.pages, 'chunks': [{'id': c.id, 'section': c.section, 'text': c.body} for c in chunks]}


@app.get('/api/documents/{doc_id}/download')
def download(doc_id: str, user=Depends(current_user), db=Depends(get_db)):
    from .db import cipher
    doc = get_document(db, user, doc_id)
    path = cfg.STORAGE_DIR / f'{doc.id}.enc'
    if doc.status != 'ready' or not path.exists():
        raise HTTPException(404, 'Arquivo indisponível')
    audit(db, user, 'document.downloaded', doc.id)
    db.commit()
    return Response(cipher.decrypt(path.read_bytes()), media_type='application/octet-stream', headers={'Content-Disposition': f'attachment; filename="documento-{doc.id}{doc.extension}"'})


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    previous_id: str | None = Field(default=None, max_length=40)


@app.post('/api/chat')
def chat(body: Question, user=Depends(current_user), db=Depends(get_db)):
    throttle('chat:' + user.id, 30, 60)
    start = time.perf_counter()
    try:
        payload = answer(db, user, body.question.strip(), body.previous_id)
    except HTTPException:
        raise
    except Exception:
        audit(db, user, 'chat.provider_failed')
        db.commit()
        raise HTTPException(503, 'Serviço de busca indisponível. Nenhuma resposta foi gerada; tente novamente.')
    payload['elapsed_ms'] = round((time.perf_counter() - start) * 1000)
    item = History(tenant_id=user.tenant_id, user_id=user.id, question=body.question, payload=json.dumps(payload, ensure_ascii=False))
    db.add(item)
    audit(db, user, 'chat.answered' if payload['found'] else 'chat.no_evidence')
    db.commit()
    return {**payload, 'id': item.id}


@app.get('/api/history')
def history(user=Depends(current_user), db=Depends(get_db)):
    output = []
    for item in db.scalars(select(History).where(History.user_id == user.id, History.tenant_id == user.tenant_id, History.created_at > now() - timedelta(days=cfg.RETENTION_DAYS)).order_by(History.created_at.desc()).limit(100)):
        payload = json.loads(item.payload)
        sources = revalidate(db, user, payload['sources'])
        # Never expose cached answers when one of their source permissions disappears.
        if len(sources) != len(payload['sources']):
            continue
        output.append({'id': item.id, 'question': item.question, 'created_at': item.created_at, **payload})
    return output


@app.delete('/api/history')
def clear_history(user=Depends(current_user), db=Depends(get_db)):
    db.execute(delete(History).where(History.user_id == user.id, History.tenant_id == user.tenant_id))
    audit(db, user, 'history.deleted')
    db.commit()
    return {'ok': True}


@app.get('/api/audit')
def logs(user=Depends(admin), db=Depends(get_db)):
    return [{'id': a.id, 'action': a.action, 'user_id': a.user_id, 'target_id': a.target_id, 'created_at': a.created_at} for a in db.scalars(select(Audit).where(Audit.tenant_id == user.tenant_id).order_by(Audit.created_at.desc()).limit(200))]

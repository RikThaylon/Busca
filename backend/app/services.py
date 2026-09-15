import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from datetime import timedelta
from pathlib import Path
from sqlalchemy import select, delete, func, cast
from sqlalchemy.exc import IntegrityError
from pgvector.sqlalchemy import Vector
from fastapi import HTTPException
from . import config as cfg, providers
from .db import Document, Chunk, History, now, uid, cipher
from .security import audit

NOT_FOUND = 'NÃO ENCONTREI EVIDÊNCIA SUFICIENTE'


def visible(user):
    conditions = [Document.tenant_id == user.tenant_id, Document.expires_at > now()]
    if user.role != 'admin':
        conditions.append(Document.visibility == 'team')
    return conditions


def get_document(db, user, doc_id):
    doc = db.scalar(select(Document).where(Document.id == doc_id, *visible(user)))
    if not doc:
        raise HTTPException(404, 'Documento não encontrado ou sem permissão')
    return doc


def ingest(db, user, filename, raw, visibility='team'):
    extension = Path(filename).suffix.lower()
    if extension not in {'.pdf', '.txt'} or not raw or len(raw) > cfg.MAX_UPLOAD:
        raise HTTPException(422, 'Envie PDF textual ou TXT UTF-8, até 10 MB')
    digest = hashlib.sha256(raw).hexdigest()
    if db.scalar(select(Document).where(Document.tenant_id == user.tenant_id, Document.digest == digest)):
        raise HTTPException(409, 'Documento já cadastrado. Exclua a versão anterior para substituí-la.')
    if db.scalar(select(func.count()).select_from(Document).where(Document.tenant_id == user.tenant_id)) >= 100:
        raise HTTPException(422, 'Limite do piloto: 100 documentos por organização')
    doc = Document(id=uid(), tenant_id=user.tenant_id, name=Path(filename).name[:180], extension=extension,
                   digest=digest, visibility=visibility, expires_at=now() + timedelta(days=cfg.RETENTION_DAYS), embedding_profile=providers.profile())
    db.add(doc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Documento já cadastrado nesta organização')
    path = cfg.STORAGE_DIR / f'{doc.id}.enc'
    try:
        with path.open('wb') as f:
            f.write(cipher.encrypt(raw))
        path.chmod(0o600)
        parsed = subprocess.run([sys.executable, '-m', 'app.parser', extension], input=raw, capture_output=True, timeout=20, check=False)
        if parsed.returncode:
            raise ValueError('Documento recusado pelo extrator')
        result = json.loads(parsed.stdout)
        for start in range(0, len(result['chunks']), 16):
            batch = result['chunks'][start:start + 16]
            vectors = providers.embed([c['body'] for c in batch])
            for chunk, vector in zip(batch, vectors):
                db.add(Chunk(document_id=doc.id, tenant_id=user.tenant_id, embedding=vector, **chunk))
        doc.pages = result['pages']
        doc.status = 'ready'
        audit(db, user, 'document.processed', doc.id)
        db.commit()
    except Exception:
        db.rollback()
        doc = db.get(Document, doc.id)
        doc.status = 'error'
        doc.error = 'Falha de processamento. Verifique PDF/TXT pesquisável (até 100 páginas) e a disponibilidade do provedor. Exclua e envie novamente.'
        path.unlink(missing_ok=True)
        audit(db, user, 'document.failed', doc.id)
        db.commit()
    return doc


def remove_document(db, user, doc):
    # Redact complete affected exchanges, including quotes and repeated evidence.
    for item in db.scalars(select(History).where(History.tenant_id == user.tenant_id)):
        if any(s['document_id'] == doc.id for s in json.loads(item.payload)['sources']):
            db.delete(item)
    db.execute(delete(Chunk).where(Chunk.document_id == doc.id, Chunk.tenant_id == user.tenant_id))
    audit(db, user, 'document.deleted', doc.id)
    db.delete(doc)
    db.commit()
    # DB access disappears first. CLI cleanup removes orphan files after a crash.
    (cfg.STORAGE_DIR / f'{doc.id}.enc').unlink(missing_ok=True)


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.lower()) if not unicodedata.combining(c))


STOP = set('a o as os de da do das dos e em um uma para por com que qual quais quem quando como deve ser realizado realizada procedimento caso sobre ao na no nas nos esta isso onde escrito me diga favor por gentileza'.split())


def terms(text):
    return {t for t in re.findall(r'[a-z0-9]+', normalized(text)) if len(t) > 2 and t not in STOP}


def source(chunk, doc, excerpt=None):
    return {'chunk_id': chunk.id, 'document_id': doc.id, 'document': doc.name, 'page': chunk.page,
            'section': chunk.section, 'excerpt': excerpt or chunk.body,
            'url': f'/api/documents/{doc.id}/source?page={chunk.page}'}


def retrieve(db, user, question):
    stmt = select(Chunk, Document).join(Document, Document.id == Chunk.document_id).where(
        *visible(user), Document.status == 'ready', Chunk.tenant_id == user.tenant_id,
        Document.embedding_profile == providers.profile())
    if cfg.PROVIDER != 'none':
        q = question
        if 'qwen3' in cfg.EMBED_MODEL.lower():
            q = 'Instruct: Given a question in Portuguese, retrieve relevant corporate document passages that answer it.\nQuery: ' + question
        vector = providers.embed([q])[0]
        if db.bind.dialect.name != 'postgresql':
            raise HTTPException(503, 'Busca semântica requer PostgreSQL/pgvector')
        distance = cast(Chunk.embedding, Vector(cfg.EMBED_DIM)).cosine_distance(vector)
        rows = db.execute(stmt.where(Chunk.embedding.is_not(None), distance <= 1 - cfg.MIN_SIMILARITY).order_by(distance).limit(5)).all()
        return [source(c, d) for c, d in rows]
    # Explicit lexical demo baseline. It is NOT an embedding or semantic model.
    query = terms(question)
    if not query:
        return []
    scored = []
    for chunk, doc in db.execute(stmt):
        overlap = query & terms(chunk.body)
        score = len(overlap) / len(query)
        if overlap and score >= 0.60:
            scored.append((score, chunk, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [source(c, d) for _, c, d in scored[:3]]


def revalidate(db, user, sources):
    valid = []
    for s in sources:
        row = db.execute(select(Chunk, Document).join(Document, Chunk.document_id == Document.id).where(
            Chunk.id == s['chunk_id'], Chunk.tenant_id == user.tenant_id, *visible(user), Document.status == 'ready')).first()
        if row and s['excerpt'] in row[0].body:
            valid.append(source(*row, excerpt=s['excerpt']))
    return valid


def answer(db, user, question, previous_id=None):
    text = normalized(question).strip(' ?.!')
    if text in {'e onde esta escrito isso', 'onde esta escrito isso', 'mostre a fonte', 'onde esta a evidencia'}:
        prior = db.scalar(select(History).where(History.id == previous_id, History.user_id == user.id, History.tenant_id == user.tenant_id)) if previous_id else None
        sources = revalidate(db, user, json.loads(prior.payload)['sources']) if prior else []
    else:
        candidates = retrieve(db, user, question)
        sources = providers.select_evidence(question, candidates) if candidates else []
        sources = revalidate(db, user, sources)
    return {'answer': '\n\n'.join(s['excerpt'] for s in sources) if sources else NOT_FOUND,
            'sources': sources, 'found': bool(sources), 'mode': 'semantic-extractive' if cfg.PROVIDER != 'none' else 'lexical-demo'}

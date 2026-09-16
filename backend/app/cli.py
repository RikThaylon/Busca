import argparse
import getpass
import os
from datetime import timedelta
from pathlib import Path
from sqlalchemy import select, text, delete
from . import config as cfg
from .db import Base, engine, SessionLocal, Tenant, User, Document, History, Audit, Session, Throttle, now
from .security import hash_password
from .services import ingest, remove_document


def init():
    if engine.dialect.name == 'postgresql':
        with engine.begin() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
    Base.metadata.create_all(engine)


def demo():
    if cfg.MODE != 'demo':
        raise RuntimeError('Seed fictício bloqueado fora do modo demo')
    init()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == 'demo@busca.local'))
        if not user:
            tenant = Tenant(name='Aurora Componentes • empresa fictícia')
            db.add(tenant)
            db.flush()
            user = User(tenant_id=tenant.id, email='demo@busca.local', role='admin', password=hash_password('Demo-Ficticia-2026!'))
            db.add(user)
            db.add(User(tenant_id=tenant.id, email='leitor@busca.local', role='reader', password=hash_password('Demo-Leitor-2026!')))
            db.commit()
        root = Path(__file__).resolve().parents[2] / 'demo'
        if not root.exists():
            root = Path('/demo')
        for path in sorted(root.glob('*.txt')):
            from fastapi import HTTPException
            try:
                doc = ingest(db, user, path.name, path.read_bytes())
                print(path.name, doc.status)
            except HTTPException as exc:
                if exc.status_code != 409:
                    raise


def create_user(args):
    init()
    password = os.getenv('BOOTSTRAP_PASSWORD') or getpass.getpass('Senha (mínimo 12 caracteres): ')
    if len(password) < 12:
        raise ValueError('Use uma senha de pelo menos 12 caracteres')
    with SessionLocal() as db:
        tenant = db.scalar(select(Tenant).where(Tenant.name == args.tenant))
        if not tenant:
            tenant = Tenant(name=args.tenant)
            db.add(tenant)
            db.flush()
        user = db.scalar(select(User).where(User.email == args.email.lower()))
        if user:
            raise ValueError('Usuário já existe')
        db.add(User(tenant_id=tenant.id, email=args.email.lower(), role=args.role, password=hash_password(password)))
        db.commit()


def cleanup():
    with SessionLocal() as db:
        for doc in db.scalars(select(Document).where(Document.expires_at <= now())).all():
            actor = db.scalar(select(User).where(User.tenant_id == doc.tenant_id, User.role == 'admin'))
            remove_document(db, actor, doc)
        for model, column in [(History, History.created_at), (Audit, Audit.created_at), (Throttle, Throttle.starts_at)]:
            db.execute(delete(model).where(column < now() - timedelta(days=cfg.RETENTION_DAYS)))
        db.execute(delete(Session).where(Session.expires_at <= now()))
        for doc in db.scalars(select(Document).where(Document.status == 'processing', Document.created_at < now() - timedelta(hours=1))):
            doc.status = 'error'
            doc.error = 'Processamento interrompido. Exclua e envie novamente.'
        db.commit()
        active = set(db.scalars(select(Document.id).where(Document.status.in_(['ready', 'processing']))))
        for path in cfg.STORAGE_DIR.glob('*.enc'):
            if path.stem not in active:
                path.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ['init', 'demo', 'cleanup']:
        commands.add_parser(name)
    user = commands.add_parser('create-user')
    user.add_argument('--tenant', required=True)
    user.add_argument('--email', required=True)
    user.add_argument('--role', choices=['admin', 'reader'], default='reader')
    args = parser.parse_args()
    {'init': init, 'demo': demo, 'cleanup': cleanup, 'create-user': lambda: create_user(args)}[args.command]()

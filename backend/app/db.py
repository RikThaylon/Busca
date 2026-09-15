import os
import uuid
from datetime import datetime, timezone
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, String, Text, ForeignKey, DateTime, Integer, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.types import TypeDecorator
from sqlalchemy import JSON
from pgvector.sqlalchemy import Vector
from . import config as cfg


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def uid():
    return str(uuid.uuid4())


key = os.getenv('STORAGE_KEY')
if not key:
    if cfg.MODE == 'pilot':
        raise RuntimeError('STORAGE_KEY é obrigatória no piloto; guardar fora do banco')
    key_path = cfg.DATA_DIR / 'demo.key'
    if not key_path.exists():
        try:
            fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as f:
                f.write(Fernet.generate_key())
        except FileExistsError:
            pass
    key = key_path.read_bytes()
cipher = Fernet(key)


class EncryptedText(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return cipher.encrypt(value.encode()).decode() if value is not None else None

    def process_result_value(self, value, dialect):
        return cipher.decrypt(value.encode()).decode() if value is not None else None


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = 'tenants'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str]


class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey('tenants.id'), index=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default='reader')


class Session(Base):
    __tablename__ = 'sessions'
    token_hash: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class Document(Base):
    __tablename__ = 'documents'
    __table_args__ = (UniqueConstraint('tenant_id', 'digest'),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey('tenants.id'), index=True)
    name: Mapped[str] = mapped_column(EncryptedText)
    digest: Mapped[str] = mapped_column(String)
    extension: Mapped[str] = mapped_column(String)
    visibility: Mapped[str] = mapped_column(String, default='team')
    status: Mapped[str] = mapped_column(String, default='processing')
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    pages: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    embedding_profile: Mapped[str] = mapped_column(String)


class Chunk(Base):
    __tablename__ = 'chunks'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    document_id: Mapped[str] = mapped_column(ForeignKey('documents.id'), index=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey('tenants.id'), index=True)
    page: Mapped[int]
    section: Mapped[str] = mapped_column(EncryptedText)
    body: Mapped[str] = mapped_column(EncryptedText)
    embedding: Mapped[list | None] = mapped_column(JSON().with_variant(Vector(cfg.EMBED_DIM), 'postgresql'), nullable=True)


class History(Base):
    __tablename__ = 'history'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey('tenants.id'), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    question: Mapped[str] = mapped_column(EncryptedText)
    payload: Mapped[str] = mapped_column(EncryptedText)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Audit(Base):
    __tablename__ = 'audit'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    tenant_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str]
    target_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Throttle(Base):
    __tablename__ = 'throttles'
    key: Mapped[str] = mapped_column(String, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=1)
    starts_at: Mapped[datetime] = mapped_column(DateTime, default=now)


engine = create_engine(cfg.DATABASE_URL, **({'connect_args': {'check_same_thread': False}} if cfg.DATABASE_URL.startswith('sqlite') else {'pool_pre_ping': True}))
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        yield db

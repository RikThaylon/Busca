import hashlib
import hmac
import secrets
from datetime import timedelta
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select, update
from .db import SessionLocal, Session, User, Throttle, now, get_db, Audit


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return salt.hex() + ':' + digest.hex()


def verify_password(password, stored):
    salt, digest = stored.split(':')
    check = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
    return hmac.compare_digest(check.hex(), digest)


def token_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def current_user(request: Request, db=Depends(get_db)):
    session = db.get(Session, token_hash(request.cookies.get('session', '')))
    if not session or session.expires_at <= now():
        raise HTTPException(401, 'Sua sessão expirou. Entre novamente.')
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, 'Sessão inválida')
    return user


def admin(user=Depends(current_user)):
    if user.role != 'admin':
        raise HTTPException(403, 'Somente administradores podem realizar esta ação')
    return user


def throttle(key, limit, seconds):
    # Atomic update prevents concurrent requests from bypassing the quota.
    from sqlalchemy.exc import IntegrityError
    key = token_hash(key)
    with SessionLocal() as db:
        row = db.get(Throttle, key)
        if not row:
            db.add(Throttle(key=key, count=0))
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
        db.execute(update(Throttle).where(Throttle.key == key, Throttle.starts_at < now() - timedelta(seconds=seconds)).values(count=0, starts_at=now()))
        result = db.execute(update(Throttle).where(Throttle.key == key, Throttle.count < limit).values(count=Throttle.count + 1))
        db.commit()
        if not result.rowcount:
            raise HTTPException(429, 'Limite temporário atingido. Tente novamente em alguns minutos.')


def audit(db, user, action, target=None):
    db.add(Audit(tenant_id=user.tenant_id, user_id=user.id, action=action, target_id=target))

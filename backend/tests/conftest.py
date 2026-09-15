import os
import tempfile
from pathlib import Path
import pytest

temp = tempfile.TemporaryDirectory()
os.environ.update(APP_MODE='demo', AI_PROVIDER='none', CHAT_MODEL='', DATA_DIR=temp.name,
                  DATABASE_URL=os.getenv('TEST_DATABASE_URL', f'sqlite:///{temp.name}/test.db'),
                  APP_ORIGIN='http://localhost:5173', EMBED_DIM='1024')

from app.db import Base, SessionLocal, engine, Tenant, User
from app.cli import init
from app.security import hash_password
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def database():
    Base.metadata.drop_all(engine)
    init()
    with SessionLocal() as db:
        for name in ['Aurora', 'Outra']:
            tenant = Tenant(name=name)
            db.add(tenant)
            db.flush()
            for role in ['admin', 'reader']:
                db.add(User(tenant_id=tenant.id, email=f'{role}@{name.lower()}.local', role=role, password=hash_password('Senha-De-Teste-123!')))
        db.commit()
    yield


@pytest.fixture
def client():
    with TestClient(app, headers={'Origin':'http://localhost:5173'}) as c:
        yield c


def login(client, role='admin', tenant='aurora'):
    response = client.post('/api/login', json={'email':f'{role}@{tenant}.local','password':'Senha-De-Teste-123!'})
    assert response.status_code == 200, response.text


@pytest.fixture
def corpus(client):
    login(client)
    root = Path(__file__).resolve().parents[2] / 'demo'
    result = []
    for path in root.glob('*.txt'):
        res = client.post('/api/documents', files={'file':(path.name,path.read_bytes(),'text/plain')})
        assert res.status_code == 200, res.text
        assert res.json()['status'] == 'ready', res.text
        result.append(res.json())
    return result

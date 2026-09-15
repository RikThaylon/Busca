import json
from datetime import timedelta
from sqlalchemy import select, text
from app import config as cfg, providers
from app.db import SessionLocal, Document, Chunk, History, now, engine
from conftest import login


def test_demo_questions_sources_and_followup(client, corpus):
    for question, expected in [
        ('Quem aprova compras superiores a R$ 10.000?', 'diretor financeiro'),
        ('Qual procedimento deve ser realizado em caso de acidente?', 'brigada'),
        ('Qual é a periodicidade da manutenção preventiva?', '30 dias'),
    ]:
        result = client.post('/api/chat', json={'question':question})
        assert result.status_code == 200, result.text
        body=result.json()
        assert body['found'] and expected in body['answer']
        assert body['sources'][0]['page'] == 2
        s=body['sources'][0]
        page=client.get(s['url']).json()
        assert any(s['excerpt'] in c['text'] for c in page['chunks'])
        followup=client.post('/api/chat', json={'question':'E onde está escrito isso?','previous_id':body['id']}).json()
        assert followup['sources'] == body['sources']
    assert len(client.get('/api/history').json()) == 6


def test_no_evidence_and_no_followup_context(client, corpus):
    for q in ['Qual é a senha do banco de dados?', 'Qual a receita de bolo de cenoura?', 'Qual é a política de reembolso de passagens?', 'E onde está escrito isso?']:
        body=client.post('/api/chat',json={'question':q}).json()
        assert not body['found'] and not body['sources'], q


def test_tenant_boundary_every_surface(client, corpus):
    answer=client.post('/api/chat',json={'question':'Quem aprova compras superiores a R$ 10.000?'}).json()
    doc_id=answer['sources'][0]['document_id']
    login(client, tenant='outra')
    assert client.get('/api/documents').json() == []
    assert client.get('/api/history').json() == []
    for route in ['source','download']:
        assert client.get(f'/api/documents/{doc_id}/{route}').status_code == 404
    assert client.delete(f'/api/documents/{doc_id}').status_code == 404
    assert not client.post('/api/chat',json={'question':'E onde está escrito isso?','previous_id':answer['id']}).json()['found']
    assert not client.post('/api/chat',json={'question':'Quem aprova compras superiores a R$ 10.000?'}).json()['found']


def test_reader_permissions_and_document_acl(client):
    login(client)
    doc=client.post('/api/documents',data={'visibility':'admin'},files={'file':('restrito.txt','A senha interna reservada é SEGREDO-DE-TESTE. Não divulgar.','text/plain')}).json()
    login(client, role='reader')
    assert client.get('/api/documents').json()==[]
    assert client.get(f"/api/documents/{doc['id']}/source").status_code==404
    assert client.get(f"/api/documents/{doc['id']}/download").status_code==404
    assert client.get('/api/audit').status_code==403
    assert client.delete(f"/api/documents/{doc['id']}").status_code==403
    assert client.post('/api/documents',files={'file':('a.txt',b'test')}).status_code==403
    assert not client.post('/api/chat',json={'question':'Qual é a senha interna reservada?'}).json()['found']


def test_delete_purges_source_chunks_and_cached_answers(client, corpus):
    result=client.post('/api/chat',json={'question':'Quem aprova compras superiores a R$ 10.000?'}).json()
    source=result['sources'][0]
    doc_id=source['document_id']
    assert client.delete(f'/api/documents/{doc_id}').status_code==200
    assert not (cfg.STORAGE_DIR/f'{doc_id}.enc').exists()
    assert client.get(source['url']).status_code==404
    assert client.get('/api/history').json()==[]
    assert not client.post('/api/chat',json={'question':'E onde está escrito isso?','previous_id':result['id']}).json()['found']
    with SessionLocal() as db:
        assert db.scalar(select(Chunk).where(Chunk.document_id==doc_id)) is None


def test_auth_logout_origin_and_rate_limit(client):
    assert client.get('/api/documents').status_code==401
    assert client.post('/api/login',headers={'Origin':'https://evil.example'},json={'email':'admin@aurora.local','password':'Senha-De-Teste-123!'}).status_code==403
    login(client)
    assert 'HttpOnly' in client.post('/api/login',json={'email':'admin@aurora.local','password':'Senha-De-Teste-123!'}).headers['set-cookie']
    client.post('/api/logout')
    assert client.get('/api/me').status_code==401
    for _ in range(10):
        assert client.post('/api/login',json={'email':'unknown@example.test','password':'wrong'}).status_code==401
    assert client.post('/api/login',json={'email':'unknown@example.test','password':'wrong'}).status_code==429


def test_untrusted_and_unsupported_files(client):
    login(client)
    assert client.post('/api/documents',files={'file':('script.html',b'<script>evil()</script>')}).status_code==422
    assert client.post('/api/documents',files={'file':('too-big.txt',b'x'*(cfg.MAX_UPLOAD+1))}).status_code==422
    result=client.post('/api/documents',files={'file':('fake.pdf',b'not a pdf')}).json()
    assert result['status']=='error'
    assert not (cfg.STORAGE_DIR/f"{result['id']}.enc").exists()
    assert client.get(f"/api/documents/{result['id']}/download").status_code==404


def test_encrypted_storage_and_expiration(client, corpus):
    body=client.post('/api/chat',json={'question':'Quem aprova compras superiores a R$ 10.000?'}).json()
    with engine.connect() as conn:
        for row in conn.execute(text('SELECT body FROM chunks')):
            assert row[0].startswith('gAAAA') and 'financeiro' not in row[0]
        assert conn.execute(text('SELECT payload FROM history')).first()[0].startswith('gAAAA')
    with SessionLocal() as db:
        doc=db.get(Document,body['sources'][0]['document_id'])
        doc.expires_at=now()-timedelta(seconds=1)
        db.commit()
    assert client.get(body['sources'][0]['url']).status_code==404
    assert client.get('/api/history').json()==[]


def test_llm_fabrication_is_rejected(monkeypatch):
    monkeypatch.setattr(cfg,'PROVIDER','ollama')
    monkeypatch.setattr(cfg,'CHAT_MODEL','qwen3:4b')
    monkeypatch.setattr(providers,'request_api',lambda *args: {'message':{'content':json.dumps({'evidence':[{'id':'a','quote':'Uma resposta completamente inventada pelo modelo.'}]})}})
    assert providers.select_evidence('pergunta',[{'chunk_id':'a','excerpt':'O diretor financeiro aprova a compra.'}])==[]


def test_llm_cannot_remove_qualifiers(monkeypatch):
    monkeypatch.setattr(cfg,'PROVIDER','ollama')
    monkeypatch.setattr(cfg,'CHAT_MODEL','qwen3:4b')
    fragment='compras são aprovadas automaticamente'
    monkeypatch.setattr(providers,'request_api',lambda *args: {'message':{'content':json.dumps({'evidence':[{'id':'a','quote':fragment}]})}})
    assert providers.select_evidence('pergunta',[{'chunk_id':'a','excerpt':'É falso que compras são aprovadas automaticamente.'}])==[]


def test_provider_outage_is_not_reported_as_absent_evidence(client, corpus, monkeypatch):
    monkeypatch.setattr(cfg,'PROVIDER','ollama')
    def fail(*args):
        raise RuntimeError('upstream unavailable')
    monkeypatch.setattr(providers,'embed',fail)
    response=client.post('/api/chat',json={'question':'Quem aprova compras superiores a R$ 10.000?'})
    assert response.status_code==503
    assert client.get('/api/history').json()==[]


def test_postgres_vector_acl_before_retrieval(client, monkeypatch):
    import pytest
    if engine.dialect.name!='postgresql':
        pytest.skip('Requires TEST_DATABASE_URL pointing to PostgreSQL/pgvector')
    monkeypatch.setattr(cfg,'PROVIDER','ollama')
    monkeypatch.setattr(providers,'embed',lambda texts:[[1.0]+[0.0]*1023 for _ in texts])
    login(client)
    doc=client.post('/api/documents',files={'file':('vetor.txt','O diretor financeiro aprova a compra especial.','text/plain')}).json()
    assert doc['status']=='ready'
    assert client.post('/api/chat',json={'question':'Quem aprova a compra especial?'}).json()['found']
    login(client,tenant='outra')
    assert not client.post('/api/chat',json={'question':'Quem aprova a compra especial?'}).json()['found']

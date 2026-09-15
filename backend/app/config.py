import os
from pathlib import Path

MODE = os.getenv('APP_MODE', 'demo')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data/demo.db')
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR = DATA_DIR / 'files'
STORAGE_DIR.mkdir(exist_ok=True)
ORIGIN = os.getenv('APP_ORIGIN', 'http://localhost:5173').rstrip('/')
SECURE_COOKIE = os.getenv('SECURE_COOKIE', 'false').lower() == 'true'
MAX_UPLOAD = 10 * 1024 * 1024
RETENTION_DAYS = int(os.getenv('RETENTION_DAYS', '30'))
PROVIDER = os.getenv('AI_PROVIDER', 'none')  # none, openai, azure, ollama
API_BASE = os.getenv('AI_BASE_URL', '').rstrip('/')
API_KEY = os.getenv('AI_API_KEY', '')
EMBED_MODEL = os.getenv('EMBED_MODEL', '')
CHAT_MODEL = os.getenv('CHAT_MODEL', '')
EMBED_DIM = int(os.getenv('EMBED_DIM', '1024'))
MIN_SIMILARITY = float(os.getenv('MIN_SIMILARITY', '0.55'))
EXTERNAL_AI_APPROVED = os.getenv('EXTERNAL_AI_APPROVED', 'false').lower() == 'true'

if MODE not in {'demo', 'pilot'} or PROVIDER not in {'none', 'openai', 'azure', 'ollama'}:
    raise RuntimeError('APP_MODE ou AI_PROVIDER inválido')
if MODE == 'pilot':
    if not DATABASE_URL.startswith('postgresql') or PROVIDER == 'none':
        raise RuntimeError('Piloto requer PostgreSQL e provedor de embeddings real')
    if not SECURE_COOKIE or not ORIGIN.startswith('https://'):
        raise RuntimeError('Piloto requer HTTPS e SECURE_COOKIE=true')
if PROVIDER != 'none' and (not API_BASE or not EMBED_MODEL):
    raise RuntimeError('Configure AI_BASE_URL e EMBED_MODEL')
if PROVIDER in {'openai', 'azure'} and not EXTERNAL_AI_APPROVED:
    raise RuntimeError('Autorize contratualmente o provedor antes de habilitar envio externo')
if RETENTION_DAYS < 1 or RETENTION_DAYS > 365 or EMBED_DIM < 1 or EMBED_DIM > 4096 or not 0 < MIN_SIMILARITY <= 1:
    raise RuntimeError('Retenção, dimensão ou limiar fora dos limites aceitos')

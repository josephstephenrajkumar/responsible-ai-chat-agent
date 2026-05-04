import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / '.env'
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

class Settings:
    PROJECT_NAME = 'Responsible AI Chat Agent'
    API_PREFIX = '/api'
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
    GROQ_API_URL = os.getenv('GROQ_API_URL', 'https://api.groq.com/openai/v1')
    LANGFUSE_PUBLIC_KEY = os.getenv('LANGFUSE_PUBLIC_KEY', '')
    LANGFUSE_SECRET_KEY = os.getenv('LANGFUSE_SECRET_KEY', '')
    LANGFUSE_HOST = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
    OTEL_SERVICE_NAME = os.getenv('OTEL_SERVICE_NAME', 'responsible-ai-chat-agent')
    JAEGER_HOST = os.getenv('JAEGER_HOST', 'localhost')
    JAEGER_PORT = int(os.getenv('JAEGER_PORT', '6831'))
    JAEGER_ENDPOINT = os.getenv('JAEGER_ENDPOINT', '')
    JAEGER_UI_URL = os.getenv('JAEGER_UI_URL', 'http://localhost:16686')
    DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR / 'storage' / 'responsible_ai.db'}")
    FRONTEND_ORIGINS = [
        'http://localhost:5173',
        'http://localhost:5174',
        'http://localhost:5175',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5174',
        'http://127.0.0.1:5175'
    ]
    POLICY_PATH = BASE_DIR / 'storage' / 'policy_config.json'
    AUDIT_LOG_PATH = BASE_DIR / 'storage' / 'audit_log.jsonl'

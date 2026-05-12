import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, create_engine, desc, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app.config import Settings
from app.telemetry import tracer

Base = declarative_base()

engine_kwargs = {}
if Settings.DATABASE_URL.startswith('sqlite'):
    engine_kwargs['connect_args'] = {'check_same_thread': False}

engine = create_engine(Settings.DATABASE_URL, future=True, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class PolicyConfig(Base):
    __tablename__ = 'policy_configs'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), unique=True, nullable=False, default='active')
    payload = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditEventRecord(Base):
    __tablename__ = 'audit_events'

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(80), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    mode = Column(String(40), nullable=False)
    model = Column(String(160), nullable=False)
    provider = Column(String(80), nullable=False)
    is_cached = Column(Boolean, nullable=False, default=False)
    summary = Column(Text, nullable=False, default='')
    responsible_ai = Column(Text, nullable=False, default='{}')


class SafetyPolicy(Base):
    __tablename__ = 'safety_policies'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(160), nullable=False)
    category = Column(String(120), nullable=False, index=True)
    severity = Column(String(40), nullable=False, default='medium')
    description = Column(Text, nullable=False, default='')
    policy_kind = Column(String(40), nullable=False, default='regex', index=True)
    status = Column(String(40), nullable=False, default='draft', index=True)
    enabled = Column(Boolean, nullable=False, default=True)
    version = Column(Integer, nullable=False, default=1)
    source = Column(String(160), nullable=False, default='local')
    approved_by = Column(String(120), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    activated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    patterns = relationship('SafetyPolicyPattern', back_populates='policy', cascade='all, delete-orphan')
    hub_validators = relationship('SafetyPolicyHubValidator', back_populates='policy', cascade='all, delete-orphan')


class SafetyPolicyPattern(Base):
    __tablename__ = 'safety_policy_patterns'

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey('safety_policies.id', ondelete='CASCADE'), nullable=False, index=True)
    pattern = Column(Text, nullable=False)
    label = Column(String(160), nullable=False, default='')
    is_case_sensitive = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    policy = relationship('SafetyPolicy', back_populates='patterns')


class SafetyPolicyHubValidator(Base):
    __tablename__ = 'safety_policy_hub_validators'

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey('safety_policies.id', ondelete='CASCADE'), nullable=False, index=True)
    hub_uri = Column(String(240), nullable=False)
    validator_class = Column(String(160), nullable=False)
    install_local_models = Column(Boolean, nullable=False, default=False)
    runtime_params = Column(Text, nullable=False, default='{}')
    metadata_json = Column('metadata', Text, nullable=False, default='{}')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    policy = relationship('SafetyPolicy', back_populates='hub_validators')


class PolicyAuditEvent(Base):
    __tablename__ = 'policy_audit_events'

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey('safety_policies.id', ondelete='SET NULL'), nullable=True, index=True)
    action = Column(String(80), nullable=False, index=True)
    actor = Column(String(120), nullable=False, default='system')
    event_hash = Column(String(64), nullable=False, index=True)
    details = Column(Text, nullable=False, default='{}')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class RuntimePolicyDecision(Base):
    __tablename__ = 'runtime_policy_decisions'

    id = Column(Integer, primary_key=True, index=True)
    input_hash = Column(String(64), nullable=False, index=True)
    stage = Column(String(40), nullable=False, default='input')
    blocked = Column(Boolean, nullable=False, default=False)
    risk_level = Column(String(40), nullable=False, default='low')
    matched_categories = Column(Text, nullable=False, default='[]')
    matched_patterns = Column(Text, nullable=False, default='[]')
    policy_version = Column(String(120), nullable=False, default='none')
    validator_engine = Column(String(120), nullable=False, default='regex_fallback')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


def default_policy() -> Dict[str, Any]:
    return {
        'provider': 'groq',
        'model': Settings.GROQ_MODEL,
        'allowed_modes': ['code', 'framework'],
        'privacy_filters': ['pii', 'sensitive_data'],
        'audit_retention_days': 30,
        'observability': {
            'opentelemetry': True,
            'jaeger_ui': Settings.JAEGER_UI_URL,
            'langfuse_framework_mode': True
        }
    }


def _loads_json(value: str, fallback: Any) -> Any:
    try:
        return json.loads(value) if value else fallback
    except json.JSONDecodeError:
        return fallback


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=None)
        except ValueError:
            return datetime.utcnow()
    return datetime.utcnow()


def _load_policy_seed() -> Dict[str, Any]:
    if Settings.POLICY_PATH.exists():
        try:
            return json.loads(Settings.POLICY_PATH.read_text())
        except json.JSONDecodeError:
            return default_policy()
    return default_policy()


def _load_audit_seed() -> List[Dict[str, Any]]:
    if not Settings.AUDIT_LOG_PATH.exists():
        return []

    events = []
    for line in Settings.AUDIT_LOG_PATH.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def init_database() -> Dict[str, Any]:
    Settings.POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)

    with tracer.start_as_current_span('db.init') as span:
        Base.metadata.create_all(bind=engine)
        with engine.begin() as connection:
            existing_policy_columns = {
                row[1]
                for row in connection.execute(text("PRAGMA table_info(safety_policies)")).fetchall()
            }
            if 'policy_kind' not in existing_policy_columns:
                connection.execute(text(
                    "ALTER TABLE safety_policies ADD COLUMN policy_kind VARCHAR(40) NOT NULL DEFAULT 'regex'"
                ))
        migrated_audit_events = 0

        with SessionLocal() as session:
            policy = session.query(PolicyConfig).filter_by(name='active').one_or_none()
            if policy is None:
                session.add(PolicyConfig(name='active', payload=json.dumps(_load_policy_seed())))

            for event in _load_audit_seed():
                request_id = event.get('request_id')
                if not request_id:
                    continue
                exists = session.query(AuditEventRecord).filter_by(request_id=request_id).first()
                if exists:
                    continue
                session.add(AuditEventRecord(
                    request_id=request_id,
                    timestamp=_parse_timestamp(event.get('timestamp')),
                    mode=str(event.get('mode', 'code')),
                    model=str(event.get('model', Settings.GROQ_MODEL)),
                    provider=str(event.get('provider', 'unknown')),
                    is_cached=bool(event.get('is_cached', False)),
                    summary=str(event.get('summary', '')),
                    responsible_ai=json.dumps(event.get('responsible_ai', {}))
                ))
                migrated_audit_events += 1

            session.commit()

        span.set_attribute('db.system', 'sqlite' if Settings.DATABASE_URL.startswith('sqlite') else 'sqlalchemy')
        span.set_attribute('db.migrated_audit_events', migrated_audit_events)
        return {'status': 'ready', 'migrated_audit_events': migrated_audit_events}


def get_policy_payload() -> Dict[str, Any]:
    with tracer.start_as_current_span('db.policy.get'):
        with SessionLocal() as session:
            policy = session.query(PolicyConfig).filter_by(name='active').one_or_none()
            if policy is None:
                return default_policy()
            return _loads_json(policy.payload, default_policy())


def append_audit_event(event: Dict[str, Any]) -> None:
    with tracer.start_as_current_span('audit_insert') as span:
        with SessionLocal() as session:
            record = AuditEventRecord(
                request_id=event['request_id'],
                timestamp=_parse_timestamp(event.get('timestamp')),
                mode=str(event.get('mode', 'code')),
                model=str(event.get('model', Settings.GROQ_MODEL)),
                provider=str(event.get('provider', 'unknown')),
                is_cached=bool(event.get('is_cached', False)),
                summary=str(event.get('summary', '')),
                responsible_ai=json.dumps(event.get('responsible_ai', {}))
            )
            session.add(record)
            try:
                session.commit()
            except SQLAlchemyError:
                session.rollback()
                raise
        span.set_attribute('audit.request_id', event['request_id'])


def hash_text(value: str) -> str:
    return hashlib.sha256((value or '').encode('utf-8')).hexdigest()


def get_recent_audit_events(limit: int = 25) -> List[Dict[str, Any]]:
    with tracer.start_as_current_span('db.audit.list') as span:
        safe_limit = max(1, min(limit, 100))
        with SessionLocal() as session:
            records = (
                session.query(AuditEventRecord)
                .order_by(desc(AuditEventRecord.timestamp), desc(AuditEventRecord.id))
                .limit(safe_limit)
                .all()
            )
        span.set_attribute('audit.limit', safe_limit)
        return [
            {
                'request_id': record.request_id,
                'timestamp': record.timestamp.isoformat() + 'Z',
                'mode': record.mode,
                'model': record.model,
                'provider': record.provider,
                'is_cached': record.is_cached,
                'summary': record.summary,
                'responsible_ai': _loads_json(record.responsible_ai, {})
            }
            for record in records
        ]

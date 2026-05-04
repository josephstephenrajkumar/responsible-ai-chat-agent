import json
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.database import append_audit_event, engine, get_policy_payload, get_recent_audit_events, init_database
from app.schemas import ChatRequest, ChatResponse, ResponsibleAIResponse, MetadataResponse, AuditEvent, PolicyResponse
from app.groq_client import groq_client
from app.responsible_ai import (
    evaluate_privacy as code_privacy,
    evaluate_safety as code_safety,
    evaluate_fairness as code_fairness,
    evaluate_explainability as code_explainability,
    evaluate_verifiability as code_verifiability,
    evaluate_transparency as code_transparency,
    evaluate_governance as code_governance,
    evaluate_controllability as code_controllability
)
from app.framework_mode import (
    evaluate_observability,
    trace_llm_call,
    evaluate_privacy as framework_privacy,
    evaluate_safety as framework_safety,
    evaluate_explainability as framework_explainability,
    evaluate_fairness as framework_fairness
)
from app.telemetry import get_tracing_status, instrument_sqlalchemy, setup_tracing, tracer

app = FastAPI(title=Settings.PROJECT_NAME, version='0.1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=Settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
    allow_headers=['Content-Type', 'Authorization', 'Accept', 'Origin'],
    expose_headers=['*'],
    max_age=3600
)


@app.on_event('startup')
def startup_event():
    setup_tracing(app)
    instrument_sqlalchemy(engine)
    init_database()


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'responsible-ai-chat-agent'}


@app.get('/')
def root():
    return {
        'service': 'responsible-ai-chat-agent',
        'status': 'ok',
        'links': {
            'health': '/health',
            'observability': '/observability',
            'policy': '/policy',
            'audit': '/audit',
            'docs': '/docs'
        }
    }


@app.get('/observability')
def observability():
    return get_tracing_status()


@app.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest):
    with tracer.start_as_current_span('/chat') as span:
        span.set_attribute('chat.mode', request.mode.value)
        span.set_attribute('chat.model', request.model)
        span.set_attribute('chat.temperature', request.temperature)
        span.set_attribute('chat.max_tokens', request.max_tokens)

        with tracer.start_as_current_span('groq_api_call') as groq_span:
            response = groq_client.send_prompt(
                request.message,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                explain=request.explain,
                verify=request.verify,
                mode=request.mode.value
            )
            groq_span.set_attribute('llm.provider', response.get('provider', 'unknown'))
            groq_span.set_attribute('llm.model', response.get('model', request.model))
            groq_span.set_attribute('llm.request_id', response.get('request_id', ''))
        answer = response.get('answer', '')

        if request.mode == 'framework':
            with tracer.start_as_current_span('observability_check'):
                observability_info = evaluate_observability(request.message)
            with tracer.start_as_current_span('privacy_check'):
                privacy_result = framework_privacy(request.message)
            with tracer.start_as_current_span('safety_check'):
                safety_result = framework_safety(request.message)
            with tracer.start_as_current_span('fairness_check'):
                fairness_result = framework_fairness(answer)
            with tracer.start_as_current_span('explainability_check'):
                explainability_result = framework_explainability(answer)
            with tracer.start_as_current_span('verifiability_check'):
                verifiability_result = {
                    'verifiability_score': 0.8,
                    'recommendation': 'Use open-source audits when available'
                }
            with tracer.start_as_current_span('transparency_check'):
                transparency_result = {
                    'transparency_level': 'high' if observability_info.get('observability') == 'enabled' else 'partial',
                    'recommendation': observability_info.get('recommendation', 'Capture and expose trace metadata')
                }
            with tracer.start_as_current_span('governance_check'):
                governance_result = {
                    'governance_concern': 'medium',
                    'recommendation': 'Enable policy enforcement with frameworks'
                }
            with tracer.start_as_current_span('controllability_check'):
                controllability_result = {
                    'controllability_properties': ['mode', 'temperature', 'max_tokens'],
                    'recommendation': 'Keep explicit controls'
                }
        else:
            with tracer.start_as_current_span('privacy_check'):
                privacy_result = code_privacy(request.message)
            with tracer.start_as_current_span('safety_check'):
                safety_result = code_safety(request.message)
            with tracer.start_as_current_span('fairness_check'):
                fairness_result = code_fairness(request.message, answer)
            with tracer.start_as_current_span('explainability_check'):
                explainability_result = code_explainability(answer)
            with tracer.start_as_current_span('verifiability_check'):
                verifiability_result = code_verifiability(answer)
            with tracer.start_as_current_span('transparency_check'):
                transparency_result = code_transparency(answer)
            with tracer.start_as_current_span('governance_check'):
                governance_result = code_governance(request.message)
            with tracer.start_as_current_span('controllability_check'):
                controllability_result = code_controllability(request.message)

        responsible_ai = ResponsibleAIResponse(
            privacy=privacy_result,
            safety=safety_result,
            fairness=fairness_result,
            explainability=explainability_result,
            verifiability=verifiability_result,
            transparency=transparency_result,
            governance=governance_result,
            controllability=controllability_result
        )

        if request.mode == 'framework':
            with tracer.start_as_current_span('langfuse_trace_flush'):
                trace_llm_call(
                    response.get('request_id', ''),
                    {
                        'message': request.message,
                        'model': request.model,
                        'temperature': request.temperature,
                        'max_tokens': request.max_tokens,
                        'mode': request.mode.value
                    },
                    {
                        'answer': answer,
                        'provider': response.get('provider', ''),
                        'model': response.get('model', ''),
                        'timestamp': response.get('timestamp', ''),
                        'metadata': response.get('metadata', {})
                    }
                )

        with tracer.start_as_current_span('response_metadata'):
            metadata = MetadataResponse(
                model=request.model,
                provider=response.get('provider', 'groq'),
                mode=request.mode,
                request_id=response.get('request_id', ''),
                timestamp=(
                    datetime.fromisoformat(response.get('timestamp').replace('Z', '+00:00'))
                    if response.get('timestamp')
                    else datetime.utcnow()
                )
            )

        audit = AuditEvent(
            request_id=metadata.request_id,
            timestamp=metadata.timestamp,
            mode=request.mode,
            model=request.model,
            provider=metadata.provider,
            is_cached=False,
            summary=answer[:120],
            responsible_ai=responsible_ai.dict() if hasattr(responsible_ai, 'dict') else responsible_ai
        )

        append_audit_event(json.loads(audit.json()))

        with tracer.start_as_current_span('response_sent') as response_span:
            response_span.set_attribute('chat.request_id', metadata.request_id)
            response_span.set_attribute('chat.provider', metadata.provider)
            return ChatResponse(answer=answer, responsible_ai=responsible_ai, metadata=metadata)


@app.get('/audit')
def audit():
    return {'events': get_recent_audit_events()}


@app.get('/policy', response_model=PolicyResponse)
def policy():
    return PolicyResponse(policy=get_policy_payload())

import os
import json
import uuid
from datetime import datetime
try:
    import httpx
except ImportError:
    httpx = None

from app.config import Settings
from app.framework_mode.langfuse_observability import (
    is_langfuse_configured,
    langfuse_observe,
    update_current_llm_trace
)

SYSTEM_PROMPT = '''You are a responsible AI assistant.
Follow these rules:
- Be accurate and honest.
- Say when you are uncertain.
- Do not expose private data.
- Avoid harmful, biased, or discriminatory content.
- Explain reasoning at a high level when requested.
'''

class GroqClient:
    def __init__(self):
        self.api_key = Settings.GROQ_API_KEY
        self.model = Settings.GROQ_MODEL
        self.base_url = Settings.GROQ_API_URL

    def send_prompt(self, message, temperature=0.2, max_tokens=800, explain=True, verify=True, mode='code'):
        if mode == 'framework' and is_langfuse_configured():
            return self._send_prompt_observed(
                message,
                temperature=temperature,
                max_tokens=max_tokens,
                explain=explain,
                verify=verify,
                mode=mode
            )

        return self._send_prompt(
            message,
            temperature=temperature,
            max_tokens=max_tokens,
            explain=explain,
            verify=verify,
            mode=mode
        )

    @langfuse_observe(name='groq_completion', as_type='generation')
    def _send_prompt_observed(self, message, temperature=0.2, max_tokens=800, explain=True, verify=True, mode='framework'):
        response = self._send_prompt(
            message,
            temperature=temperature,
            max_tokens=max_tokens,
            explain=explain,
            verify=verify,
            mode=mode
        )
        update_current_llm_trace(
            response.get('request_id', ''),
            {
                'message': message,
                'model': self.model,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'mode': mode,
                'explain': explain,
                'verify': verify
            },
            {
                'answer': response.get('answer', ''),
                'provider': response.get('provider', ''),
                'model': response.get('model', ''),
                'timestamp': response.get('timestamp', ''),
                'metadata': response.get('metadata', {})
            }
        )
        return response

    def _send_prompt(self, message, temperature=0.2, max_tokens=800, explain=True, verify=True, mode='code'):
        if not self.api_key or httpx is None:
            answer = (f'Unable to reach Groq API because GROQ_API_KEY is missing or httpx is not installed. '
                      'Here is a responsible fallback answer: ' + message)
            return {
                'answer': answer,
                'provider': 'groq-fallback',
                'model': self.model,
                'request_id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'tokens': 0,
                'notes': 'fallback path used'
            }

        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': message}
            ],
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        try:
            response = httpx.post(f'{self.base_url}/chat/completions', headers=headers, json=payload, timeout=25.0)
            response.raise_for_status()
            data = response.json()
            answer = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            usage = data.get('usage', {})

            return {
                'answer': answer,
                'provider': 'groq',
                'model': self.model,
                'request_id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'tokens': usage.get('total_tokens', 0),
                'metadata': data
            }
        except Exception as exc:
            return {
                'answer': f'Groq API request failed: {exc}',
                'provider': 'groq-error',
                'model': self.model,
                'request_id': str(uuid.uuid4()),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'tokens': 0,
                'metadata': {'error': str(exc)}
            }

groq_client = GroqClient()

import re
import warnings
from functools import lru_cache

warnings.filterwarnings(
    'ignore',
    message='Could not obtain an event loop. Falling back to synchronous validation.',
    category=UserWarning,
    module='guardrails.validator_service'
)

try:
    from guardrails import Guard, OnFailAction
    from guardrails.settings import settings as guardrails_settings
    from guardrails.validator_base import Validator, register_validator
    from guardrails.validators import FailResult, PassResult

    guardrails_settings.disable_tracing = True
    if guardrails_settings.rc:
        guardrails_settings.rc.enable_metrics = False
        guardrails_settings.rc.use_remote_inferencing = False

    _guardrails_available = True
except ImportError:
    Guard = None
    OnFailAction = None
    Validator = object
    FailResult = None
    PassResult = None
    register_validator = None
    _guardrails_available = False


_SAFETY_POLICIES = [
    {
        'category': 'violence_or_harm',
        'severity': 'high',
        'patterns': [
            r'\bkill\b',
            r'\bharm\b',
            r'\bpoison\b',
            r'\battack\b',
            r'\bmake\s+(?:a\s+)?bomb\b',
        ],
    },
    {
        'category': 'cyber_abuse',
        'severity': 'high',
        'patterns': [
            r'\bexploit\b',
            r'\bmalware\b',
            r'\bransomware\b',
            r'\bcredential\s*(?:theft|stealing|harvesting)\b',
            r'\bbypass\s+(?:mfa|2fa|authentication|login)\b',
        ],
    },
    {
        'category': 'fraud_or_phishing',
        'severity': 'high',
        'patterns': [
            r'\b(?:create|build|write|send|launch|run)\s+(?:a\s+)?phishing\b',
            r'\bphishing\s+(?:kit|page|site|email|message|campaign|template)\b',
            r'\bspoof(?:ing)?\s+(?:a\s+)?(?:bank|payment|login|website|email)\b',
            r'\b(?:run|create|build)\s+(?:a\s+)?scam\b',
            r'\bfake\s+(?:invoice|bank|payment|login|website)\b',
            r'\bsteal\s+(?:money|credentials|passwords?|card|account)\b',
        ],
    },
    {
        'category': 'money_laundering',
        'severity': 'high',
        'patterns': [
            r'\bmoney\s+launder(?:ing)?\b',
            r'\blayer(?:ing)?\s+transactions\b',
            r'\bstructure\s+(?:cash\s+)?deposits\b',
            r'\bavoid\s+(?:aml|kyc|sanctions|transaction\s+monitoring)\b',
        ],
    },
    {
        'category': 'unsafe_financial_action',
        'severity': 'medium',
        'patterns': [
            r'\bexecute\s+(?:a\s+)?(?:wire|transfer|payment|trade|transaction)\b',
            r'\bapprove\s+(?:this\s+)?(?:loan|payment|wire|transaction)\b',
            r'\bwithout\s+human\s+approval\b',
        ],
    },
]

_COMPILED_POLICIES = [
    {
        **policy,
        'compiled_patterns': [re.compile(pattern, re.IGNORECASE) for pattern in policy['patterns']],
    }
    for policy in _SAFETY_POLICIES
]


def _detect_violations(text):
    text = text or ''
    violations = []

    for policy in _COMPILED_POLICIES:
        matched_terms = []
        for pattern in policy['compiled_patterns']:
            matched_terms.extend(match.group(0) for match in pattern.finditer(text))

        if matched_terms:
            violations.append({
                'category': policy['category'],
                'severity': policy['severity'],
                'matches': sorted(set(matched_terms), key=str.lower),
            })

    return violations


def _risk_for(violations):
    if any(item['severity'] == 'high' for item in violations):
        return 'high'
    if violations:
        return 'medium'
    return 'low'


if _guardrails_available:
    @register_validator(name='responsible_ai/safety_policy', data_type='string')
    class ResponsibleAISafetyPolicy(Validator):
        def _validate(self, value, metadata):
            violations = _detect_violations(value)
            if violations:
                categories = ', '.join(item['category'] for item in violations)
                return FailResult(
                    errorMessage=f'Unsafe content matched safety policy: {categories}',
                    metadata={'violations': violations}
                )

            return PassResult(metadata={'violations': []})


@lru_cache(maxsize=1)
def _get_guardrails_safety_guard():
    if not _guardrails_available:
        return None, 'guardrails-ai is not installed'

    try:
        guard = Guard()
        guard.configure(allow_metrics_collection=False)
        return guard.use(ResponsibleAISafetyPolicy(on_fail=OnFailAction.NOOP)), None
    except Exception as exc:
        return None, str(exc)


def evaluate_safety(message, stage='input'):
    message = message or ''
    violations = _detect_violations(message)
    risk = _risk_for(violations)
    guard, setup_error = _get_guardrails_safety_guard()

    validation_passed = risk == 'low'
    validation_summaries = []
    engine = 'guardrails_ai'

    if guard:
        try:
            outcome = guard.validate(message, metadata={'stage': stage})
            validation_passed = bool(outcome.validation_passed)
            validation_summaries = [
                {
                    'validator_name': summary.validator_name,
                    'validator_status': summary.validator_status,
                    'failure_reason': summary.failure_reason,
                    'property_path': summary.property_path,
                }
                for summary in outcome.validation_summaries
            ]
        except Exception as exc:
            setup_error = str(exc)
            engine = 'guardrails_ai_with_regex_fallback'
    else:
        engine = 'regex_fallback'

    blocked = not validation_passed or risk == 'high'
    categories = [item['category'] for item in violations]

    return {
        'safety_engine': engine,
        'safety_stage': stage,
        'safety_risk': risk,
        'validation_passed': validation_passed,
        'blocked': blocked,
        'violations': categories,
        'policy_violations': violations,
        'validation_summaries': validation_summaries,
        'setup_error': setup_error,
        'recommendation': (
            'Block this request and route to human review'
            if blocked
            else 'Guardrails AI safety policy passed'
        )
    }

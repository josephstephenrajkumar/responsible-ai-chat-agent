def evaluate_privacy(message):
    sensitive_terms = ['password', 'ssn', 'credit card', 'secret', 'private']
    detected = [term for term in sensitive_terms if term in message.lower()]
    return {
        'privacy_risk': 'high' if detected else 'low',
        'detected_sensitive_terms': detected,
        'recommendation': 'Apply PII detection before generating the answer'
    }

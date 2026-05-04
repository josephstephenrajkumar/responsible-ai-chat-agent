def evaluate_safety(message):
    unsafe_patterns = ['harm', 'attack', 'kill', 'exploit', 'poison']
    detected = [term for term in unsafe_patterns if term in message.lower()]
    return {
        'safety_risk': 'high' if detected else 'low',
        'violations': detected,
        'recommendation': 'Use safety rules to block unsafe content'
    }

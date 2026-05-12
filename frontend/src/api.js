const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export async function sendChat(payload) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  return response.json()
}

export async function fetchPolicy() {
  const response = await fetch(`${API_BASE}/policy`)
  return response.json()
}

export async function fetchObservability() {
  const response = await fetch(`${API_BASE}/observability`)
  return response.json()
}

export async function fetchPolicies() {
  const response = await fetch(`${API_BASE}/policies`)
  return response.json()
}

export async function createPolicy(payload) {
  const response = await fetch(`${API_BASE}/policies`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  return response.json()
}

export async function importHubPolicy(payload) {
  const response = await fetch(`${API_BASE}/policies/import/hub`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: payload.name,
      category: payload.category,
      severity: payload.severity,
      description: payload.description,
      source: payload.source,
      hub_validator: payload.hub_validators[0]
    })
  })
  return response.json()
}

export async function fetchHubValidators() {
  const response = await fetch(`${API_BASE}/policies/hub/validators`)
  return response.json()
}

export async function installHubValidator(payload) {
  const response = await fetch(`${API_BASE}/policies/hub/validators/install`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  return response.json()
}

export async function updatePolicy(id, payload) {
  const response = await fetch(`${API_BASE}/policies/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  return response.json()
}

export async function deletePolicy(id) {
  const response = await fetch(`${API_BASE}/policies/${id}`, { method: 'DELETE' })
  return response.json()
}

export async function approvePolicy(id) {
  const response = await fetch(`${API_BASE}/policies/${id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actor: 'policy-manager' })
  })
  return response.json()
}

export async function activatePolicy(id) {
  const response = await fetch(`${API_BASE}/policies/${id}/activate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actor: 'policy-manager' })
  })
  return response.json()
}

export async function reloadPolicies() {
  const response = await fetch(`${API_BASE}/policies/reload`, { method: 'POST' })
  return response.json()
}

export async function testPolicies(message) {
  const response = await fetch(`${API_BASE}/policies/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  })
  return response.json()
}

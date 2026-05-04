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

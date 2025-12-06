const API_BASE = import.meta.env.DEV ? '' : '';

export async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`);
  return response.json();
}

export async function loadTools() {
  const response = await fetch(`${API_BASE}/api/tools`);
  return response.json();
}

export async function sendChatMessage(query, sessionId = '') {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      session_id: sessionId,
      context: ''
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '请求失败');
  }

  return response.json();
}


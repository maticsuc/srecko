export interface ChatSource {
  tool: string;
  query: string;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

export async function sendMessage(message: string): Promise<ChatResponse> {
  const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
  const res = await fetch(`${basePath}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

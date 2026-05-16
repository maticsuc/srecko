export interface ChatSource {
  tool: string;
  query: string;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

export interface GameTextPart {
  type: "text";
  text: string;
}

export interface GameBlankPart {
  type: "blank";
  blankId: string;
  answer: string;
}

export type GameLinePart = GameTextPart | GameBlankPart;

export interface GameWord {
  blankId: string;
  word: string;
}

export interface GameRound {
  id: number;
  title: string;
  category: string;
  url: string | null;
  lines: GameLinePart[][];
  words: GameWord[];
}

export async function sendMessage(message: string): Promise<ChatResponse> {
  const res = await fetch("/api/chat", {
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

export async function fetchGameRound(): Promise<GameRound> {
  const res = await fetch("/api/game/round", {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

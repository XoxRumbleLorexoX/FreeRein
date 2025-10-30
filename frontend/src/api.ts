export type ChatResponse = {
  reply: string;
  sources: string[];
  meta: Record<string, unknown>;
};

export async function chat(message: string, mode: string): Promise<ChatResponse> {
  const response = await fetch("/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message, mode }),
  });
  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.statusText}`);
  }
  return response.json();
}

export async function getHealth() {
  const response = await fetch("/health");
  if (!response.ok) {
    throw new Error("Failed to fetch health");
  }
  return response.json();
}

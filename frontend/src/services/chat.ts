import { getToken } from './auth';

const API_URL = 'http://localhost:8000/api/v1';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  id?: string; // optional for rendering keys
}

export async function sendMessage(
  message: string,
  callbacks: {
    onChunk: (chunk: string) => void;
    onComplete: () => void;
    onError: (error: Error) => void;
  },
  model?: string,
  signal?: AbortSignal
): Promise<void> {
  const token = getToken();
  if (!token) {
    callbacks.onError(new Error('Not authenticated'));
    return;
  }

  try {
    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ message, model }),
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Chat failed: ${response.status} ${errorText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No response body');
    }

    // Read the stream
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      callbacks.onChunk(chunk);
    }
    callbacks.onComplete();
  } catch (error) {
    if (error instanceof Error) {
      callbacks.onError(error);
    } else {
      callbacks.onError(new Error(String(error)));
    }
  }
}
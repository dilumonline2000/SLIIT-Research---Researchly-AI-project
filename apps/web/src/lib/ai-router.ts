import {
  startGeneralChatSession,
  startModuleChatSession,
  sendMessageStreaming,
  type GenerativeChat,
} from './gemini';
import { useAIProviderStore, type AIProvider } from '@/stores/aiProviderStore';

export type ChatMode = 'general' | 'integrity' | 'collaboration' | 'dataManagement' | 'analytics';

export interface AISession {
  sendMessage: (
    message: string,
    onChunk: (chunk: string) => void,
    onDone: (fullText: string) => void,
    onError: (error: string) => void
  ) => Promise<void>;
  provider: AIProvider;
  mode: ChatMode;
}

export async function createAISession(mode: ChatMode, contextData?: string): Promise<AISession> {
  const { provider } = useAIProviderStore.getState();

  if (provider === 'gemini') {
    return createGeminiSession(mode, contextData);
  } else {
    return createLocalSession(mode, contextData);
  }
}

async function createGeminiSession(mode: ChatMode, contextData?: string): Promise<AISession> {
  const chat =
    mode === 'general'
      ? await startGeneralChatSession()
      : await startModuleChatSession(mode, contextData);

  return {
    provider: 'gemini',
    mode,
    sendMessage: async (message, onChunk, onDone, onError) => {
      try {
        let fullText = '';
        await sendMessageStreaming(
          chat,
          message,
          (chunk) => {
            fullText += chunk;
            onChunk(chunk);
          },
          () => onDone(fullText)
        );
      } catch (err: any) {
        onError(err?.message ?? 'Gemini API error');
      }
    },
  };
}

async function createLocalSession(mode: ChatMode, contextData?: string): Promise<AISession> {
  const capturedContext = contextData;

  return {
    provider: 'local',
    mode,
    sendMessage: async (message, onChunk, onDone, onError) => {
      try {
        const gatewayUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:3001';
        const response = await fetch(`${gatewayUrl}/api/v1/ai/local/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            mode,
            message,
            context: capturedContext ?? null,
          }),
        });

        if (!response.ok) {
          throw new Error(`Local model error: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        if (!reader) throw new Error('No response body');

        let fullText = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const raw = decoder.decode(value);
          const lines = raw.split('\n');

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const payload = line.slice(6).trim();
            if (payload === '[DONE]') {
              onDone(fullText);
              return;
            }
            fullText += payload;
            onChunk(payload);
          }
        }
        onDone(fullText);
      } catch (err: any) {
        onError(err?.message ?? 'Local model error');
      }
    },
  };
}

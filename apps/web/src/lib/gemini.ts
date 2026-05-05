import { GoogleGenerativeAI } from '@google/generative-ai';

const apiKey = process.env.NEXT_PUBLIC_GEMINI_API_KEY;
if (!apiKey) {
  console.error('NEXT_PUBLIC_GEMINI_API_KEY not set');
}

const genAI = new GoogleGenerativeAI(apiKey ?? '');

export interface GenerativeChat {
  sendMessage: (message: string) => Promise<string>;
  stream: (message: string, onChunk: (chunk: string) => void) => Promise<void>;
}

// gemini-2.0-flash is the current stable model (1.5-flash removed from v1beta API).
const MODEL_ID = 'gemini-2.0-flash';

/** Parse "Please retry in X.XXXs." from a 429 error body and return ms to wait. */
function parseRetryDelay(msg: string): number {
  const m = msg.match(/retry in (\d+(?:\.\d+)?)s/i);
  if (m) return Math.ceil(parseFloat(m[1]) * 1000) + 500; // add 500ms buffer
  return 15000; // default 15 s
}

/** Wait ms milliseconds. */
const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

/** Wrap a Gemini call with one automatic retry on 429 rate-limit. */
async function withRateLimitRetry<T>(fn: () => Promise<T>): Promise<T> {
  try {
    return await fn();
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    if (msg.includes('429') || msg.toLowerCase().includes('quota')) {
      const delay = parseRetryDelay(msg);
      console.warn(`[Gemini] Rate limited — retrying in ${delay}ms…`);
      await sleep(delay);
      return await fn(); // one more attempt
    }
    throw err;
  }
}

function makeChat(rawChat: ReturnType<ReturnType<typeof genAI.getGenerativeModel>['startChat']>): GenerativeChat {
  return {
    sendMessage: async (message: string) => {
      const result = await withRateLimitRetry(() => rawChat.sendMessage(message));
      return result.response.text();
    },
    stream: async (message: string, onChunk: (chunk: string) => void) => {
      const stream = await withRateLimitRetry(() => rawChat.sendMessageStream(message));
      for await (const chunk of stream.stream) {
        const text = chunk.text();
        if (text) onChunk(text);
      }
    },
  };
}

export async function startGeneralChatSession(): Promise<GenerativeChat> {
  const model = genAI.getGenerativeModel({ model: MODEL_ID });
  const rawChat = model.startChat({
    history: [],
    generationConfig: { maxOutputTokens: 2048, temperature: 0.7 },
  });
  return makeChat(rawChat);
}

export async function startModuleChatSession(
  module: string,
  contextData?: string
): Promise<GenerativeChat> {
  const model = genAI.getGenerativeModel({ model: MODEL_ID });

  const systemPrompt =
    module === 'integrity'
      ? 'You are an expert in research paper integrity analysis. Help users with citation parsing, gap analysis, and proposal generation.'
      : module === 'collaboration'
      ? 'You are an expert research advisor helping with supervisor matching, peer connections, and feedback analysis.'
      : module === 'dataManagement'
      ? 'You are a data scientist helping with research data management, categorization, and summarization.'
      : module === 'analytics'
      ? 'You are a research analytics expert providing insights on trends, quality, and success predictions.'
      : 'You are a helpful research assistant.';

  const history: Array<{ role: 'user' | 'model'; parts: Array<{ text: string }> }> = contextData
    ? [
        { role: 'user', parts: [{ text: `Context: ${contextData}` }] },
        { role: 'model', parts: [{ text: 'I have received the context. Ready to help.' }] },
      ]
    : [];

  const rawChat = model.startChat({
    history,
    generationConfig: { maxOutputTokens: 2048, temperature: 0.7 },
    systemInstruction: systemPrompt,
  });
  return makeChat(rawChat);
}

export async function sendMessageStreaming(
  chat: GenerativeChat,
  message: string,
  onChunk: (chunk: string) => void,
  onDone: () => void
): Promise<void> {
  await chat.stream(message, onChunk);
  onDone();
}

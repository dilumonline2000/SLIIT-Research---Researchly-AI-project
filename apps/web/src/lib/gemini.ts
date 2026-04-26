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

const MODEL_ID = 'gemini-1.5-flash';

export async function startGeneralChatSession(): Promise<GenerativeChat> {
  const model = genAI.getGenerativeModel({ model: MODEL_ID });
  const chat = model.startChat({
    history: [],
    generationConfig: {
      maxOutputTokens: 2048,
      temperature: 0.7,
    },
  });

  return {
    sendMessage: async (message: string) => {
      const result = await chat.sendMessage(message);
      return result.response.text();
    },
    stream: async (message: string, onChunk: (chunk: string) => void) => {
      const stream = await chat.sendMessageStream(message);
      for await (const chunk of stream.stream) {
        const text = chunk.text();
        if (text) onChunk(text);
      }
    },
  };
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
        {
          role: 'user',
          parts: [{ text: `Context: ${contextData}` }],
        },
        {
          role: 'model',
          parts: [{ text: 'I have received the context. Ready to help with your questions.' }],
        },
      ]
    : [];

  const chat = model.startChat({
    history,
    generationConfig: {
      maxOutputTokens: 2048,
      temperature: 0.7,
    },
    systemInstruction: systemPrompt,
  });

  return {
    sendMessage: async (message: string) => {
      const result = await chat.sendMessage(message);
      return result.response.text();
    },
    stream: async (message: string, onChunk: (chunk: string) => void) => {
      const stream = await chat.sendMessageStream(message);
      for await (const chunk of stream.stream) {
        const text = chunk.text();
        if (text) onChunk(text);
      }
    },
  };
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

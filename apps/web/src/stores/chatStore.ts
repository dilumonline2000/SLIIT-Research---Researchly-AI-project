import { create } from "zustand";

export interface ChatCitation {
  paper_id: string | null;
  paper_title: string | null;
  section: string | null;
  score: number | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  detected_language?: string | null;
  response_language?: string | null;
  citations?: ChatCitation[] | null;
  created_at?: string;
}

export interface ChatSession {
  id: string;
  title: string | null;
  session_type: string;
  paper_ids: string[];
  preferred_language: string;
  message_count: number;
  created_at?: string;
  updated_at?: string;
}

interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  messages: ChatMessage[];
  sending: boolean;
  setSessions: (s: ChatSession[]) => void;
  upsertSession: (s: ChatSession) => void;
  removeSession: (id: string) => void;
  setActive: (id: string | null) => void;
  setMessages: (m: ChatMessage[]) => void;
  appendMessage: (m: ChatMessage) => void;
  setSending: (v: boolean) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  sessions: [],
  activeSessionId: null,
  messages: [],
  sending: false,
  setSessions: (sessions) => set({ sessions }),
  upsertSession: (session) =>
    set((state) => {
      const idx = state.sessions.findIndex((s) => s.id === session.id);
      if (idx === -1) return { sessions: [session, ...state.sessions] };
      const next = [...state.sessions];
      next[idx] = { ...next[idx], ...session };
      return { sessions: next };
    }),
  removeSession: (id) =>
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== id),
      activeSessionId: state.activeSessionId === id ? null : state.activeSessionId,
    })),
  setActive: (id) => set({ activeSessionId: id }),
  setMessages: (messages) => set({ messages }),
  appendMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setSending: (sending) => set({ sending }),
}));

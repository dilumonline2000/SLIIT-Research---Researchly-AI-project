"use client";

import { useCallback } from "react";
import { apiGet, apiPost, apiDelete, apiPatch } from "@/lib/api";
import { API_ROUTES } from "@/lib/constants";
import {
  useChatStore,
  type ChatMessage,
  type ChatSession,
} from "@/stores/chatStore";

interface ListSessionsResponse {
  sessions: ChatSession[];
  count: number;
}

interface SessionDetailResponse {
  session: ChatSession;
  messages: ChatMessage[];
}

export function useChat() {
  const {
    sessions,
    activeSessionId,
    messages,
    sending,
    setSessions,
    upsertSession,
    removeSession,
    setActive,
    setMessages,
    appendMessage,
    setSending,
  } = useChatStore();

  const loadSessions = useCallback(async () => {
    const data = await apiGet<ListSessionsResponse>(API_ROUTES.chat.sessions);
    setSessions(data.sessions || []);
  }, [setSessions]);

  const createSession = useCallback(
    async (input: {
      title?: string;
      paper_ids: string[];
      preferred_language?: string;
      session_type?: string;
    }) => {
      const session = await apiPost<ChatSession>(API_ROUTES.chat.sessions, input);
      upsertSession(session);
      setActive(session.id);
      setMessages([]);
      return session;
    },
    [upsertSession, setActive, setMessages],
  );

  const openSession = useCallback(
    async (id: string) => {
      const data = await apiGet<SessionDetailResponse>(API_ROUTES.chat.session(id));
      setActive(id);
      setMessages(data.messages || []);
      if (data.session) upsertSession(data.session);
    },
    [setActive, setMessages, upsertSession],
  );

  const sendMessage = useCallback(
    async (content: string, languageOverride?: string) => {
      if (!activeSessionId) throw new Error("No active chat session");
      // optimistic user message
      const tempUserMsg: ChatMessage = {
        id: `temp-${Date.now()}`,
        role: "user",
        content,
      };
      appendMessage(tempUserMsg);
      setSending(true);
      try {
        const reply = await apiPost<ChatMessage>(API_ROUTES.chat.message(activeSessionId), {
          content,
          language_override: languageOverride,
        });
        appendMessage(reply);
        return reply;
      } finally {
        setSending(false);
      }
    },
    [activeSessionId, appendMessage, setSending],
  );

  const sendFeedback = useCallback(
    async (messageId: string, isHelpful: boolean, rating?: number) => {
      if (!activeSessionId) return;
      await apiPost(API_ROUTES.chat.feedback(activeSessionId), {
        message_id: messageId,
        is_helpful: isHelpful,
        rating,
      });
    },
    [activeSessionId],
  );

  const deleteSession = useCallback(
    async (id: string) => {
      await apiDelete(API_ROUTES.chat.session(id));
      removeSession(id);
    },
    [removeSession],
  );

  const updateSessionPapers = useCallback(
    async (id: string, paperIds: string[]) => {
      await apiPatch(API_ROUTES.chat.setPapers(id), { paper_ids: paperIds });
    },
    [],
  );

  return {
    sessions,
    activeSessionId,
    messages,
    sending,
    loadSessions,
    createSession,
    openSession,
    sendMessage,
    sendFeedback,
    deleteSession,
    updateSessionPapers,
  };
}

'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { createAISession, type AISession, type ChatMode } from '@/lib/ai-router';
import { useAIProviderStore } from '@/stores/aiProviderStore';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  provider: 'gemini' | 'local';
  timestamp: Date;
  isStreaming?: boolean;
  isError?: boolean;
}

export function useAIProvider(mode: ChatMode) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const sessionRef = useRef<AISession | null>(null);
  const { provider } = useAIProviderStore();

  // Reset session when provider changes
  useEffect(() => {
    sessionRef.current = null;
    setMessages([]);
  }, [provider]);

  const initSession = useCallback(
    async (contextData?: string) => {
      sessionRef.current = await createAISession(mode, contextData);
    },
    [mode, provider]
  );

  const sendMessage = useCallback(
    async (userText: string, contextData?: string) => {
      if (!sessionRef.current) {
        await initSession(contextData);
      }

      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content: userText,
        provider,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);
      setStreamingContent('');

      const assistantId = crypto.randomUUID();
      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: 'assistant',
          content: '',
          provider,
          timestamp: new Date(),
          isStreaming: true,
        },
      ]);

      await sessionRef.current!.sendMessage(
        userText,
        (chunk) => {
          setStreamingContent((prev) => {
            const next = prev + chunk;
            setMessages((msgs) =>
              msgs.map((m) => (m.id === assistantId ? { ...m, content: next } : m))
            );
            return next;
          });
        },
        (fullText) => {
          setMessages((msgs) =>
            msgs.map((m) =>
              m.id === assistantId ? { ...m, content: fullText, isStreaming: false } : m
            )
          );
          setIsLoading(false);
          setStreamingContent('');
        },
        (error) => {
          setMessages((msgs) =>
            msgs.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: `⚠️ ${error}. ${
                      provider === 'local'
                        ? 'Try switching to Gemini mode.'
                        : 'Please try again.'
                    }`,
                    isStreaming: false,
                    isError: true,
                  }
                : m
            )
          );
          setIsLoading(false);
          setStreamingContent('');
        }
      );
    },
    [mode, provider, initSession]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    sessionRef.current = null;
  }, []);

  return {
    messages,
    isLoading,
    streamingContent,
    currentProvider: provider,
    sendMessage,
    initSession,
    clearMessages,
  };
}

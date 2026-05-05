"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, AlertCircle, Bot } from "lucide-react";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { useChat } from "@/hooks/useChat";
import { useAIProviderStore } from "@/stores/aiProviderStore";

export function ChatWindow({ sessionId }: { sessionId: string }) {
  const { messages, sending, openSession, sendMessage, sendFeedback } = useChat();
  const { provider } = useAIProviderStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (sessionId) {
      openSession(sessionId).catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load session");
      });
    }
  }, [sessionId, openSession]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length]);

  const handleSend = async (text: string, lang?: string) => {
    setError("");
    try {
      await sendMessage(text, lang);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b bg-muted/40 px-4 py-2 text-xs">
        <Bot className="h-3.5 w-3.5 text-muted-foreground" />
        <span className="text-muted-foreground">
          Mode: <strong className="capitalize">{provider}</strong>
          {provider === "local" && " · using trained models"}
          {provider === "gemini" && " · using Google Gemini"}
        </span>
      </div>
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && !sending && !error && (
          <div className="text-center text-sm text-muted-foreground space-y-2 py-8">
            <Bot className="mx-auto h-8 w-8 text-primary/40" />
            <p className="font-medium">Start the conversation</p>
            <p className="text-xs">Your question will be answered using the papers in this session.</p>
          </div>
        )}
        {messages.map((m) => (
          <ChatMessage key={m.id} message={m} onFeedback={sendFeedback} />
        ))}
        {sending && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Thinking…
          </div>
        )}
        {error && (
          <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium">Failed to send message</p>
              <p className="text-xs mt-1">{error}</p>
              <p className="text-xs mt-2">
                Tip: Use <strong>Quick Chat</strong> mode on the chat home page to chat directly
                with Gemini without uploaded papers.
              </p>
            </div>
          </div>
        )}
      </div>
      <ChatInput
        disabled={sending}
        onSend={handleSend}
      />
    </div>
  );
}

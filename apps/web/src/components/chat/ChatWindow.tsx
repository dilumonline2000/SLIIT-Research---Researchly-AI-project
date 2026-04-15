"use client";

import { useEffect, useRef } from "react";
import { Loader2 } from "lucide-react";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { useChat } from "@/hooks/useChat";

export function ChatWindow({ sessionId }: { sessionId: string }) {
  const { messages, sending, openSession, sendMessage, sendFeedback } = useChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (sessionId) openSession(sessionId).catch(() => {});
  }, [sessionId, openSession]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length]);

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && !sending && (
          <p className="text-center text-sm text-muted-foreground">
            Start the conversation. Your question will be answered using the papers in this session.
          </p>
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
      </div>
      <ChatInput
        disabled={sending}
        onSend={async (text, lang) => {
          await sendMessage(text, lang);
        }}
      />
    </div>
  );
}

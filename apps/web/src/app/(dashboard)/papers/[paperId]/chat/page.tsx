"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { useChat } from "@/hooks/useChat";

export default function PaperChatPage() {
  const params = useParams<{ paperId: string }>();
  const paperId = params.paperId;
  const { createSession, activeSessionId } = useChat();
  const [creating, setCreating] = useState(true);

  useEffect(() => {
    createSession({
      title: "Paper chat",
      paper_ids: [paperId],
      session_type: "paper_specific",
      preferred_language: "auto",
    })
      .catch(console.error)
      .finally(() => setCreating(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paperId]);

  if (creating || !activeSessionId)
    return <p className="text-sm text-muted-foreground">Starting chat session…</p>;

  return (
    <div className="h-[calc(100vh-8rem)] overflow-hidden rounded-lg border bg-card">
      <ChatWindow sessionId={activeSessionId} />
    </div>
  );
}

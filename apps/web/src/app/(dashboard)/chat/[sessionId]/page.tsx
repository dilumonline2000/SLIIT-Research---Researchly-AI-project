"use client";

import { useParams } from "next/navigation";
import { ChatWindow } from "@/components/chat/ChatWindow";

export default function ChatSessionPage() {
  const params = useParams<{ sessionId: string }>();
  return (
    <div className="h-[calc(100vh-8rem)] h-[calc(100dvh-8rem)] overflow-hidden rounded-xl border bg-card shadow-soft">
      <ChatWindow sessionId={params.sessionId} />
    </div>
  );
}

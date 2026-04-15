"use client";

import { useParams } from "next/navigation";
import { ChatWindow } from "@/components/chat/ChatWindow";

export default function ChatSessionPage() {
  const params = useParams<{ sessionId: string }>();
  return (
    <div className="h-[calc(100vh-8rem)] overflow-hidden rounded-lg border bg-card">
      <ChatWindow sessionId={params.sessionId} />
    </div>
  );
}

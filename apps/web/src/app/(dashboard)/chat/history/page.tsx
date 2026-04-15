"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Trash2, MessageSquare } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useChat } from "@/hooks/useChat";

export default function ChatHistoryPage() {
  const { sessions, loadSessions, deleteSession } = useChat();

  useEffect(() => {
    loadSessions().catch(console.error);
  }, [loadSessions]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Chat History</h1>
        <p className="text-sm text-muted-foreground">All your past research conversations.</p>
      </div>

      {sessions.length === 0 ? (
        <p className="text-sm text-muted-foreground">No sessions yet.</p>
      ) : (
        <div className="space-y-2">
          {sessions.map((s) => (
            <Card key={s.id}>
              <CardContent className="flex items-center justify-between p-4">
                <Link href={`/chat/${s.id}`} className="flex flex-1 items-center gap-3">
                  <MessageSquare className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{s.title || "Untitled"}</p>
                    <p className="text-xs text-muted-foreground">
                      {s.paper_ids.length} papers · {s.message_count} messages · {s.preferred_language}
                    </p>
                  </div>
                </Link>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    if (confirm("Delete this chat?")) await deleteSession(s.id);
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

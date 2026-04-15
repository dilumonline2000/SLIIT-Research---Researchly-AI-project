"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Plus, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { PaperSelector } from "@/components/papers/PaperSelector";
import { useChat } from "@/hooks/useChat";

export default function ChatHomePage() {
  const router = useRouter();
  const { sessions, loadSessions, createSession } = useChat();
  const [selected, setSelected] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadSessions().catch(console.error);
  }, [loadSessions]);

  const start = async () => {
    setCreating(true);
    try {
      const s = await createSession({
        title: selected.length > 0 ? `Chat (${selected.length} papers)` : "Corpus chat",
        paper_ids: selected,
        session_type: selected.length > 0 ? "paper_specific" : "corpus_wide",
        preferred_language: "auto",
      });
      router.push(`/chat/${s.id}`);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Research Chat</h1>
          <p className="text-sm text-muted-foreground">
            Ask questions in English, Sinhala, Tamil, or Singlish — answers are grounded in your uploaded papers.
          </p>
        </div>
        <Link href="/chat/history">
          <Button variant="outline">History</Button>
        </Link>
      </div>

      <Card>
        <CardContent className="space-y-4 p-6">
          <h2 className="text-lg font-semibold">Start a new chat</h2>
          <p className="text-sm text-muted-foreground">
            Optionally select papers to scope the conversation. Leaving empty searches across all your papers.
          </p>
          <PaperSelector selectedIds={selected} onChange={setSelected} />
          <Button onClick={start} disabled={creating}>
            <Plus className="mr-2 h-4 w-4" />
            {creating ? "Creating…" : "Start chat"}
          </Button>
        </CardContent>
      </Card>

      <div>
        <h2 className="mb-3 text-lg font-semibold">Recent sessions</h2>
        {sessions.length === 0 ? (
          <p className="text-sm text-muted-foreground">No chat sessions yet.</p>
        ) : (
          <div className="space-y-2">
            {sessions.slice(0, 8).map((s) => (
              <Link key={s.id} href={`/chat/${s.id}`}>
                <Card className="transition-shadow hover:shadow">
                  <CardContent className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-3">
                      <MessageSquare className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="font-medium">{s.title || "Untitled"}</p>
                        <p className="text-xs text-muted-foreground">
                          {s.paper_ids.length} papers · {s.message_count} messages
                        </p>
                      </div>
                    </div>
                    <span className="text-xs text-muted-foreground">{s.preferred_language}</span>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

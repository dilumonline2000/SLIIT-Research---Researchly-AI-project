"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Trash2, MessageSquare, History, Plus, Search, FileText, Languages, ChevronRight } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHero, heroButtonPrimary } from "@/components/shared/PageHero";
import { useChat } from "@/hooks/useChat";

function formatDate(iso?: string) {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? null
    : d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export default function ChatHistoryPage() {
  const { sessions, loadSessions, deleteSession } = useChat();
  const [query, setQuery] = useState("");

  useEffect(() => {
    loadSessions().catch(console.error);
  }, [loadSessions]);

  const totalMessages = sessions.reduce((n, s) => n + (s.message_count || 0), 0);
  const visible = sessions.filter(
    (s) => !query.trim() || (s.title || "Untitled").toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <div className="space-y-6 pb-8">
      <PageHero
        theme="library"
        icon={History}
        title="Chat History"
        description="All your past research conversations — pick up right where you left off."
        actions={
          <Link href="/chat" className={heroButtonPrimary}>
            <Plus className="h-4 w-4" /> New chat
          </Link>
        }
        stats={[
          { label: "Conversations", value: sessions.length, icon: MessageSquare },
          { label: "Messages", value: totalMessages, icon: History },
        ]}
      />

      {sessions.length > 0 && (
        <div className="relative max-w-md">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search conversations…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="h-11 rounded-xl bg-card pl-10 shadow-soft"
          />
        </div>
      )}

      {sessions.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed bg-card/50 p-10 text-center">
          <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-md">
            <MessageSquare className="h-7 w-7" />
          </span>
          <p className="font-semibold">No sessions yet</p>
          <p className="text-sm text-muted-foreground">Start a research chat and it will appear here.</p>
          <Link
            href="/chat"
            className="inline-flex h-10 items-center rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 px-4 text-sm font-semibold text-white"
          >
            Start chatting
          </Link>
        </div>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {visible.map((s) => (
            <Card
              key={s.id}
              className="group flex items-center gap-3 p-3 transition-all hover:border-primary/30 hover:shadow-lg sm:p-4"
            >
              <Link href={`/chat/${s.id}`} className="flex min-w-0 flex-1 items-center gap-3">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-sm">
                  <MessageSquare className="h-5 w-5" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-semibold group-hover:text-primary">{s.title || "Untitled"}</p>
                  <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1">
                      <FileText className="h-3 w-3" /> {s.paper_ids.length} papers
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <MessageSquare className="h-3 w-3" /> {s.message_count} messages
                    </span>
                    <span className="inline-flex items-center gap-1 uppercase">
                      <Languages className="h-3 w-3" /> {s.preferred_language}
                    </span>
                    {formatDate(s.updated_at || s.created_at) && (
                      <span>{formatDate(s.updated_at || s.created_at)}</span>
                    )}
                  </div>
                </div>
                <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </Link>
              <Button
                variant="ghost"
                size="sm"
                aria-label="Delete chat"
                className="h-9 w-9 shrink-0 p-0 text-muted-foreground hover:bg-rose-500/10 hover:text-rose-600"
                onClick={async () => {
                  if (confirm("Delete this chat?")) await deleteSession(s.id);
                }}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </Card>
          ))}
          {visible.length === 0 && (
            <p className="text-sm text-muted-foreground">No conversations match “{query}”.</p>
          )}
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Plus, MessageSquare, Send, Loader2, Sparkles, FileText, Bot, User, History } from "lucide-react";
import { PageHero, heroButtonGhost, SegmentedTabs, SectionTitle } from "@/components/shared/PageHero";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { PaperSelector } from "@/components/papers/PaperSelector";
import { useChat } from "@/hooks/useChat";
import { useAIProviderStore } from "@/stores/aiProviderStore";
import { startGeneralChatSession, type GenerativeChat } from "@/lib/gemini";

interface QuickMsg {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export default function ChatHomePage() {
  const router = useRouter();
  const { sessions, loadSessions, createSession } = useChat();
  const { provider } = useAIProviderStore();
  const [selected, setSelected] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);
  const [showPaperMode, setShowPaperMode] = useState(false);

  // Quick chat state
  const [quickMessages, setQuickMessages] = useState<QuickMsg[]>([]);
  const [quickInput, setQuickInput] = useState("");
  const [quickSending, setQuickSending] = useState(false);
  const [quickError, setQuickError] = useState("");
  const chatRef = useRef<GenerativeChat | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSessions().catch(() => {});
  }, [loadSessions]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [quickMessages.length, quickSending]);

  const startWithPapers = async () => {
    setCreating(true);
    try {
      const s = await createSession({
        title: selected.length > 0 ? `Chat (${selected.length} papers)` : "Corpus chat",
        paper_ids: selected,
        session_type: selected.length > 0 ? "paper_specific" : "corpus_wide",
        preferred_language: "auto",
      });
      router.push(`/chat/${s.id}`);
    } catch (err) {
      alert("Failed to create chat session: " + (err instanceof Error ? err.message : "Unknown error"));
    } finally {
      setCreating(false);
    }
  };

  const sendQuickMessage = async () => {
    const text = quickInput.trim();
    if (!text || quickSending) return;

    setQuickInput("");
    setQuickError("");
    const userMsg: QuickMsg = {
      id: `u-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: Date.now(),
    };
    setQuickMessages((prev) => [...prev, userMsg]);
    setQuickSending(true);

    try {
      // Lazy-init chat session; reset on error to allow retry
      if (!chatRef.current) {
        chatRef.current = await startGeneralChatSession();
      }
      const reply = await chatRef.current.sendMessage(text);
      setQuickMessages((prev) => [
        ...prev,
        { id: `a-${Date.now()}`, role: "assistant", content: reply, timestamp: Date.now() },
      ]);
    } catch (err) {
      // Reset chat session so next message starts fresh
      chatRef.current = null;
      const raw = err instanceof Error ? err.message : "Failed to get response";
      // Parse common Gemini API errors into friendly messages
      let friendly = raw;
      if (raw.includes("429") || raw.toLowerCase().includes("quota")) {
        friendly = "Gemini API quota exceeded. You've hit the free-tier rate limit. Please wait a minute and try again, or check your API key billing at ai.google.dev.";
      } else if (raw.includes("404") || raw.toLowerCase().includes("not found")) {
        friendly = "Gemini model unavailable. Check that NEXT_PUBLIC_GEMINI_API_KEY is valid and has access to Gemini 2.5 Flash.";
      } else if (raw.includes("403") || raw.toLowerCase().includes("permission")) {
        friendly = "Gemini API key doesn't have permission for this model. Verify your key at ai.google.dev.";
      } else if (raw.includes("400")) {
        friendly = "Invalid request to Gemini API. The message may be too long — try a shorter question.";
      }
      setQuickError(friendly);
      setQuickMessages((prev) => [
        ...prev,
        {
          id: `e-${Date.now()}`,
          role: "assistant",
          content: `⚠️ ${friendly}`,
          timestamp: Date.now(),
        },
      ]);
    } finally {
      setQuickSending(false);
    }
  };

  const onKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendQuickMessage();
    }
  };

  const clearQuickChat = () => {
    setQuickMessages([]);
    chatRef.current = null;
    setQuickError("");
  };

  return (
    <div className="space-y-6 pb-8">
      <PageHero
        theme="library"
        icon={MessageSquare}
        title="Research Chat"
        description="Ask any research question, or chat with your uploaded papers using retrieval-augmented AI."
        actions={
          <Link href="/chat/history" className={heroButtonGhost}>
            <History className="h-4 w-4" /> History
          </Link>
        }
      />

      {/* Mode selector */}
      <SegmentedTabs<"quick" | "papers">
        theme="library"
        value={showPaperMode ? "papers" : "quick"}
        onChange={(v) => setShowPaperMode(v === "papers")}
        tabs={[
          { id: "quick", label: "Quick Chat (Gemini)", icon: Sparkles },
          { id: "papers", label: "Chat with Papers (RAG)", icon: FileText },
        ]}
      />

      {!showPaperMode ? (
        // ── QUICK CHAT (no papers needed) ─────────────────────────────────
        <Card className="overflow-hidden">
          <div className="flex items-center justify-between gap-3 border-b bg-gradient-to-r from-indigo-500/[0.06] to-violet-500/[0.06] px-4 py-3 sm:px-6">
            <div className="flex min-w-0 items-center gap-3">
              <span className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-sm">
                <Bot className="h-5 w-5" />
                <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-card bg-emerald-500" />
              </span>
              <div className="min-w-0">
                <p className="truncate font-semibold">Quick Research Chat</p>
                <p className="truncate text-xs text-muted-foreground">
                  Research questions, summaries, methodology help · Google Gemini
                </p>
              </div>
            </div>
            {quickMessages.length > 0 && (
              <Button variant="ghost" size="sm" onClick={clearQuickChat}>
                Clear
              </Button>
            )}
          </div>
          <CardContent className="p-0">
            <div
              ref={scrollRef}
              className="flex max-h-[60vh] min-h-[320px] flex-col gap-4 overflow-y-auto bg-gradient-to-b from-background to-muted/20 p-4 sm:max-h-[520px] sm:p-6"
            >
              {quickMessages.length === 0 && (
                <div className="space-y-3 py-8 text-center text-sm text-muted-foreground">
                  <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-glow">
                    <Sparkles className="h-7 w-7" />
                  </span>
                  <p className="text-base font-semibold text-foreground">What would you like to explore today?</p>
                  <p className="mx-auto max-w-md text-sm">
                    Try: &ldquo;Explain transformer architecture&rdquo;, &ldquo;Help me write an
                    abstract for a paper on federated learning&rdquo;, or &ldquo;What are common
                    research methodologies?&rdquo;
                  </p>
                  <div className="flex flex-wrap justify-center gap-2 pt-2">
                    {[
                      "Explain BERT in simple terms",
                      "How to write a literature review?",
                      "Best practices for SLR methodology",
                    ].map((q) => (
                      <button
                        key={q}
                        onClick={() => setQuickInput(q)}
                        className="rounded-full border bg-card px-3.5 py-1.5 text-xs font-medium transition-colors hover:border-primary/40 hover:bg-accent hover:text-accent-foreground"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {quickMessages.map((m) => (
                <div
                  key={m.id}
                  className={`flex gap-2.5 sm:gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {m.role === "assistant" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 text-white">
                      <Bot className="h-4 w-4" />
                    </div>
                  )}
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm shadow-sm sm:max-w-[80%] ${
                      m.role === "user"
                        ? "rounded-br-md bg-gradient-to-br from-indigo-600 to-violet-600 text-white"
                        : "rounded-bl-md border bg-card"
                    }`}
                  >
                    <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
                  </div>
                  {m.role === "user" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                      <User className="h-4 w-4" />
                    </div>
                  )}
                </div>
              ))}

              {quickSending && (
                <div className="flex justify-start gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 text-white">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="flex items-center gap-2 rounded-2xl rounded-bl-md border bg-card px-4 py-2.5 text-sm shadow-sm">
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                    <span className="text-muted-foreground">Thinking…</span>
                  </div>
                </div>
              )}

              {quickError && (
                <p className="text-center text-xs text-destructive">{quickError}</p>
              )}
            </div>

            <div className="border-t bg-card p-3">
              <div className="flex items-end gap-2 rounded-2xl border bg-background p-1.5 shadow-sm focus-within:ring-2 focus-within:ring-ring">
                <textarea
                  value={quickInput}
                  onChange={(e) => setQuickInput(e.target.value)}
                  onKeyDown={onKey}
                  rows={2}
                  placeholder="Ask anything... (Enter to send, Shift+Enter for newline)"
                  className="flex-1 resize-none bg-transparent p-2.5 text-sm focus:outline-none"
                  disabled={quickSending}
                />
                <Button
                  onClick={sendQuickMessage}
                  disabled={quickSending || !quickInput.trim()}
                  aria-label="Send"
                  className="h-10 w-10 shrink-0 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 p-0 text-white"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              <p className="mt-1.5 px-1 text-xs text-muted-foreground">
                Powered by Gemini 2.5 Flash · Provider: <strong className="capitalize">{provider}</strong>
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        // ── PAPER MODE (RAG with uploaded papers) ─────────────────────────
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2.5 text-lg">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white">
                <FileText className="h-4 w-4" />
              </span>
              Chat with your uploaded papers
            </CardTitle>
            <CardDescription>
              Select papers to scope the conversation. Leave empty to search across all your papers.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <PaperSelector selectedIds={selected} onChange={setSelected} />
            <Button
              onClick={startWithPapers}
              disabled={creating}
              className="w-full bg-gradient-to-r from-indigo-600 to-violet-600 text-white sm:w-auto"
            >
              <Plus className="mr-2 h-4 w-4" />
              {creating ? "Creating…" : "Start chat with papers"}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Recent paper-chat sessions */}
      <div className="space-y-3">
        <SectionTitle
          theme="library"
          icon={History}
          title="Recent paper conversations"
          action={
            sessions.length > 0 ? (
              <Link href="/chat/history" className="text-sm font-medium text-primary hover:underline">
                View all
              </Link>
            ) : undefined
          }
        />
        {sessions.length === 0 ? (
          <p className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">
            No paper-based chat sessions yet. Switch to &ldquo;Chat with Papers&rdquo; mode to start one.
          </p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {sessions.slice(0, 6).map((s) => (
              <Link key={s.id} href={`/chat/${s.id}`}>
                <Card className="group transition-all hover:border-primary/30 hover:shadow-lg">
                  <CardContent className="flex items-center justify-between gap-3 p-3.5">
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-300">
                        <MessageSquare className="h-4 w-4" />
                      </span>
                      <div className="min-w-0">
                        <p className="truncate font-medium group-hover:text-primary">{s.title || "Untitled"}</p>
                        <p className="text-xs text-muted-foreground">
                          {s.paper_ids.length} papers · {s.message_count} messages
                        </p>
                      </div>
                    </div>
                    <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-xs uppercase text-muted-foreground">
                      {s.preferred_language}
                    </span>
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

"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Plus, MessageSquare, Send, Loader2, Sparkles, FileText, Bot, User } from "lucide-react";
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
        friendly = "Gemini model unavailable. Check that NEXT_PUBLIC_GEMINI_API_KEY is valid and has access to Gemini 2.0 Flash.";
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Research Chat</h1>
          <p className="text-sm text-muted-foreground">
            Ask any research question, or chat with your uploaded papers.
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/chat/history">
            <Button variant="outline" size="sm">
              <MessageSquare className="mr-2 h-4 w-4" /> History
            </Button>
          </Link>
        </div>
      </div>

      {/* Mode selector */}
      <div className="flex gap-2">
        <Button
          variant={!showPaperMode ? "default" : "outline"}
          size="sm"
          onClick={() => setShowPaperMode(false)}
        >
          <Sparkles className="mr-2 h-4 w-4" /> Quick Chat (Gemini)
        </Button>
        <Button
          variant={showPaperMode ? "default" : "outline"}
          size="sm"
          onClick={() => setShowPaperMode(true)}
        >
          <FileText className="mr-2 h-4 w-4" /> Chat with Papers (RAG)
        </Button>
      </div>

      {!showPaperMode ? (
        // ── QUICK CHAT (no papers needed) ─────────────────────────────────
        <Card className="overflow-hidden">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Bot className="h-5 w-5" /> Quick Research Chat
                </CardTitle>
                <CardDescription>
                  Ask anything — research questions, paper summaries, methodology help. Uses Google Gemini directly.
                </CardDescription>
              </div>
              {quickMessages.length > 0 && (
                <Button variant="ghost" size="sm" onClick={clearQuickChat}>
                  Clear
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div
              ref={scrollRef}
              className="flex flex-col gap-4 max-h-[500px] min-h-[300px] overflow-y-auto p-6 bg-gradient-to-b from-background to-muted/20"
            >
              {quickMessages.length === 0 && (
                <div className="text-center text-sm text-muted-foreground py-8 space-y-3">
                  <Sparkles className="mx-auto h-10 w-10 text-primary/40" />
                  <p className="font-medium">Start a conversation</p>
                  <p className="text-xs max-w-md mx-auto">
                    Try: &ldquo;Explain transformer architecture&rdquo;, &ldquo;Help me write an
                    abstract for a paper on federated learning&rdquo;, or &ldquo;What are common
                    research methodologies?&rdquo;
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center pt-2">
                    {[
                      "Explain BERT in simple terms",
                      "How to write a literature review?",
                      "Best practices for SLR methodology",
                    ].map((q) => (
                      <button
                        key={q}
                        onClick={() => setQuickInput(q)}
                        className="rounded-full border bg-card px-3 py-1 text-xs hover:bg-accent transition-colors"
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
                  className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {m.role === "assistant" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                      <Bot className="h-4 w-4" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm shadow-sm ${
                      m.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-card border"
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
                <div className="flex gap-3 justify-start">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="bg-card border rounded-2xl px-4 py-2.5 text-sm shadow-sm flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-muted-foreground">Thinking…</span>
                  </div>
                </div>
              )}

              {quickError && (
                <p className="text-xs text-destructive text-center">{quickError}</p>
              )}
            </div>

            <div className="border-t bg-background p-3">
              <div className="flex items-end gap-2">
                <textarea
                  value={quickInput}
                  onChange={(e) => setQuickInput(e.target.value)}
                  onKeyDown={onKey}
                  rows={2}
                  placeholder="Ask anything... (Press Enter to send, Shift+Enter for newline)"
                  className="flex-1 resize-none rounded-md border bg-background p-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  disabled={quickSending}
                />
                <Button onClick={sendQuickMessage} disabled={quickSending || !quickInput.trim()}>
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              <p className="mt-1.5 text-xs text-muted-foreground">
                Powered by Gemini 2.0 Flash · Provider: <strong>{provider}</strong>
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        // ── PAPER MODE (RAG with uploaded papers) ─────────────────────────
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Chat with your uploaded papers</CardTitle>
            <CardDescription>
              Select papers to scope the conversation. Leave empty to search across all your papers.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <PaperSelector selectedIds={selected} onChange={setSelected} />
            <Button onClick={startWithPapers} disabled={creating}>
              <Plus className="mr-2 h-4 w-4" />
              {creating ? "Creating…" : "Start chat with papers"}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Recent paper-chat sessions */}
      <div>
        <h2 className="mb-3 text-lg font-semibold">Recent paper conversations</h2>
        {sessions.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No paper-based chat sessions yet. Switch to &ldquo;Chat with Papers&rdquo; mode to start one.
          </p>
        ) : (
          <div className="grid gap-2 md:grid-cols-2">
            {sessions.slice(0, 6).map((s) => (
              <Link key={s.id} href={`/chat/${s.id}`}>
                <Card className="transition-shadow hover:shadow">
                  <CardContent className="flex items-center justify-between p-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <MessageSquare className="h-4 w-4 text-muted-foreground shrink-0" />
                      <div className="min-w-0">
                        <p className="font-medium truncate">{s.title || "Untitled"}</p>
                        <p className="text-xs text-muted-foreground">
                          {s.paper_ids.length} papers · {s.message_count} messages
                        </p>
                      </div>
                    </div>
                    <span className="text-xs text-muted-foreground shrink-0">{s.preferred_language}</span>
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

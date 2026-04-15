"use client";

import { ThumbsUp, ThumbsDown, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatMessage as Msg } from "@/stores/chatStore";

const LANG_FLAG: Record<string, string> = {
  en: "EN",
  si: "සි",
  ta: "த",
  singlish: "EN+සි",
};

export function ChatMessage({
  message,
  onFeedback,
}: {
  message: Msg;
  onFeedback?: (id: string, helpful: boolean) => void;
}) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex gap-3", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3 text-sm shadow-sm",
          isUser ? "bg-primary text-primary-foreground" : "bg-card border",
        )}
      >
        <div className="mb-1 flex items-center gap-2 text-xs opacity-70">
          <span>{isUser ? "You" : "Assistant"}</span>
          {message.detected_language && (
            <span className="rounded bg-black/10 px-1.5 py-0.5">
              {LANG_FLAG[message.detected_language] || message.detected_language}
            </span>
          )}
        </div>
        <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>

        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-3 space-y-1 border-t border-border/50 pt-2">
            <p className="text-xs font-semibold opacity-70">Sources</p>
            {message.citations.slice(0, 5).map((c, i) => (
              <div key={i} className="flex items-center gap-1 text-xs">
                <FileText className="h-3 w-3" />
                <span className="line-clamp-1">
                  {c.paper_title || "Untitled"}
                  {c.section ? ` — ${c.section}` : ""}
                </span>
                {typeof c.score === "number" && (
                  <span className="ml-auto opacity-60">{(c.score * 100).toFixed(0)}%</span>
                )}
              </div>
            ))}
          </div>
        )}

        {!isUser && onFeedback && (
          <div className="mt-2 flex gap-2 text-xs opacity-60">
            <button
              onClick={() => onFeedback(message.id, true)}
              className="rounded p-1 hover:bg-accent"
              aria-label="Helpful"
            >
              <ThumbsUp className="h-3 w-3" />
            </button>
            <button
              onClick={() => onFeedback(message.id, false)}
              className="rounded p-1 hover:bg-accent"
              aria-label="Not helpful"
            >
              <ThumbsDown className="h-3 w-3" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

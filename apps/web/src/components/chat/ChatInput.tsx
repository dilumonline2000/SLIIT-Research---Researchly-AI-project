"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useLanguageDetect } from "@/hooks/useLanguageDetect";

const LANG_LABEL: Record<string, string> = {
  auto: "Auto",
  en: "English",
  si: "Sinhala",
  ta: "Tamil",
  singlish: "Singlish",
};

export function ChatInput({
  disabled,
  onSend,
}: {
  disabled?: boolean;
  onSend: (text: string, language?: string) => Promise<void>;
}) {
  const [value, setValue] = useState("");
  const [override, setOverride] = useState<string>("auto");
  const { result, detectLocal } = useLanguageDetect();
  const taRef = useRef<HTMLTextAreaElement>(null);

  const submit = async () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    setValue("");
    await onSend(trimmed, override === "auto" ? undefined : override);
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="border-t bg-card p-3">
      <div className="mb-2 flex items-center gap-3 text-xs text-muted-foreground">
        <span>
          Detected:{" "}
          <strong>{result ? LANG_LABEL[result.language] || result.language : "—"}</strong>
        </span>
        <select
          value={override}
          onChange={(e) => setOverride(e.target.value)}
          className="rounded border bg-background px-2 py-0.5"
        >
          {Object.entries(LANG_LABEL).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
        <span className="ml-auto hidden sm:inline">Ctrl/⌘ + Enter to send</span>
      </div>
      <div className="flex items-end gap-2 rounded-2xl border bg-background p-1.5 shadow-sm focus-within:ring-2 focus-within:ring-ring">
        <textarea
          ref={taRef}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            if (e.target.value.length > 4) detectLocal(e.target.value);
          }}
          onKeyDown={onKey}
          rows={2}
          placeholder="Ask anything about your papers… (English / සිංහල / தமிழ் / Singlish)"
          className="flex-1 resize-none bg-transparent p-2.5 text-sm focus:outline-none"
          disabled={disabled}
        />
        <Button
          onClick={submit}
          disabled={disabled || !value.trim()}
          aria-label="Send"
          className="h-10 w-10 shrink-0 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 p-0 text-white"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

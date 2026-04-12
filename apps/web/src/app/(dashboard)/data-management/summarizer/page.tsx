"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface SummarizeResponse {
  summary: string;
  model_version: string;
}

export default function SummarizePage() {
  const [text, setText] = useState("");
  const [length, setLength] = useState<"short" | "medium" | "detailed">("medium");
  const [result, setResult] = useState<SummarizeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSummarize = async () => {
    if (text.trim().length < 100) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<SummarizeResponse>(API_ROUTES.module3.summarize, { text, length });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Summarization failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Research Summarizer</h1>
        <p className="text-muted-foreground">Generate abstractive summaries of research papers.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Input Paper</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="sum-text">Paper text (minimum 100 characters)</Label>
            <textarea
              id="sum-text"
              className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Paste the full paper text or a large section..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">{text.length} characters</p>
          </div>
          <div className="flex gap-2">
            {(["short", "medium", "detailed"] as const).map((l) => (
              <Button key={l} variant={length === l ? "default" : "outline"} size="sm" onClick={() => setLength(l)}>
                {l.charAt(0).toUpperCase() + l.slice(1)}
              </Button>
            ))}
          </div>
          <Button onClick={handleSummarize} disabled={loading || text.trim().length < 100}>
            {loading ? "Summarizing..." : "Generate Summary"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {result && result.summary && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              Summary <span className="text-sm font-normal text-muted-foreground">({result.model_version})</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed">{result.summary}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

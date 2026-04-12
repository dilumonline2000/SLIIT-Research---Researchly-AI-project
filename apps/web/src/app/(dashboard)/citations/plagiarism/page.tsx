"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface FlaggedPassage {
  text: string;
  matched_source: string;
  similarity_score: number;
}

interface PlagiarismResponse {
  risk_level: "low" | "medium" | "high";
  overall_score: number;
  flagged_passages: FlaggedPassage[];
}

const riskColors = { low: "text-green-600", medium: "text-yellow-600", high: "text-red-600" };

export default function PlagiarismPage() {
  const [text, setText] = useState("");
  const [threshold, setThreshold] = useState(0.8);
  const [result, setResult] = useState<PlagiarismResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleCheck = async () => {
    if (text.trim().length < 10) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<PlagiarismResponse>(API_ROUTES.module1.checkPlagiarism, { text, threshold });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Check failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Plagiarism Checker</h1>
        <p className="text-muted-foreground">Check your text against the research paper corpus.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Input Text</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="check-text">Text to check</Label>
            <textarea
              id="check-text"
              className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Paste your research text here (minimum 10 characters)..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-4">
            <div className="space-y-1">
              <Label htmlFor="threshold">Similarity threshold</Label>
              <input type="range" id="threshold" min={0.5} max={1.0} step={0.05} value={threshold} onChange={(e) => setThreshold(parseFloat(e.target.value))} className="w-40" />
              <span className="ml-2 text-sm text-muted-foreground">{(threshold * 100).toFixed(0)}%</span>
            </div>
          </div>
          <Button onClick={handleCheck} disabled={loading || text.trim().length < 10}>
            {loading ? "Checking..." : "Check Plagiarism"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              Result:
              <span className={`capitalize font-bold ${riskColors[result.risk_level]}`}>
                {result.risk_level} risk
              </span>
              <span className="text-sm font-normal text-muted-foreground ml-2">
                (score: {(result.overall_score * 100).toFixed(1)}%)
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {result.flagged_passages.length > 0 ? (
              <div className="space-y-3">
                <p className="text-sm font-medium">{result.flagged_passages.length} passage(s) flagged:</p>
                {result.flagged_passages.map((fp, i) => (
                  <div key={i} className="rounded border border-destructive/20 bg-destructive/5 p-3 space-y-1">
                    <p className="text-sm italic">&quot;{fp.text}&quot;</p>
                    <p className="text-xs text-muted-foreground">
                      Matches: {fp.matched_source} ({(fp.similarity_score * 100).toFixed(1)}% similar)
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-green-600">No passages flagged above the similarity threshold.</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

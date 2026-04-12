"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface CategorizeResponse {
  categories: string[];
  confidence_scores: Record<string, number>;
  model_version: string;
}

export default function CategorizePage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<CategorizeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleCategorize = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<CategorizeResponse>(API_ROUTES.module3.categorize, { text });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Categorization failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Topic Categorization</h1>
        <p className="text-muted-foreground">Classify a paper into research categories using SciBERT.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Paper Text</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="cat-text">Abstract or full text</Label>
            <textarea
              id="cat-text"
              className="flex min-h-[150px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Paste a paper abstract..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          </div>
          <Button onClick={handleCategorize} disabled={loading || !text.trim()}>
            {loading ? "Classifying..." : "Categorize"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Categories ({result.model_version})</CardTitle>
          </CardHeader>
          <CardContent>
            {result.categories.length > 0 ? (
              <div className="space-y-2">
                {result.categories.map((cat) => (
                  <div key={cat} className="flex items-center gap-3">
                    <span className="rounded bg-primary/10 px-3 py-1 text-sm font-medium text-primary">{cat}</span>
                    <div className="flex-1 h-2 rounded-full bg-secondary">
                      <div className="h-2 rounded-full bg-primary" style={{ width: `${((result.confidence_scores[cat] || 0) * 100).toFixed(0)}%` }} />
                    </div>
                    <span className="text-sm text-muted-foreground">{((result.confidence_scores[cat] || 0) * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No categories matched above the threshold.</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface ResearchGap {
  topic: string;
  description: string;
  gap_score: number;
  recency_score: number;
  novelty_score: number;
  supporting_paper_ids: string[];
}

interface GapsResponse {
  gaps: ResearchGap[];
  total_papers_analyzed: number;
}

export default function GapAnalysisPage() {
  const [topic, setTopic] = useState("");
  const [result, setResult] = useState<GapsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<GapsResponse>(API_ROUTES.module1.analyzeGaps, { topic, corpus_size: 100 });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Research Gap Analysis</h1>
        <p className="text-muted-foreground">Discover under-explored areas in your research field.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Search Topic</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="topic">Research topic or area</Label>
            <Input
              id="topic"
              placeholder="e.g., federated learning for IoT security"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
            />
          </div>
          <Button onClick={handleAnalyze} disabled={loading || !topic.trim()}>
            {loading ? "Analyzing..." : "Find Research Gaps"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Analyzed {result.total_papers_analyzed} papers — found {result.gaps.length} potential gaps
          </p>
          {result.gaps.map((gap, i) => (
            <Card key={i}>
              <CardHeader>
                <CardTitle className="text-lg capitalize">{gap.topic}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm">{gap.description}</p>
                <div className="flex gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Gap: </span>
                    <span className="font-medium">{(gap.gap_score * 100).toFixed(0)}%</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Recency: </span>
                    <span className="font-medium">{(gap.recency_score * 100).toFixed(0)}%</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Novelty: </span>
                    <span className="font-medium">{(gap.novelty_score * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          {result.gaps.length === 0 && (
            <p className="text-sm text-muted-foreground">No significant gaps found. Try a more specific topic.</p>
          )}
        </div>
      )}
    </div>
  );
}

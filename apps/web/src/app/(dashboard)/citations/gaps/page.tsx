"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Database, Sparkles, BookOpen } from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface SupportingPaper {
  paper_id: string;
  title: string;
  authors: string[];
  year: number | string | null;
  url: string;
}

interface ResearchGap {
  topic: string;
  description: string;
  gap_score: number;
  recency_score: number;
  novelty_score: number;
  similarity?: number;
  gap_type?: string;
  supporting_paper?: SupportingPaper | null;
  supporting_paper_ids: string[];
}

interface GapsResponse {
  gaps: ResearchGap[];
  total_papers_analyzed: number;
  total_corpus_size?: number;
  model_version?: string;
  base_model?: string;
  source?: "local" | "gemini" | "fallback";
}

const SAMPLE_TOPICS = [
  "machine learning in healthcare",
  "blockchain supply chain",
  "deep learning crop disease detection",
  "IoT security in smart cities",
  "natural language processing for Sinhala",
];

export default function GapAnalysisPage() {
  const [topic, setTopic] = useState("");
  const [result, setResult] = useState<GapsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async (queryTopic?: string) => {
    const t = (queryTopic ?? topic).trim();
    if (!t) return;
    setTopic(t);
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<GapsResponse>(API_ROUTES.module1.analyzeGaps, {
        topic: t,
        top_k: 8,
        min_similarity: 0.2,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const sourceColor = (s?: string) => {
    if (s === "local") return "bg-emerald-100 text-emerald-700 border-emerald-200";
    if (s === "gemini") return "bg-blue-100 text-blue-700 border-blue-200";
    return "bg-gray-100 text-gray-700 border-gray-200";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Research Gap Analysis</h1>
        <p className="text-muted-foreground">
          Discover under-explored areas grounded in real SLIIT research papers.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Database className="h-5 w-5" /> Search Topic
          </CardTitle>
          <CardDescription>
            Enter any research area — we&apos;ll match it against 4,200+ SLIIT papers and surface gaps from their abstracts.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="topic">Research topic</Label>
            <Input
              id="topic"
              placeholder="e.g., federated learning for IoT security"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <span className="text-xs text-muted-foreground self-center">Try:</span>
            {SAMPLE_TOPICS.map((t) => (
              <button
                key={t}
                onClick={() => handleAnalyze(t)}
                className="rounded-full border bg-muted/50 px-3 py-1 text-xs hover:bg-accent transition-colors"
              >
                {t}
              </button>
            ))}
          </div>

          <Button onClick={() => handleAnalyze()} disabled={loading || !topic.trim()}>
            {loading ? "Analyzing..." : "Find Research Gaps"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <div className="space-y-4">
          <Card className="bg-muted/30">
            <CardContent className="p-3 flex flex-wrap items-center gap-3 text-sm">
              <Badge variant="outline" className={sourceColor(result.source)}>
                {result.source === "local" ? (
                  <span className="flex items-center gap-1"><Database className="h-3 w-3" /> Local SBERT model</span>
                ) : result.source === "gemini" ? (
                  <span className="flex items-center gap-1"><Sparkles className="h-3 w-3" /> Gemini fallback</span>
                ) : (
                  "Fallback"
                )}
              </Badge>
              {result.base_model && (
                <span className="text-xs text-muted-foreground">Model: {result.base_model}</span>
              )}
              <span className="text-xs text-muted-foreground">
                Found <strong>{result.gaps.length}</strong> gaps
                {result.total_corpus_size ? ` from a corpus of ${result.total_corpus_size.toLocaleString()} extracted gaps` : ""}
              </span>
            </CardContent>
          </Card>

          {result.gaps.map((gap, i) => (
            <Card key={i}>
              <CardHeader>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <CardTitle className="text-base capitalize line-clamp-2">{gap.topic}</CardTitle>
                    {gap.gap_type && (
                      <Badge variant="secondary" className="mt-1.5 text-[10px]">
                        {gap.gap_type.replace("_", " ")}
                      </Badge>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm leading-relaxed text-foreground/90">&ldquo;{gap.description}&rdquo;</p>

                <div className="flex flex-wrap gap-4 text-xs border-t pt-3">
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
                  {typeof gap.similarity === "number" && gap.similarity > 0 && (
                    <div>
                      <span className="text-muted-foreground">Similarity: </span>
                      <span className="font-medium">{(gap.similarity * 100).toFixed(0)}%</span>
                    </div>
                  )}
                </div>

                {gap.supporting_paper && gap.supporting_paper.title && (
                  <div className="rounded-md border bg-muted/30 p-3 text-xs space-y-1">
                    <div className="flex items-center gap-1.5 text-muted-foreground font-medium">
                      <BookOpen className="h-3 w-3" /> Source SLIIT paper
                    </div>
                    <p className="font-medium text-foreground">{gap.supporting_paper.title}</p>
                    <p className="text-muted-foreground">
                      {(gap.supporting_paper.authors || []).slice(0, 3).join(", ") || "Unknown authors"}
                      {gap.supporting_paper.year ? ` · ${gap.supporting_paper.year}` : ""}
                    </p>
                    {gap.supporting_paper.url && (
                      <a
                        href={gap.supporting_paper.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-primary hover:underline"
                      >
                        View on SLIIT RDA <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}

          {result.gaps.length === 0 && (
            <Card>
              <CardContent className="py-6 text-center text-sm text-muted-foreground">
                No significant gaps found for this topic. Try a more specific or related research area.
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

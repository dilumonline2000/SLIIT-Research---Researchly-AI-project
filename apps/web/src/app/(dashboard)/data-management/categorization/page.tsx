"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Database, Sparkles, Tag, BookOpen, ExternalLink } from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface TopCategory {
  label: string;
  confidence: number;
}

interface RelatedPaper {
  paper_id: string;
  title: string;
  authors: string[];
  year: number | string | null;
  url: string;
  subject?: string | string[] | null;
  similarity: number;
  abstract_excerpt: string;
}

interface CategorizeResponse {
  categories: string[];
  confidence_scores: Record<string, number>;
  top_categories: TopCategory[];
  related_papers?: RelatedPaper[];
  model_version: string;
  source?: "local" | "gemini" | "fallback";
}

const SAMPLE_ABSTRACTS = [
  {
    label: "Deep learning sample",
    text: "We propose a deep convolutional neural network architecture for medical image classification. The model is trained on 10,000 chest X-rays and achieves 95% accuracy on COVID-19 detection.",
  },
  {
    label: "Machine learning + Sri Lanka",
    text: "This paper investigates machine learning techniques for predicting agricultural yields in Sri Lanka. We use random forests and gradient boosting on rainfall and soil-moisture sensor data.",
  },
  {
    label: "IoT + cybersecurity",
    text: "We present a lightweight intrusion detection system for IoT networks based on anomaly detection. Our approach uses statistical features and a one-class SVM classifier deployed at the edge.",
  },
];

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
      const data = await apiPost<CategorizeResponse>(API_ROUTES.module3.categorize, {
        text,
        threshold: 0.2,
        top_k: 6,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Categorization failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Topic Categorization</h1>
        <p className="text-muted-foreground">
          Multi-label classifier trained on 1,382 SLIIT papers across 80 categories.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Paper Text</CardTitle>
          <CardDescription>
            Paste a paper abstract or first paragraph. The model returns the top categories with their confidence scores.
          </CardDescription>
        </CardHeader>
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

          <div className="flex flex-wrap gap-2">
            <span className="text-xs text-muted-foreground self-center">Try a sample:</span>
            {SAMPLE_ABSTRACTS.map((s) => (
              <button
                key={s.label}
                onClick={() => setText(s.text)}
                className="rounded-full border bg-muted/50 px-3 py-1 text-xs hover:bg-accent transition-colors"
              >
                {s.label}
              </button>
            ))}
          </div>

          <Button onClick={handleCategorize} disabled={loading || !text.trim()}>
            {loading ? "Classifying..." : "Categorize"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <>
          <Card className="bg-muted/30">
            <CardContent className="p-3 flex flex-wrap items-center gap-3 text-sm">
              <Badge variant="outline" className={
                result.source === "local"
                  ? "bg-emerald-100 text-emerald-700 border-emerald-200"
                  : "bg-blue-100 text-blue-700 border-blue-200"
              }>
                {result.source === "local" ? (
                  <span className="flex items-center gap-1"><Database className="h-3 w-3" /> Local TF-IDF + LogReg</span>
                ) : (
                  <span className="flex items-center gap-1"><Sparkles className="h-3 w-3" /> Gemini fallback</span>
                )}
              </Badge>
              <span className="text-xs text-muted-foreground">Model: {result.model_version}</span>
            </CardContent>
          </Card>

          {result.top_categories.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Tag className="h-5 w-5" /> Top {result.top_categories.length} Predictions
                </CardTitle>
                <CardDescription>
                  Ranked by confidence. Categories above the threshold ({result.categories.length}) are bolded.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {result.top_categories.map((tc) => {
                  const aboveThreshold = result.categories.includes(tc.label);
                  return (
                    <div key={tc.label} className="flex items-center gap-3">
                      <span
                        className={`min-w-[180px] rounded px-3 py-1 text-sm capitalize ${
                          aboveThreshold
                            ? "bg-primary/15 font-semibold text-primary"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        {tc.label}
                      </span>
                      <div className="flex-1 h-2 rounded-full bg-secondary overflow-hidden">
                        <div
                          className={`h-2 ${aboveThreshold ? "bg-primary" : "bg-muted-foreground/40"}`}
                          style={{ width: `${(tc.confidence * 100).toFixed(0)}%` }}
                        />
                      </div>
                      <span className="text-sm text-muted-foreground tabular-nums w-12 text-right">
                        {(tc.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          )}

          {result.top_categories.length === 0 && (
            <Card>
              <CardContent className="py-6 text-center text-sm text-muted-foreground">
                No categories matched. Try pasting a longer paper abstract.
              </CardContent>
            </Card>
          )}

          {/* Related SLIIT papers — surfaced from the 4,219-paper SBERT index */}
          {result.related_papers && result.related_papers.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <BookOpen className="h-5 w-5" /> Related SLIIT Papers
                </CardTitle>
                <CardDescription>
                  Papers from the SLIIT research library most semantically similar to your input.
                  Useful for finding existing work in the same area.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {result.related_papers.map((p) => (
                  <div key={p.paper_id} className="rounded-md border bg-muted/30 p-3 text-sm space-y-1">
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-medium flex-1">{p.title}</p>
                      <Badge variant="secondary" className="text-[10px] shrink-0">
                        {(p.similarity * 100).toFixed(0)}% match
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {(p.authors || []).slice(0, 3).join(", ") || "Unknown authors"}
                      {p.year ? ` · ${p.year}` : ""}
                    </p>
                    {p.abstract_excerpt && (
                      <p className="text-xs italic text-muted-foreground">
                        {p.abstract_excerpt}
                      </p>
                    )}
                    {p.url && (
                      <a
                        href={p.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                      >
                        View on SLIIT RDA <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

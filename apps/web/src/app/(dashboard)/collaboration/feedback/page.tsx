"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface FeedbackResponse {
  overall_sentiment: string;
  overall_score: number;
  aspects: {
    methodology: string;
    writing: string;
    originality: string;
    data_analysis: string;
  };
  aspect_probabilities: Record<string, Record<string, number>> | null;
}

const sentimentColor = (s: string) => {
  if (s === "positive") return "text-green-600 bg-green-50 dark:bg-green-950";
  if (s === "negative") return "text-red-600 bg-red-50 dark:bg-red-950";
  return "text-yellow-600 bg-yellow-50 dark:bg-yellow-950";
};

export default function FeedbackAnalysisPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<FeedbackResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<FeedbackResponse>(API_ROUTES.module2.analyzeFeedback, { feedback_text: text });
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
        <h1 className="text-2xl font-bold">Feedback Sentiment Analysis</h1>
        <p className="text-muted-foreground">Analyze academic feedback across four aspects: methodology, writing, originality, and data analysis.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Feedback Text</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="feedback">Paste supervisor or peer feedback</Label>
            <textarea
              id="feedback"
              className="flex min-h-[150px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="The methodology is well-structured but the writing needs improvement..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          </div>
          <Button onClick={handleAnalyze} disabled={loading || !text.trim()}>
            {loading ? "Analyzing..." : "Analyze Feedback"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                Overall: <span className={`capitalize ${sentimentColor(result.overall_sentiment)} px-2 py-1 rounded`}>{result.overall_sentiment}</span>
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  (score: {result.overall_score.toFixed(2)})
                </span>
              </CardTitle>
            </CardHeader>
          </Card>

          <div className="grid gap-4 sm:grid-cols-2">
            {Object.entries(result.aspects).map(([aspect, sentiment]) => (
              <Card key={aspect}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base capitalize">{aspect.replace("_", " ")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <span className={`capitalize rounded px-3 py-1 text-sm font-medium ${sentimentColor(sentiment)}`}>
                    {sentiment}
                  </span>
                  {result.aspect_probabilities?.[aspect] && (
                    <div className="mt-3 space-y-1">
                      {Object.entries(result.aspect_probabilities[aspect]).map(([label, prob]) => (
                        <div key={label} className="flex items-center gap-2">
                          <span className="w-16 text-xs text-muted-foreground capitalize">{label}</span>
                          <div className="flex-1 h-2 rounded-full bg-secondary">
                            <div
                              className="h-2 rounded-full bg-primary"
                              style={{ width: `${(prob * 100).toFixed(0)}%` }}
                            />
                          </div>
                          <span className="text-xs w-10 text-right">{(prob * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

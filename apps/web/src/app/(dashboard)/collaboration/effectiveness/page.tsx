"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiGet } from "@/lib/api";

interface EffectivenessResponse {
  supervisor_id: string;
  overall_score: number;
  completion_rate: number;
  avg_feedback_sentiment: number;
  student_satisfaction: number;
  breakdown: Record<string, number>;
}

export default function EffectivenessPage() {
  const [supervisorId, setSupervisorId] = useState("");
  const [result, setResult] = useState<EffectivenessResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFetch = async () => {
    if (!supervisorId.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiGet<EffectivenessResponse>(API_ROUTES.module2.effectiveness(supervisorId));
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch effectiveness");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Supervisor Effectiveness</h1>
        <p className="text-muted-foreground">Weighted score from completion rate, feedback sentiment, and student satisfaction.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Lookup</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="supervisor-id">Supervisor ID</Label>
            <Input id="supervisor-id" placeholder="Enter supervisor ID" value={supervisorId} onChange={(e) => setSupervisorId(e.target.value)} />
          </div>
          <Button onClick={handleFetch} disabled={loading || !supervisorId.trim()}>
            {loading ? "Loading..." : "Get Effectiveness"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <div className="grid gap-4 md:grid-cols-2">
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-3">
                Overall Score
                <span className="text-3xl font-bold">{(result.overall_score * 100).toFixed(0)}%</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-3 rounded-full bg-secondary">
                <div
                  className="h-3 rounded-full bg-primary transition-all"
                  style={{ width: `${(result.overall_score * 100).toFixed(0)}%` }}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-sm text-muted-foreground">Completion Rate</CardTitle></CardHeader>
            <CardContent><p className="text-2xl font-bold">{(result.completion_rate * 100).toFixed(0)}%</p></CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-sm text-muted-foreground">Avg Feedback Sentiment</CardTitle></CardHeader>
            <CardContent><p className="text-2xl font-bold">{result.avg_feedback_sentiment.toFixed(2)}</p></CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-sm text-muted-foreground">Student Satisfaction</CardTitle></CardHeader>
            <CardContent><p className="text-2xl font-bold">{(result.student_satisfaction * 100).toFixed(0)}%</p></CardContent>
          </Card>

          {Object.keys(result.breakdown || {}).length > 0 && (
            <Card className="md:col-span-2">
              <CardHeader><CardTitle className="text-lg">Breakdown</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {Object.entries(result.breakdown).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between text-sm">
                    <span className="capitalize">{k.replace(/_/g, " ")}</span>
                    <span className="font-medium">{typeof v === "number" ? v.toFixed(2) : String(v)}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

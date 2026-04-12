"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface QualityResponse {
  proposal_id: string;
  overall_score: number;
  originality_score: number;
  citation_impact_score: number;
  methodology_score: number;
  clarity_score: number;
  breakdown: Record<string, number>;
}

const DIMENSIONS = [
  { key: "originality_score", label: "Originality", weight: 30, color: "bg-purple-500" },
  { key: "citation_impact_score", label: "Citation Impact", weight: 25, color: "bg-blue-500" },
  { key: "methodology_score", label: "Methodology", weight: 25, color: "bg-green-500" },
  { key: "clarity_score", label: "Clarity", weight: 20, color: "bg-amber-500" },
] as const;

export default function QualityScoresPage() {
  const [proposalId, setProposalId] = useState("");
  const [result, setResult] = useState<QualityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleScore = async () => {
    if (!proposalId.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<QualityResponse>(API_ROUTES.module4.qualityScore, {
        proposal_id: proposalId,
        user_id: "current",
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Scoring failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Quality Scoring</h1>
        <p className="text-muted-foreground">Weighted multi-dimensional quality evaluation across originality, citation impact, methodology, and clarity.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Evaluate Proposal</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="proposal-id">Proposal ID</Label>
            <Input id="proposal-id" placeholder="Enter proposal ID" value={proposalId} onChange={(e) => setProposalId(e.target.value)} />
          </div>
          <Button onClick={handleScore} disabled={loading || !proposalId.trim()}>
            {loading ? "Scoring..." : "Score Proposal"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-3">
                Overall Quality
                <span className="text-3xl font-bold">{(result.overall_score * 100).toFixed(0)}%</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-4 rounded-full bg-secondary">
                <div className="h-4 rounded-full bg-primary transition-all" style={{ width: `${(result.overall_score * 100).toFixed(0)}%` }} />
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            {DIMENSIONS.map((dim) => {
              const value = (result[dim.key as keyof QualityResponse] as number) || 0;
              return (
                <Card key={dim.key}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm">{dim.label}</CardTitle>
                      <span className="text-xs text-muted-foreground">Weight: {dim.weight}%</span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="mb-2 text-2xl font-bold">{(value * 100).toFixed(0)}%</p>
                    <div className="h-2 rounded-full bg-secondary">
                      <div className={`h-2 rounded-full ${dim.color} transition-all`} style={{ width: `${(value * 100).toFixed(0)}%` }} />
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {Object.keys(result.breakdown || {}).length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-lg">Details</CardTitle></CardHeader>
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
        </>
      )}
    </div>
  );
}

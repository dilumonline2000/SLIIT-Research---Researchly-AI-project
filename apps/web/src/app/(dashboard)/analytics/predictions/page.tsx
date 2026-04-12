"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface RiskFactor {
  factor: string;
  severity: string;
  description: string;
}

interface PredictResponse {
  proposal_id: string;
  success_probability: number;
  risk_level: string;
  risk_factors: RiskFactor[];
  recommendations: string[];
  model_type: string;
}

const riskColors: Record<string, string> = {
  low: "text-green-600 bg-green-50 dark:bg-green-950",
  medium: "text-yellow-600 bg-yellow-50 dark:bg-yellow-950",
  high: "text-orange-600 bg-orange-50 dark:bg-orange-950",
  critical: "text-red-600 bg-red-50 dark:bg-red-950",
};

export default function PredictPage() {
  const [proposalId, setProposalId] = useState("");
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handlePredict = async () => {
    if (!proposalId.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<PredictResponse>(API_ROUTES.module4.predict, {
        proposal_id: proposalId,
        user_id: "current",
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Success Prediction</h1>
        <p className="text-muted-foreground">Predict research project outcome with actionable recommendations.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Proposal</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="proposal-id">Proposal ID</Label>
            <Input id="proposal-id" placeholder="Enter your proposal ID" value={proposalId} onChange={(e) => setProposalId(e.target.value)} />
          </div>
          <Button onClick={handlePredict} disabled={loading || !proposalId.trim()}>
            {loading ? "Predicting..." : "Run Prediction"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-3">
                Success Probability
                <span className="text-3xl font-bold">{(result.success_probability * 100).toFixed(0)}%</span>
                <span className={`capitalize rounded px-3 py-1 text-sm font-medium ${riskColors[result.risk_level] || ""}`}>
                  {result.risk_level} risk
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-4 rounded-full bg-secondary">
                <div
                  className={`h-4 rounded-full transition-all ${
                    result.success_probability >= 0.75 ? "bg-green-500"
                    : result.success_probability >= 0.5 ? "bg-yellow-500"
                    : "bg-red-500"
                  }`}
                  style={{ width: `${(result.success_probability * 100).toFixed(0)}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-muted-foreground">Model: {result.model_type}</p>
            </CardContent>
          </Card>

          {result.risk_factors.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-lg">Risk Factors</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {result.risk_factors.map((rf, i) => (
                  <div key={i} className="flex items-start gap-3 rounded border p-3">
                    <span className={`rounded px-2 py-0.5 text-xs font-medium capitalize ${riskColors[rf.severity] || ""}`}>
                      {rf.severity}
                    </span>
                    <div>
                      <p className="text-sm font-medium">{rf.factor.replace(/_/g, " ")}</p>
                      <p className="text-xs text-muted-foreground">{rf.description}</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {result.recommendations.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-lg">Recommendations</CardTitle></CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {result.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <span className="mt-1 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                      {rec}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

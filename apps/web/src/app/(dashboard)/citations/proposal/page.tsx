"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface GeneratedProposal {
  problem_statement: string;
  objectives: string[];
  methodology: string;
  expected_outcomes: string;
  retrieved_paper_ids: string[];
}

export default function ProposalGeneratorPage() {
  const [topic, setTopic] = useState("");
  const [domain, setDomain] = useState("");
  const [result, setResult] = useState<GeneratedProposal | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<GeneratedProposal>(API_ROUTES.module1.generateProposal, {
        topic,
        domain: domain || undefined,
        user_id: "current",
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Generation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Proposal Generator</h1>
        <p className="text-muted-foreground">Generate a structured research proposal outline using AI.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Research Details</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="topic">Research topic</Label>
            <Input id="topic" placeholder="e.g., Privacy-preserving federated learning" value={topic} onChange={(e) => setTopic(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="domain">Domain (optional)</Label>
            <Input id="domain" placeholder="e.g., Computer Science, Healthcare" value={domain} onChange={(e) => setDomain(e.target.value)} />
          </div>
          <Button onClick={handleGenerate} disabled={loading || !topic.trim()}>
            {loading ? "Generating..." : "Generate Proposal"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle className="text-lg">Problem Statement</CardTitle></CardHeader>
            <CardContent><p className="text-sm">{result.problem_statement}</p></CardContent>
          </Card>
          {result.objectives.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-lg">Objectives</CardTitle></CardHeader>
              <CardContent>
                <ol className="list-decimal list-inside space-y-1 text-sm">
                  {result.objectives.map((obj, i) => <li key={i}>{obj}</li>)}
                </ol>
              </CardContent>
            </Card>
          )}
          {result.methodology && (
            <Card>
              <CardHeader><CardTitle className="text-lg">Methodology</CardTitle></CardHeader>
              <CardContent><p className="text-sm">{result.methodology}</p></CardContent>
            </Card>
          )}
          {result.expected_outcomes && (
            <Card>
              <CardHeader><CardTitle className="text-lg">Expected Outcomes</CardTitle></CardHeader>
              <CardContent><p className="text-sm">{result.expected_outcomes}</p></CardContent>
            </Card>
          )}
          {result.retrieved_paper_ids.length > 0 && (
            <p className="text-xs text-muted-foreground">Based on {result.retrieved_paper_ids.length} retrieved papers</p>
          )}
        </div>
      )}
    </div>
  );
}

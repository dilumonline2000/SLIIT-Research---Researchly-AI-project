"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface SupervisorMatch {
  supervisor_id: number;
  name: string;
  email: string;
  department: string;
  research_cluster: string;
  research_interests: string[];
  similarity_score: number;
  multi_factor_score: number;
  explanation: string;
  availability: boolean;
  current_students: number;
  max_students: number;
}

export default function SupervisorMatchingPage() {
  const [interests, setInterests] = useState("");
  const [abstract, setAbstract] = useState("");
  const [matches, setMatches] = useState<SupervisorMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleMatch = async () => {
    if (!interests.trim() && !abstract.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<{ matches: SupervisorMatch[] }>(API_ROUTES.module2.matchSupervisors, {
        student_id: "current",
        research_interests: interests.split(",").map(s => s.trim()).filter(Boolean),
        abstract: abstract || undefined,
        top_k: 5,
      });
      setMatches(data.matches);
    } catch (err: any) {
      setError(err.message || "Matching failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Supervisor Matching</h1>
        <p className="text-muted-foreground">Find supervisors aligned with your research interests.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Your Research Profile</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="interests">Research interests (comma-separated)</Label>
            <Input id="interests" placeholder="e.g., Machine Learning, NLP, Computer Vision" value={interests} onChange={(e) => setInterests(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="abstract">Research abstract (optional)</Label>
            <textarea
              id="abstract"
              className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Describe your research focus..."
              value={abstract}
              onChange={(e) => setAbstract(e.target.value)}
            />
          </div>
          <Button onClick={handleMatch} disabled={loading}>
            {loading ? "Finding matches..." : "Find Supervisors"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {matches.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Top Matches</h2>
          {matches.map((m, i) => (
            <Card key={m.supervisor_id}>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">{i + 1}</span>
                  {m.name}
                  <span className="ml-auto text-sm font-normal text-muted-foreground">
                    Score: {(m.multi_factor_score * 100).toFixed(0)}%
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm">{m.explanation}</p>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Email:</span>
                    <span className="font-medium">{m.email}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Department:</span>
                    <span className="font-medium">{m.department}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Cluster:</span>
                    <span className="font-medium">{m.research_cluster}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Similarity:</span>
                    <span className="font-medium">{(m.similarity_score * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Availability:</span>
                    <span className={`font-medium ${m.availability ? "text-green-600" : "text-red-600"}`}>
                      {m.availability ? `Available (${m.max_students - m.current_students} slots)` : "Not available"}
                    </span>
                  </div>
                </div>
                {m.research_interests.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Research Interests:</span>
                    <div className="flex flex-wrap gap-2">
                      {m.research_interests.map((interest) => (
                        <span key={interest} className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
                          {interest}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

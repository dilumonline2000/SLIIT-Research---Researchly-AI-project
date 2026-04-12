"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface ConceptNode { id: string; concept: string; importance: number; domain_cluster: string; }
interface ConceptEdge { source: string; target: string; relationship_strength: number; }
interface ConceptMap { nodes: ConceptNode[]; edges: ConceptEdge[]; }

const clusterColors: Record<string, string> = {
  ml: "bg-purple-500",
  nlp: "bg-blue-500",
  cv: "bg-green-500",
  systems: "bg-amber-500",
  theory: "bg-pink-500",
  default: "bg-gray-500",
};

export default function MindMapsPage() {
  const [topic, setTopic] = useState("");
  const [department, setDepartment] = useState("");
  const [maxNodes, setMaxNodes] = useState(30);
  const [result, setResult] = useState<ConceptMap | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<ConceptMap>(API_ROUTES.module4.mindmap, {
        topic: topic || undefined,
        department: department || undefined,
        max_nodes: maxNodes,
      });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Mind map generation failed");
    } finally {
      setLoading(false);
    }
  };

  const colorFor = (cluster: string) =>
    clusterColors[cluster?.toLowerCase()] || clusterColors.default;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Concept Mind Maps</h1>
        <p className="text-muted-foreground">GNN-based concept graph expansion from a topic or department seed.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Generate</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="topic">Topic (optional)</Label>
            <Input id="topic" placeholder="e.g., federated learning" value={topic} onChange={(e) => setTopic(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="department">Department (optional)</Label>
            <Input id="department" placeholder="e.g., Computer Science" value={department} onChange={(e) => setDepartment(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="max">Max Nodes</Label>
            <Input id="max" type="number" min={5} max={200} value={maxNodes} onChange={(e) => setMaxNodes(Number(e.target.value))} className="w-32" />
          </div>
          <Button onClick={handleGenerate} disabled={loading}>
            {loading ? "Building..." : "Generate Mind Map"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {result && result.nodes.length > 0 && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Concepts ({result.nodes.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {result.nodes
                  .slice()
                  .sort((a, b) => b.importance - a.importance)
                  .map((n) => {
                    const size = 10 + Math.round(n.importance * 20);
                    return (
                      <div
                        key={n.id}
                        className={`rounded-full px-3 py-1 text-white ${colorFor(n.domain_cluster)}`}
                        style={{ fontSize: `${size}px` }}
                        title={`${n.domain_cluster} · importance ${n.importance.toFixed(2)}`}
                      >
                        {n.concept}
                      </div>
                    );
                  })}
              </div>
            </CardContent>
          </Card>

          {result.edges.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-lg">Relationships ({result.edges.length})</CardTitle></CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="pb-2 pr-4">Source</th>
                        <th className="pb-2 pr-4">Target</th>
                        <th className="pb-2">Strength</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.edges
                        .slice()
                        .sort((a, b) => b.relationship_strength - a.relationship_strength)
                        .slice(0, 50)
                        .map((e, i) => {
                          const srcNode = result.nodes.find((n) => n.id === e.source);
                          const tgtNode = result.nodes.find((n) => n.id === e.target);
                          return (
                            <tr key={`${e.source}-${e.target}-${i}`} className="border-b border-border/50">
                              <td className="py-1.5 pr-4">{srcNode?.concept || e.source}</td>
                              <td className="py-1.5 pr-4">{tgtNode?.concept || e.target}</td>
                              <td className="py-1.5">{e.relationship_strength.toFixed(2)}</td>
                            </tr>
                          );
                        })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {result && result.nodes.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">No concepts generated. Try providing a topic seed or ensure the GNN model is trained.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

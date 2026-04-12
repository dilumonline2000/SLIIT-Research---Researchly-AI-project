"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface MindMapNode {
  id: string;
  label: string;
  type: string;
  weight: number;
}

interface MindMapEdge {
  source: string;
  target: string;
  weight: number;
}

interface MindMapResponse {
  nodes: MindMapNode[];
  edges: MindMapEdge[];
}

export default function MindMapPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<MindMapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (text.trim().length < 50) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<MindMapResponse>(API_ROUTES.module1.generateMindMap, { text, max_nodes: 20 });
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
        <h1 className="text-2xl font-bold">Mind Map Builder</h1>
        <p className="text-muted-foreground">Extract key concepts and visualize relationships.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Input Text</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="mindmap-text">Research text or abstract</Label>
            <textarea
              id="mindmap-text"
              className="flex min-h-[150px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Paste your research abstract or paper section (minimum 50 characters)..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          </div>
          <Button onClick={handleGenerate} disabled={loading || text.trim().length < 50}>
            {loading ? "Generating..." : "Build Mind Map"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {result && result.nodes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              Concept Map ({result.nodes.length} concepts, {result.edges.length} connections)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3 mb-6">
              {result.nodes.map((node) => (
                <div
                  key={node.id}
                  className={`rounded-full px-4 py-2 text-sm font-medium transition-all ${
                    node.type === "central"
                      ? "bg-primary text-primary-foreground shadow-md"
                      : "bg-secondary text-secondary-foreground"
                  }`}
                  style={{ fontSize: `${Math.max(12, 14 + node.weight * 4)}px` }}
                >
                  {node.label}
                </div>
              ))}
            </div>
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">Connections:</p>
              <div className="grid gap-1 sm:grid-cols-2 lg:grid-cols-3">
                {result.edges.map((edge, i) => {
                  const source = result.nodes.find(n => n.id === edge.source);
                  const target = result.nodes.find(n => n.id === edge.target);
                  return (
                    <p key={i} className="text-xs text-muted-foreground">
                      {source?.label} — {target?.label} ({(edge.weight * 100).toFixed(0)}%)
                    </p>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

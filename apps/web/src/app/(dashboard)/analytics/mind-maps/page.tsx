"use client";

import { useState, useRef, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Network, Sparkles, AlertCircle, Download } from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";
import { MindMapGraph, type GraphNode, type GraphLink } from "@/components/shared/MindMapGraph";

interface ConceptNode {
  id: string;
  concept: string;
  importance: number;
  domain_cluster: string;
}

interface ConceptEdge {
  source: string;
  target: string;
  relationship_strength: number;
}

interface ConceptMap {
  nodes: ConceptNode[];
  edges: ConceptEdge[];
}

const CLUSTER_COLORS: Record<string, string> = {
  ml: "#9333ea",
  nlp: "#2563eb",
  cv: "#10b981",
  systems: "#f59e0b",
  theory: "#ec4899",
  default: "#6b7280",
};

function colorFor(cluster: string) {
  return CLUSTER_COLORS[cluster?.toLowerCase()] || CLUSTER_COLORS.default;
}

export default function MindMapsPage() {
  const [topic, setTopic] = useState("");
  const [department, setDepartment] = useState("");
  const [maxNodes, setMaxNodes] = useState(30);
  const [result, setResult] = useState<ConceptMap | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  const graphNodes = useMemo<GraphNode[]>(() => {
    if (!result) return [];
    return result.nodes.map((n) => ({
      id: n.id,
      label: n.concept,
      color: colorFor(n.domain_cluster),
      val: 8 + n.importance * 32,
    }));
  }, [result]);

  const graphLinks = useMemo<GraphLink[]>(() => {
    if (!result) return [];
    return result.edges.map((e) => ({
      source: e.source,
      target: e.target,
      weight: e.relationship_strength,
    }));
  }, [result]);

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await apiPost<ConceptMap>(API_ROUTES.module4.mindmap, {
        topic: topic || undefined,
        department: department || undefined,
        max_nodes: maxNodes,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Mind map generation failed");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    if (!result || !containerRef.current) return;
    const svgEl = containerRef.current.querySelector("svg");
    if (!svgEl) return;
    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(svgEl);
    const blob = new Blob([svgStr], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `concept-map-${Date.now()}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const graphWidth = 860;
  const graphHeight = 580;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Network className="h-6 w-6" /> Concept Mind Maps
        </h1>
        <p className="text-muted-foreground">
          GNN-based concept graph expansion from a topic or department seed.
          Hover over nodes to highlight relationships.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Generate Concept Map</CardTitle>
          <CardDescription>Provide a topic or department to seed the graph</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="topic">Topic</Label>
              <Input
                id="topic"
                placeholder="e.g., federated learning"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="department">Department</Label>
              <Input
                id="department"
                placeholder="e.g., Computer Science"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="max">Max Nodes</Label>
              <Input
                id="max"
                type="number"
                min={5}
                max={100}
                value={maxNodes}
                onChange={(e) => setMaxNodes(Number(e.target.value))}
              />
            </div>
          </div>
          <Button onClick={handleGenerate} disabled={loading}>
            {loading ? "Building..." : (
              <>
                <Sparkles className="mr-2 h-4 w-4" /> Generate Mind Map
              </>
            )}
          </Button>
          {error && (
            <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {result && result.nodes.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">Interactive Concept Graph</CardTitle>
                <CardDescription>
                  {result.nodes.length} concepts · {result.edges.length} relationships · hover to explore
                </CardDescription>
              </div>
              <Button size="sm" variant="outline" onClick={handleExport}>
                <Download className="mr-2 h-4 w-4" /> Export SVG
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div
              ref={containerRef}
              className="rounded-lg border bg-gradient-to-br from-slate-50 to-purple-50 overflow-hidden"
              style={{ height: graphHeight }}
            >
              <MindMapGraph
                nodes={graphNodes}
                links={graphLinks}
                width={graphWidth}
                height={graphHeight}
              />
            </div>

            {/* Cluster legend */}
            <div className="mt-3 flex flex-wrap gap-3 text-xs">
              {Object.entries(CLUSTER_COLORS).filter(([k]) => k !== "default").map(([cluster, color]) => (
                <div key={cluster} className="flex items-center gap-1.5">
                  <div className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
                  <span className="uppercase text-muted-foreground">{cluster}</span>
                </div>
              ))}
            </div>

            {/* Top concepts */}
            <div className="mt-4">
              <p className="mb-2 text-sm font-medium">Top concepts by importance:</p>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {result.nodes
                  .slice()
                  .sort((a, b) => b.importance - a.importance)
                  .slice(0, 12)
                  .map((n) => (
                    <div key={n.id} className="rounded-md border bg-card p-2 text-xs">
                      <div className="flex items-center gap-2">
                        <div
                          className="h-2.5 w-2.5 rounded-full shrink-0"
                          style={{ backgroundColor: colorFor(n.domain_cluster) }}
                        />
                        <span className="font-medium truncate">{n.concept}</span>
                      </div>
                      <p className="mt-0.5 uppercase text-muted-foreground">
                        {n.domain_cluster} · {(n.importance * 100).toFixed(0)}%
                      </p>
                    </div>
                  ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {result && result.nodes.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">
              No concepts generated. Try providing a topic seed or ensure the GNN model is trained.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

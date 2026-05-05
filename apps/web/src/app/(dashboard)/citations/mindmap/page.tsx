"use client";

import { useState, useRef, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Network, Sparkles, AlertCircle, Download } from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";
import { MindMapGraph, type GraphNode, type GraphLink } from "@/components/shared/MindMapGraph";

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

const NODE_COLORS: Record<string, string> = {
  central: "#9333ea",
  primary: "#2563eb",
  secondary: "#0891b2",
  detail: "#64748b",
  default: "#6b7280",
};

export default function MindMapPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<MindMapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  const graphNodes = useMemo<GraphNode[]>(() => {
    if (!result) return [];
    return result.nodes.map((n) => ({
      id: n.id,
      label: n.label,
      color: NODE_COLORS[n.type] || NODE_COLORS.default,
      val: 8 + n.weight * 30,
    }));
  }, [result]);

  const graphLinks = useMemo<GraphLink[]>(() => {
    if (!result) return [];
    return result.edges.map((e) => ({
      source: e.source,
      target: e.target,
      weight: e.weight,
    }));
  }, [result]);

  const handleGenerate = async () => {
    if (text.trim().length < 50) {
      setError("Please enter at least 50 characters of research text");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await apiPost<MindMapResponse>(API_ROUTES.module1.generateMindMap, {
        text,
        max_nodes: 25,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  };

  const handleExportSVG = () => {
    if (!result || !containerRef.current) return;
    const svgEl = containerRef.current.querySelector("svg");
    if (!svgEl) return;
    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(svgEl);
    const blob = new Blob([svgStr], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `mindmap-${Date.now()}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const graphWidth = 800;
  const graphHeight = 560;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Network className="h-6 w-6" /> Mind Map Builder
        </h1>
        <p className="text-muted-foreground">
          Extract key concepts and visualize relationships as an interactive graph.
          Hover over nodes to highlight connections.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Input Research Text</CardTitle>
          <CardDescription>Paste an abstract or paper section (≥ 50 characters)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="mindmap-text">Text</Label>
            <textarea
              id="mindmap-text"
              className="flex min-h-[150px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Paste your research abstract or paper section..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">{text.length} characters</p>
          </div>
          <Button onClick={handleGenerate} disabled={loading || text.trim().length < 50}>
            {loading ? "Generating..." : (
              <>
                <Sparkles className="mr-2 h-4 w-4" /> Build Mind Map
              </>
            )}
          </Button>
          {error && (
            <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
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
                <CardTitle className="text-lg">Concept Graph</CardTitle>
                <CardDescription>
                  {result.nodes.length} concepts · {result.edges.length} connections · hover to explore
                </CardDescription>
              </div>
              <Button size="sm" variant="outline" onClick={handleExportSVG}>
                <Download className="mr-2 h-4 w-4" /> Export SVG
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div
              ref={containerRef}
              className="rounded-lg border bg-gradient-to-br from-slate-50 to-blue-50 overflow-hidden"
              style={{ height: graphHeight }}
            >
              <MindMapGraph
                nodes={graphNodes}
                links={graphLinks}
                width={graphWidth}
                height={graphHeight}
              />
            </div>

            {/* Legend */}
            <div className="mt-3 flex flex-wrap gap-3 text-xs">
              {Object.entries(NODE_COLORS).filter(([k]) => k !== "default").map(([type, color]) => (
                <div key={type} className="flex items-center gap-1.5">
                  <div className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
                  <span className="capitalize text-muted-foreground">{type}</span>
                </div>
              ))}
            </div>

            {/* Concept list */}
            <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {result.nodes
                .slice()
                .sort((a, b) => b.weight - a.weight)
                .slice(0, 12)
                .map((n) => (
                  <div key={n.id} className="rounded-md border bg-card p-2 text-xs">
                    <div className="flex items-center gap-2">
                      <div
                        className="h-2.5 w-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: NODE_COLORS[n.type] || NODE_COLORS.default }}
                      />
                      <span className="font-medium">{n.label}</span>
                    </div>
                    <p className="mt-0.5 capitalize text-muted-foreground">
                      {n.type} · weight {(n.weight * 100).toFixed(0)}%
                    </p>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Network, Sparkles, AlertCircle, Maximize2, Download } from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

// Dynamic import - react-force-graph requires window/canvas
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

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

interface GraphNode {
  id: string;
  label: string;
  type: string;
  weight: number;
  val: number;
  color: string;
}

interface GraphLink {
  source: string;
  target: string;
  weight: number;
}

const NODE_COLORS: Record<string, string> = {
  central: "#9333ea",     // purple
  primary: "#2563eb",     // blue
  secondary: "#0891b2",   // cyan
  detail: "#64748b",      // slate
  default: "#6b7280",
};


export default function MindMapPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<MindMapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<unknown>(null);

  useEffect(() => {
    const updateDims = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: 600,
        });
      }
    };
    updateDims();
    window.addEventListener("resize", updateDims);
    return () => window.removeEventListener("resize", updateDims);
  }, [result]);

  const graphData = useMemo(() => {
    if (!result) return { nodes: [], links: [] };
    const nodes: GraphNode[] = result.nodes.map((n) => ({
      id: n.id,
      label: n.label,
      type: n.type,
      weight: n.weight,
      val: 4 + n.weight * 12,
      color: NODE_COLORS[n.type] || NODE_COLORS.default,
    }));
    const links: GraphLink[] = result.edges.map((e) => ({
      source: e.source,
      target: e.target,
      weight: e.weight,
    }));
    return { nodes, links };
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
    if (!result) return;
    // Build a simple SVG representation
    const w = 1200;
    const h = 800;
    const cx = w / 2;
    const cy = h / 2;
    const nodes = result.nodes;
    const r = 320;
    const positions = new Map<string, { x: number; y: number }>();
    nodes.forEach((n, i) => {
      if (n.type === "central") {
        positions.set(n.id, { x: cx, y: cy });
      } else {
        const angle = (i / Math.max(1, nodes.length - 1)) * 2 * Math.PI;
        positions.set(n.id, {
          x: cx + Math.cos(angle) * r,
          y: cy + Math.sin(angle) * r,
        });
      }
    });

    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">`;
    svg += `<rect width="${w}" height="${h}" fill="white"/>`;
    // Edges
    result.edges.forEach((e) => {
      const s = positions.get(e.source);
      const t = positions.get(e.target);
      if (s && t) {
        svg += `<line x1="${s.x}" y1="${s.y}" x2="${t.x}" y2="${t.y}" stroke="#cbd5e1" stroke-width="${1 + e.weight * 3}"/>`;
      }
    });
    // Nodes
    nodes.forEach((n) => {
      const p = positions.get(n.id);
      if (!p) return;
      const color = NODE_COLORS[n.type] || NODE_COLORS.default;
      const radius = 22 + n.weight * 12;
      svg += `<circle cx="${p.x}" cy="${p.y}" r="${radius}" fill="${color}" opacity="0.85"/>`;
      svg += `<text x="${p.x}" y="${p.y + 4}" text-anchor="middle" font-family="sans-serif" font-size="13" font-weight="bold" fill="white">${n.label.replace(/[<>&]/g, "")}</text>`;
    });
    svg += "</svg>";

    const blob = new Blob([svg], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `mindmap-${Date.now()}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Network className="h-6 w-6" /> Mind Map Builder
        </h1>
        <p className="text-muted-foreground">
          Extract key concepts and visualize relationships as an interactive graph.
          Drag nodes, zoom, and pan to explore.
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
                <CardTitle className="text-lg">
                  Concept Graph
                </CardTitle>
                <CardDescription>
                  {result.nodes.length} concepts · {result.edges.length} connections · drag to explore
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={handleExportSVG}>
                  <Download className="mr-2 h-4 w-4" /> Export SVG
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    const ref = graphRef.current as { zoomToFit?: (ms: number, padding: number) => void } | null;
                    ref?.zoomToFit?.(400, 50);
                  }}
                >
                  <Maximize2 className="mr-2 h-4 w-4" /> Fit to View
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div
              ref={containerRef}
              className="rounded-lg border bg-gradient-to-br from-slate-50 to-blue-50 overflow-hidden"
              style={{ height: 600 }}
            >
              <ForceGraph2D
                ref={graphRef as React.MutableRefObject<unknown>}
                graphData={graphData}
                width={dimensions.width}
                height={dimensions.height}
                nodeLabel={(n: object) => (n as GraphNode).label}
                nodeColor={(n: object) => (n as GraphNode).color}
                nodeVal={(n: object) => (n as GraphNode).val}
                linkWidth={(l: object) => 1 + (l as GraphLink).weight * 4}
                linkColor={() => "rgba(100, 116, 139, 0.4)"}
                linkDirectionalParticles={2}
                linkDirectionalParticleSpeed={0.005}
                linkDirectionalParticleColor={() => "#9333ea"}
                nodeCanvasObject={(node: object, ctx: CanvasRenderingContext2D, globalScale: number) => {
                  const n = node as GraphNode & { x?: number; y?: number };
                  const fontSize = 12 / globalScale;
                  const radius = n.val;
                  ctx.beginPath();
                  ctx.arc(n.x || 0, n.y || 0, radius, 0, 2 * Math.PI);
                  ctx.fillStyle = n.color;
                  ctx.fill();
                  ctx.strokeStyle = "#fff";
                  ctx.lineWidth = 2 / globalScale;
                  ctx.stroke();
                  // Label
                  ctx.font = `${fontSize}px sans-serif`;
                  ctx.textAlign = "center";
                  ctx.textBaseline = "middle";
                  ctx.fillStyle = "#fff";
                  ctx.fillText(n.label, n.x || 0, n.y || 0);
                }}
                cooldownTicks={100}
                onEngineStop={() => {
                  const ref = graphRef.current as { zoomToFit?: (ms: number, padding: number) => void } | null;
                  ref?.zoomToFit?.(400, 60);
                }}
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
                      className="h-2.5 w-2.5 rounded-full"
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

"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Network, Sparkles, AlertCircle, Maximize2, Download } from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

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

interface GraphNode {
  id: string;
  label: string;
  cluster: string;
  importance: number;
  val: number;
  color: string;
}
interface GraphLink {
  source: string;
  target: string;
  weight: number;
}

export default function MindMapsPage() {
  const [topic, setTopic] = useState("");
  const [department, setDepartment] = useState("");
  const [maxNodes, setMaxNodes] = useState(30);
  const [result, setResult] = useState<ConceptMap | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
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

  const colorFor = (cluster: string) =>
    CLUSTER_COLORS[cluster?.toLowerCase()] || CLUSTER_COLORS.default;

  const graphData = useMemo(() => {
    if (!result) return { nodes: [], links: [] };
    const nodes: GraphNode[] = result.nodes.map((n) => ({
      id: n.id,
      label: n.concept,
      cluster: n.domain_cluster,
      importance: n.importance,
      val: 4 + n.importance * 16,
      color: colorFor(n.domain_cluster),
    }));
    const links: GraphLink[] = result.edges.map((e) => ({
      source: e.source,
      target: e.target,
      weight: e.relationship_strength,
    }));
    return { nodes, links };
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
    if (!result) return;
    const w = 1400;
    const h = 900;
    const cx = w / 2;
    const cy = h / 2;
    const r = 380;
    const positions = new Map<string, { x: number; y: number }>();
    result.nodes.forEach((n, i) => {
      const angle = (i / result.nodes.length) * 2 * Math.PI;
      positions.set(n.id, {
        x: cx + Math.cos(angle) * r * (0.5 + n.importance * 0.5),
        y: cy + Math.sin(angle) * r * (0.5 + n.importance * 0.5),
      });
    });
    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="${w}" height="${h}" fill="white"/>`;
    result.edges.forEach((e) => {
      const s = positions.get(e.source);
      const t = positions.get(e.target);
      if (s && t) svg += `<line x1="${s.x}" y1="${s.y}" x2="${t.x}" y2="${t.y}" stroke="#cbd5e1" stroke-width="${1 + e.relationship_strength * 3}"/>`;
    });
    result.nodes.forEach((n) => {
      const p = positions.get(n.id);
      if (!p) return;
      const radius = 24 + n.importance * 14;
      svg += `<circle cx="${p.x}" cy="${p.y}" r="${radius}" fill="${colorFor(n.domain_cluster)}" opacity="0.85"/>`;
      svg += `<text x="${p.x}" y="${p.y + 4}" text-anchor="middle" font-family="sans-serif" font-size="13" font-weight="bold" fill="white">${n.concept.replace(/[<>&]/g, "")}</text>`;
    });
    svg += "</svg>";
    const blob = new Blob([svg], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `concept-map-${Date.now()}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Network className="h-6 w-6" /> Concept Mind Maps
        </h1>
        <p className="text-muted-foreground">
          GNN-based concept graph expansion from a topic or department seed. Drag,
          zoom, and pan to explore relationships.
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
              <Input id="topic" placeholder="e.g., federated learning" value={topic} onChange={(e) => setTopic(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="department">Department</Label>
              <Input id="department" placeholder="e.g., Computer Science" value={department} onChange={(e) => setDepartment(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="max">Max Nodes</Label>
              <Input id="max" type="number" min={5} max={100} value={maxNodes} onChange={(e) => setMaxNodes(Number(e.target.value))} />
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
                  {result.nodes.length} concepts · {result.edges.length} relationships
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={handleExport}>
                  <Download className="mr-2 h-4 w-4" /> Export SVG
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    const ref = graphRef.current as { zoomToFit?: (ms: number, padding: number) => void } | null;
                    ref?.zoomToFit?.(400, 60);
                  }}
                >
                  <Maximize2 className="mr-2 h-4 w-4" /> Fit
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div
              ref={containerRef}
              className="rounded-lg border bg-gradient-to-br from-slate-50 to-purple-50 overflow-hidden"
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
                linkWidth={(l: object) => 1 + (l as GraphLink).weight * 3}
                linkColor={() => "rgba(100, 116, 139, 0.4)"}
                linkDirectionalParticles={1}
                linkDirectionalParticleSpeed={0.005}
                linkDirectionalParticleColor={(l: object) => {
                  const sourceNode = graphData.nodes.find(n => n.id === (l as GraphLink).source);
                  return sourceNode?.color || "#9333ea";
                }}
                nodeCanvasObject={(node: object, ctx: CanvasRenderingContext2D, globalScale: number) => {
                  const n = node as GraphNode & { x?: number; y?: number };
                  const fontSize = 11 / globalScale;
                  const radius = n.val;
                  ctx.beginPath();
                  ctx.arc(n.x || 0, n.y || 0, radius, 0, 2 * Math.PI);
                  ctx.fillStyle = n.color;
                  ctx.fill();
                  ctx.strokeStyle = "#fff";
                  ctx.lineWidth = 2 / globalScale;
                  ctx.stroke();
                  ctx.font = `${fontSize}px sans-serif`;
                  ctx.textAlign = "center";
                  ctx.textBaseline = "middle";
                  ctx.fillStyle = "#fff";
                  // Truncate long labels
                  const label = n.label.length > 18 ? n.label.slice(0, 16) + "…" : n.label;
                  ctx.fillText(label, n.x || 0, n.y || 0);
                }}
                cooldownTicks={120}
                onEngineStop={() => {
                  const ref = graphRef.current as { zoomToFit?: (ms: number, padding: number) => void } | null;
                  ref?.zoomToFit?.(400, 80);
                }}
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

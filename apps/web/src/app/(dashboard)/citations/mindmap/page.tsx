"use client";

import { useState, useRef, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Network, Sparkles, AlertCircle, Download, Crown, Star, Layers, Dot,
  Lightbulb, ImageDown,
} from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";
import { MindMapGraph, type GraphNode, type GraphLink, type NodeType } from "@/components/shared/MindMapGraph";

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

const NODE_TYPE_META: Record<NodeType, { label: string; icon: typeof Crown; color: string; bg: string }> = {
  central:   { label: "Central concept",   icon: Crown,    color: "text-purple-700",  bg: "bg-purple-50 border-purple-200" },
  primary:   { label: "Primary themes",    icon: Star,     color: "text-blue-700",    bg: "bg-blue-50 border-blue-200" },
  secondary: { label: "Secondary themes",  icon: Layers,   color: "text-emerald-700", bg: "bg-emerald-50 border-emerald-200" },
  detail:    { label: "Details",           icon: Dot,      color: "text-orange-700",  bg: "bg-orange-50 border-orange-200" },
};

const SAMPLE_TEXT =
  "Recent advances in deep learning have enabled significant improvements in medical image classification. " +
  "Convolutional neural networks (CNNs) trained on large datasets of chest X-rays can detect COVID-19 with high accuracy. " +
  "Transfer learning from ImageNet weights, combined with data augmentation strategies, helps mitigate small-dataset limitations. " +
  "However, model generalization across hospitals remains a challenge due to scanner variability and patient demographics. " +
  "Future research should explore federated learning to preserve patient privacy while training across institutions.";

export default function MindMapPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<MindMapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  const graphNodes = useMemo<GraphNode[]>(() => {
    if (!result) return [];
    return result.nodes.map((n) => {
      const t = (["central", "primary", "secondary", "detail"] as const).includes(n.type as NodeType)
        ? (n.type as NodeType)
        : "detail";
      return {
        id: n.id,
        label: n.label,
        type: t,
        val: 8 + n.weight * 30,
      };
    });
  }, [result]);

  const graphLinks = useMemo<GraphLink[]>(() => {
    if (!result) return [];
    return result.edges.map((e) => ({
      source: e.source,
      target: e.target,
      weight: e.weight,
    }));
  }, [result]);

  // Group concepts by type for the legend grid
  const grouped = useMemo(() => {
    if (!result) return {} as Record<NodeType, MindMapNode[]>;
    const out: Record<NodeType, MindMapNode[]> = { central: [], primary: [], secondary: [], detail: [] };
    for (const n of result.nodes) {
      const t = (["central", "primary", "secondary", "detail"] as const).includes(n.type as NodeType)
        ? (n.type as NodeType)
        : "detail";
      out[t].push(n);
    }
    // sort each bucket by weight desc
    for (const k of Object.keys(out) as NodeType[]) {
      out[k] = out[k].slice().sort((a, b) => b.weight - a.weight);
    }
    return out;
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

  const handleExportPNG = async () => {
    if (!result || !containerRef.current) return;
    const svgEl = containerRef.current.querySelector("svg");
    if (!svgEl) return;
    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(svgEl);
    const svgBlob = new Blob([svgStr], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);

    const img = new Image();
    img.onload = () => {
      const scale = 2; // higher-DPI export
      const canvas = document.createElement("canvas");
      canvas.width = (svgEl.clientWidth || 800) * scale;
      canvas.height = (svgEl.clientHeight || 560) * scale;
      const ctx = canvas.getContext("2d")!;
      ctx.fillStyle = "white";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      canvas.toBlob((blob) => {
        if (!blob) return;
        const u = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = u;
        a.download = `mindmap-${Date.now()}.png`;
        a.click();
        URL.revokeObjectURL(u);
      }, "image/png");
    };
    img.src = url;
  };

  const graphWidth = 900;
  const graphHeight = 600;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-2xl bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-600 p-6 text-white shadow-lg">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Network className="h-7 w-7" /> Mind Map Builder
            </h1>
            <p className="mt-1 text-sm text-white/85 max-w-xl">
              Turn an abstract or research description into an interactive concept graph. Hover any
              node to see what it connects to — perfect for planning what to focus on, what depends
              on what, and where to dig deeper.
            </p>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            {(Object.entries(NODE_TYPE_META) as [NodeType, typeof NODE_TYPE_META.central][]).map(([key, meta]) => {
              const Icon = meta.icon;
              return (
                <span
                  key={key}
                  className="inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-1 backdrop-blur-sm"
                >
                  <Icon className="h-3 w-3" /> {meta.label}
                </span>
              );
            })}
          </div>
        </div>
      </div>

      {/* Input */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-amber-500" /> What is your research about?
          </CardTitle>
          <CardDescription>
            Paste an abstract, problem statement, or paper section (≥ 50 characters). The system
            extracts the most important concepts and shows how they relate.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="mindmap-text">Research text</Label>
            <textarea
              id="mindmap-text"
              className="flex min-h-[150px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Paste your research abstract, problem statement, or paper section..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <div className="flex items-center justify-between flex-wrap gap-2">
              <p className="text-xs text-muted-foreground">{text.length} characters</p>
              <button
                type="button"
                onClick={() => setText(SAMPLE_TEXT)}
                className="text-xs text-primary hover:underline"
              >
                Try a sample text →
              </button>
            </div>
          </div>
          <Button onClick={handleGenerate} disabled={loading || text.trim().length < 50} size="lg">
            {loading ? (
              <>
                <Sparkles className="mr-2 h-4 w-4 animate-pulse" /> Building your mind map…
              </>
            ) : (
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

      {/* Graph */}
      {result && result.nodes.length > 0 && (
        <Card className="overflow-hidden">
          <CardHeader>
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Network className="h-5 w-5 text-indigo-600" /> Concept Graph
                </CardTitle>
                <CardDescription>
                  {result.nodes.length} concepts · {result.edges.length} connections · hover to explore
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={handleExportSVG}>
                  <Download className="mr-2 h-4 w-4" /> Export SVG
                </Button>
                <Button size="sm" variant="outline" onClick={handleExportPNG}>
                  <ImageDown className="mr-2 h-4 w-4" /> Export PNG
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div
              ref={containerRef}
              className="rounded-xl border bg-gradient-to-br from-indigo-50 via-white to-purple-50 overflow-hidden shadow-inner"
              style={{ height: graphHeight }}
            >
              <MindMapGraph
                nodes={graphNodes}
                links={graphLinks}
                width={graphWidth}
                height={graphHeight}
              />
            </div>

            {/* Concept buckets — one card per type, sorted by weight */}
            <div className="mt-5 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
              {(Object.entries(NODE_TYPE_META) as [NodeType, typeof NODE_TYPE_META.central][]).map(([key, meta]) => {
                const items = grouped[key] || [];
                if (items.length === 0) return null;
                const Icon = meta.icon;
                return (
                  <div key={key} className={`rounded-lg border ${meta.bg} p-3 space-y-2`}>
                    <div className={`flex items-center gap-2 ${meta.color} font-semibold text-sm`}>
                      <Icon className="h-4 w-4" />
                      {meta.label}
                      <Badge variant="secondary" className="ml-auto text-[10px]">
                        {items.length}
                      </Badge>
                    </div>
                    <div className="space-y-1.5">
                      {items.slice(0, 6).map((n) => (
                        <div key={n.id} className="text-xs space-y-0.5">
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-medium truncate">{n.label}</span>
                            <span className="text-muted-foreground tabular-nums shrink-0">
                              {(n.weight * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="h-1.5 rounded-full bg-white/70 overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-current to-current/60"
                              style={{ width: `${n.weight * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                      {items.length > 6 && (
                        <p className="text-xs text-muted-foreground pt-1">
                          +{items.length - 6} more
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Reading guide */}
            <div className="mt-5 rounded-lg border bg-muted/30 p-3 text-xs space-y-1">
              <p className="font-medium text-foreground flex items-center gap-1.5">
                <Lightbulb className="h-3.5 w-3.5 text-amber-500" /> How to read this map
              </p>
              <ul className="text-muted-foreground space-y-0.5 list-disc pl-5">
                <li>The <strong className="text-purple-700">central</strong> node is the topic everything else hangs off — start here.</li>
                <li><strong className="text-blue-700">Primary</strong> nodes are the major themes. They tell you what to focus on first.</li>
                <li><strong className="text-emerald-700">Secondary</strong> nodes break each theme into work items.</li>
                <li><strong className="text-orange-700">Detail</strong> nodes are specifics — pick the ones that matter to your scope.</li>
                <li>Edge thickness shows how strongly two concepts are linked. Hover any node to dim everything else.</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

"use client";

import { useMemo, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Database, Sparkles, BookOpen, ExternalLink, Upload, FileText, FileUp, X,
  TrendingUp, TrendingDown, Minus, Lightbulb, AlertTriangle, Layers, Network,
  Download, Search, Filter, Copy, Check,
} from "lucide-react";
import api from "@/lib/api";
import { apiPost } from "@/lib/api";
import { API_ROUTES } from "@/lib/constants";

// ─── Types ────────────────────────────────────────────────────────────────

interface SupportingPaper {
  paper_id: string;
  title: string;
  authors: string[];
  year: number | string | null;
  url: string;
}

interface Gap {
  topic: string;
  description: string;
  gap_score: number;
  recency_score: number;
  novelty_score: number;
  similarity: number;
  gap_type: string;
  classification: string;
  category_label: string;
  multi_dim_score: number;
  explanation: string;
  supporting_paper: SupportingPaper | null;
  supporting_paper_ids: string[];
}

interface YearBucket { year: number; count: number }

interface Trends {
  by_year: YearBucket[];
  peak_year: number | null;
  peak_count: number | null;
  total_papers: number | null;
  interpretation: string;
}

interface CrossDomain {
  domain_a: string;
  domain_b: string;
  papers_in_intersection: number;
  papers_in_primary: number;
  opportunity_score: number;
  suggestion: string;
}

interface Saturation { term: string; paper_count: number; warning: string }

interface Recommendation {
  title: string;
  rationale: string;
  problem_statement: string;
  based_on: string;
  supporting_paper: SupportingPaper | null;
}

interface CategoryCount { category: string; label: string; count: number }

interface AnalyzeResponse {
  loaded: boolean;
  query: string;
  filters: { year_from?: number | null; year_to?: number | null };
  gaps: Gap[];
  classification_distribution: CategoryCount[];
  trends: Trends;
  saturation: Saturation[];
  cross_domain: CrossDomain[];
  recommendations: Recommendation[];
  total_papers_analyzed: number;
  total_corpus_size: number;
  model_version: string;
  base_model: string;
  source: string;
}

type Mode = "topic" | "pdf" | "fullPaper";

// ─── Visual constants ────────────────────────────────────────────────────

const SAMPLE_TOPICS = [
  "machine learning in healthcare",
  "blockchain supply chain transparency",
  "deep learning crop disease detection",
  "IoT security in smart cities",
  "natural language processing for Sinhala",
  "renewable energy forecasting Sri Lanka",
  "AI in agriculture",
  "fintech fraud detection",
];

const CATEGORY_STYLE: Record<string, { bg: string; text: string; border: string }> = {
  future_work: { bg: "bg-purple-50",   text: "text-purple-700",  border: "border-purple-200" },
  methodology: { bg: "bg-blue-50",     text: "text-blue-700",    border: "border-blue-200" },
  dataset:     { bg: "bg-amber-50",    text: "text-amber-700",   border: "border-amber-200" },
  domain:      { bg: "bg-emerald-50",  text: "text-emerald-700", border: "border-emerald-200" },
  performance: { bg: "bg-red-50",      text: "text-red-700",     border: "border-red-200" },
  general:     { bg: "bg-slate-50",    text: "text-slate-700",   border: "border-slate-200" },
};

// ─── Tiny SVG bar chart for trends ───────────────────────────────────────

function TrendChart({ data }: { data: YearBucket[] }) {
  if (!data || data.length === 0) return null;
  const max = Math.max(1, ...data.map((d) => d.count));
  const W = 600;
  const H = 160;
  const PAD = 28;
  const barW = (W - PAD * 2) / data.length;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-40">
      {[0.25, 0.5, 0.75].map((t) => (
        <line key={t}
          x1={PAD} x2={W - PAD}
          y1={PAD + (H - PAD * 2) * (1 - t)} y2={PAD + (H - PAD * 2) * (1 - t)}
          stroke="currentColor" strokeOpacity="0.08" strokeDasharray="3 3" />
      ))}
      {data.map((d, i) => {
        const h = (d.count / max) * (H - PAD * 2);
        const x = PAD + i * barW + barW * 0.15;
        const y = H - PAD - h;
        return (
          <g key={d.year}>
            <rect x={x} y={y} width={barW * 0.7} height={h} rx={3}
              fill="url(#bar-grad)" />
            <text x={x + barW * 0.35} y={y - 4} textAnchor="middle"
              fontSize="10" fill="currentColor" opacity="0.7">{d.count}</text>
            <text x={x + barW * 0.35} y={H - PAD + 14} textAnchor="middle"
              fontSize="10" fill="currentColor" opacity="0.7">{d.year}</text>
          </g>
        );
      })}
      <defs>
        <linearGradient id="bar-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#8b5cf6" />
        </linearGradient>
      </defs>
    </svg>
  );
}

// ─── Helpers ─────────────────────────────────────────────────────────────

function renderInline(text: string) {
  // Render **bold** markers in text (used in trend interpretation, etc.)
  const parts: React.ReactNode[] = [];
  const re = /\*\*([^*]+)\*\*/g;
  let i = 0;
  let key = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    if (m.index > i) parts.push(<span key={key++}>{text.slice(i, m.index)}</span>);
    parts.push(<strong key={key++}>{m[1]}</strong>);
    i = m.index + m[0].length;
  }
  if (i < text.length) parts.push(<span key={key++}>{text.slice(i)}</span>);
  return <>{parts}</>;
}

// ─── Component ───────────────────────────────────────────────────────────

export default function GapAnalysisPage() {
  const [mode, setMode] = useState<Mode>("topic");

  // Input state
  const [topic, setTopic] = useState("");
  const [fullText, setFullText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Filters
  const [yearFrom, setYearFrom] = useState<string>("");
  const [yearTo, setYearTo] = useState<string>("");

  // Results
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState<string | null>(null);

  const filtersPayload = useMemo(() => {
    const out: Record<string, number> = {};
    if (yearFrom) out.year_from = parseInt(yearFrom, 10);
    if (yearTo) out.year_to = parseInt(yearTo, 10);
    return out;
  }, [yearFrom, yearTo]);

  // ─── Actions ──────────────────────────────────────────────────

  const runTopic = async (q?: string) => {
    const query = (q ?? topic).trim();
    if (!query) return;
    setTopic(query);
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<AnalyzeResponse>(API_ROUTES.module1.analyzeGaps, {
        topic: query, top_k: 10, min_similarity: 0.18, ...filtersPayload,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const runFullPaper = async () => {
    if (fullText.trim().length < 200) {
      setError("Paper text must be at least 200 characters.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<AnalyzeResponse>(API_ROUTES.module1.analyzeGapsFullPaper, {
        text: fullText, top_k: 10, min_similarity: 0.18, ...filtersPayload,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Full-paper analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const runPdf = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("top_k", "10");
      fd.append("min_similarity", "0.18");
      if (yearFrom) fd.append("year_from", yearFrom);
      if (yearTo) fd.append("year_to", yearTo);
      const resp = await api.post<AnalyzeResponse>(API_ROUTES.module1.analyzeGapsPdf, fd, { timeout: 180_000 });
      setResult(resp.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null;
    if (f && !f.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      setFile(null);
      return;
    }
    if (f && f.size > 25 * 1024 * 1024) {
      setError("PDF must be under 25 MB.");
      setFile(null);
      return;
    }
    setFile(f);
    setError("");
  };

  const downloadReport = async () => {
    if (!result) return;
    try {
      const resp = await apiPost<string>(API_ROUTES.module1.gapsReport, { payload: result });
      const html = typeof resp === "string" ? resp : (await api.post(API_ROUTES.module1.gapsReport, { payload: result }, { responseType: "text" })).data;
      const blob = new Blob([html], { type: "text/html" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `gap-report-${Date.now()}.html`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to download report");
    }
  };

  const copyText = async (key: string, text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 1500);
  };

  const trendIcon = (interp: string) => {
    if (/rising|growing/i.test(interp)) return <TrendingUp className="h-4 w-4 text-emerald-600" />;
    if (/declining/i.test(interp)) return <TrendingDown className="h-4 w-4 text-rose-600" />;
    return <Minus className="h-4 w-4 text-blue-600" />;
  };

  // ─── Render ───────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="rounded-2xl bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-600 p-6 text-white shadow-lg">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Sparkles className="h-7 w-7" /> Research Intelligence Platform
        </h1>
        <p className="mt-1 text-sm text-white/85 max-w-3xl">
          Analyse a topic, paste a paper, or upload a PDF. The system surfaces ranked gaps, trends,
          cross-domain opportunities, and AI-assisted research directions — all grounded in 4,200+ SLIIT papers.
        </p>
      </div>

      {/* Mode tabs */}
      <div className="flex gap-2 flex-wrap">
        <Button variant={mode === "topic" ? "default" : "outline"} size="sm" onClick={() => { setMode("topic"); setError(""); }}>
          <Search className="mr-2 h-4 w-4" /> Topic Query
        </Button>
        <Button variant={mode === "fullPaper" ? "default" : "outline"} size="sm" onClick={() => { setMode("fullPaper"); setError(""); }}>
          <FileText className="mr-2 h-4 w-4" /> Paste Paper Text
        </Button>
        <Button variant={mode === "pdf" ? "default" : "outline"} size="sm" onClick={() => { setMode("pdf"); setError(""); }}>
          <Upload className="mr-2 h-4 w-4" /> Upload PDF
        </Button>
      </div>

      {/* Input panel */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Database className="h-5 w-5" />
            {mode === "topic" && "Topic input"}
            {mode === "fullPaper" && "Paste research paper"}
            {mode === "pdf" && "Upload research paper (PDF)"}
          </CardTitle>
          <CardDescription>
            {mode === "topic" && "Type any research area — the system matches against 4,200+ SLIIT papers and surfaces gaps from their abstracts."}
            {mode === "fullPaper" && "Paste a full paper. Methodology + conclusion get extra weight in the matching."}
            {mode === "pdf" && "Drop in a PDF (≤ 25 MB). Section-aware parsing emphasises methodology + conclusion for richer gap detection."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {mode === "topic" && (
            <>
              <div className="space-y-2">
                <Label htmlFor="topic">Research topic</Label>
                <Input
                  id="topic"
                  placeholder="e.g., federated learning for IoT security"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && runTopic()}
                />
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="text-xs text-muted-foreground self-center">Try:</span>
                {SAMPLE_TOPICS.map((t) => (
                  <button
                    key={t}
                    onClick={() => runTopic(t)}
                    className="rounded-full border bg-muted/50 px-3 py-1 text-xs hover:bg-accent transition-colors"
                  >
                    {t}
                  </button>
                ))}
              </div>
            </>
          )}

          {mode === "fullPaper" && (
            <div className="space-y-2">
              <Label htmlFor="full-text">Paper text (≥ 200 characters)</Label>
              <textarea
                id="full-text"
                className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Paste the full text of the paper..."
                value={fullText}
                onChange={(e) => setFullText(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">{fullText.length} characters</p>
            </div>
          )}

          {mode === "pdf" && (
            <div className="space-y-2">
              <Label htmlFor="pdf-file">PDF file</Label>
              <div className="flex items-center gap-3">
                <label
                  htmlFor="pdf-file"
                  className="flex flex-1 items-center justify-center gap-2 rounded-md border border-dashed border-input bg-background px-4 py-8 text-sm text-muted-foreground cursor-pointer hover:bg-accent transition-colors"
                >
                  <FileUp className="h-5 w-5" />
                  {file ? (
                    <span className="text-foreground font-medium">
                      {file.name}
                      <span className="ml-2 text-xs text-muted-foreground">
                        ({(file.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    </span>
                  ) : (
                    <span>Click to choose a PDF</span>
                  )}
                </label>
                <input ref={fileInputRef} id="pdf-file" type="file" accept=".pdf,application/pdf"
                  onChange={handleFileChange} className="hidden" />
                {file && (
                  <Button type="button" variant="ghost" size="icon" onClick={() => { setFile(null); if (fileInputRef.current) fileInputRef.current.value = ""; }}>
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          )}

          {/* Filters */}
          <div className="flex flex-wrap items-end gap-3 border-t pt-4">
            <div className="text-sm font-medium flex items-center gap-1.5">
              <Filter className="h-4 w-4" /> Filters:
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Year from</Label>
              <Input className="w-24" type="number" min={2000} max={2030} placeholder="any"
                value={yearFrom} onChange={(e) => setYearFrom(e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Year to</Label>
              <Input className="w-24" type="number" min={2000} max={2030} placeholder="any"
                value={yearTo} onChange={(e) => setYearTo(e.target.value)} />
            </div>
            <span className="text-xs text-muted-foreground">Filters apply to supporting paper years.</span>
          </div>

          <Button
            size="lg"
            onClick={() => mode === "topic" ? runTopic() : mode === "pdf" ? runPdf() : runFullPaper()}
            disabled={loading
              || (mode === "topic" && !topic.trim())
              || (mode === "fullPaper" && fullText.trim().length < 200)
              || (mode === "pdf" && !file)}
          >
            <Sparkles className="mr-2 h-4 w-4" />
            {loading ? "Analysing…" : "Run Intelligence Analysis"}
          </Button>

          {error && (
            <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
              <AlertTriangle className="h-4 w-4 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Results ───────────────────────────────────────────── */}
      {result && result.loaded && (
        <>
          {/* Status strip */}
          <Card className="bg-muted/30">
            <CardContent className="p-3 flex flex-wrap items-center gap-3 text-sm">
              <Badge variant="outline" className="bg-emerald-100 text-emerald-700 border-emerald-200">
                <Database className="h-3 w-3 mr-1" /> Local SBERT model
              </Badge>
              <span className="text-xs text-muted-foreground">
                Query: <strong className="text-foreground">{result.query}</strong>
              </span>
              <span className="text-xs text-muted-foreground">
                {result.gaps.length} ranked gaps · corpus {result.total_corpus_size.toLocaleString()} extracted gaps · {result.base_model}
              </span>
              <Button size="sm" variant="outline" className="ml-auto" onClick={downloadReport}>
                <Download className="mr-2 h-4 w-4" /> Download Report (HTML)
              </Button>
            </CardContent>
          </Card>

          {/* Classification donut as bar segments */}
          {result.classification_distribution.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Layers className="h-4 w-4" /> Gap classification
                </CardTitle>
                <CardDescription>How the {result.gaps.length} ranked gaps break down by type.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex w-full h-3 rounded-full overflow-hidden border">
                  {(() => {
                    const total = result.classification_distribution.reduce((s, c) => s + c.count, 0) || 1;
                    return result.classification_distribution.map((c) => {
                      const style = CATEGORY_STYLE[c.category] || CATEGORY_STYLE.general;
                      const pct = (c.count / total) * 100;
                      return (
                        <div key={c.category}
                          className={style.bg + " " + style.text}
                          title={`${c.label}: ${c.count}`}
                          style={{ width: `${pct}%` }} />
                      );
                    });
                  })()}
                </div>
                <div className="mt-3 flex flex-wrap gap-3 text-xs">
                  {result.classification_distribution.map((c) => {
                    const style = CATEGORY_STYLE[c.category] || CATEGORY_STYLE.general;
                    return (
                      <div key={c.category} className="flex items-center gap-1.5">
                        <span className={`inline-block h-2.5 w-2.5 rounded-full ${style.bg} border ${style.border}`} />
                        <span className="text-muted-foreground">{c.label}</span>
                        <strong className={style.text}>{c.count}</strong>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Trends */}
          {result.trends.by_year.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    {trendIcon(result.trends.interpretation)}
                    Year-wise trend
                  </CardTitle>
                  <Badge variant="outline" className="text-xs">
                    Peak: {result.trends.peak_year} ({result.trends.peak_count} papers)
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <TrendChart data={result.trends.by_year} />
                <p className="text-sm leading-relaxed mt-3">
                  {renderInline(result.trends.interpretation)}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Gaps */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Top research gaps</CardTitle>
              <CardDescription>Ranked by multi-dimensional score (similarity × type × novelty × recency).</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {result.gaps.map((g, i) => {
                const style = CATEGORY_STYLE[g.classification] || CATEGORY_STYLE.general;
                return (
                  <div key={i} className="rounded-md border p-4 space-y-2">
                    <div className="flex items-start justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline" className="font-mono text-[10px]">#{i + 1}</Badge>
                        <Badge variant="outline" className={`${style.bg} ${style.text} ${style.border}`}>
                          {g.category_label}
                        </Badge>
                        <Badge variant="secondary" className="text-[10px]">
                          Score: {(g.multi_dim_score * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      <div className="flex gap-3 text-xs text-muted-foreground">
                        <span>Sim {(g.similarity * 100).toFixed(0)}%</span>
                        <span>Novelty {(g.novelty_score * 100).toFixed(0)}%</span>
                        <span>Recency {(g.recency_score * 100).toFixed(0)}%</span>
                      </div>
                    </div>

                    <p className="text-sm leading-relaxed font-medium">&ldquo;{g.description}&rdquo;</p>

                    <p className="text-xs text-muted-foreground italic border-l-2 border-primary/30 pl-3">
                      <Lightbulb className="inline h-3 w-3 mr-1 text-amber-500" />
                      {g.explanation}
                    </p>

                    {g.supporting_paper && g.supporting_paper.title && (
                      <div className="rounded-md border bg-muted/30 p-2 text-xs space-y-1">
                        <div className="flex items-center gap-1.5 text-muted-foreground font-medium">
                          <BookOpen className="h-3 w-3" /> Source SLIIT paper
                        </div>
                        <p className="font-medium text-foreground">{g.supporting_paper.title}</p>
                        <p className="text-muted-foreground">
                          {(g.supporting_paper.authors || []).slice(0, 3).join(", ") || "Unknown authors"}
                          {g.supporting_paper.year ? ` · ${g.supporting_paper.year}` : ""}
                        </p>
                        {g.supporting_paper.url && (
                          <a href={g.supporting_paper.url} target="_blank" rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-primary hover:underline">
                            View on SLIIT RDA <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
              {result.gaps.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">No gaps matched. Try a broader query or relax the year filter.</p>
              )}
            </CardContent>
          </Card>

          {/* Cross-domain opportunities */}
          {result.cross_domain.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Network className="h-4 w-4" /> Cross-domain opportunities
                </CardTitle>
                <CardDescription>
                  Domain pairs with sparse coverage in the SLIIT corpus — strong starting points for novel research.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {result.cross_domain.map((c, i) => (
                  <div key={i} className="rounded-md border bg-muted/30 p-3 text-sm space-y-1">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-1.5 font-medium">
                        <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">{c.domain_a}</Badge>
                        <span className="text-muted-foreground">×</span>
                        <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">{c.domain_b}</Badge>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {c.papers_in_intersection}/{c.papers_in_primary} cover both ·
                        opportunity <strong>{(c.opportunity_score * 100).toFixed(0)}%</strong>
                      </span>
                    </div>
                    <p className="text-xs">{renderInline(c.suggestion)}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Recommendations */}
          {result.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-amber-500" /> Recommended research directions
                </CardTitle>
                <CardDescription>Auto-generated titles + problem statements grounded in the gaps above.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {result.recommendations.map((r, i) => (
                  <div key={i} className="rounded-md border p-3 space-y-2 text-sm">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-semibold flex-1">{r.title}</h3>
                      <Button size="sm" variant="ghost" onClick={() => copyText(`rec-${i}`, `${r.title}\n\n${r.problem_statement}`)}>
                        {copied === `rec-${i}` ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground italic">{r.rationale}</p>
                    <div className="rounded bg-muted/40 p-2 text-xs leading-relaxed">{r.problem_statement}</div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Saturated zones */}
          {result.saturation.length > 0 && (
            <Card className="border-amber-200 bg-amber-50/40">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2 text-amber-800">
                  <AlertTriangle className="h-4 w-4" /> Saturated subtopics — avoid duplicating
                </CardTitle>
                <CardDescription className="text-amber-800/80">
                  Terms that appear in many of the matched papers. Differentiate your contribution from these.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1.5">
                  {result.saturation.map((s) => (
                    <span key={s.term}
                      title={s.warning}
                      className="rounded-full border border-amber-200 bg-white px-3 py-1 text-xs">
                      <code className="font-medium">{s.term}</code>
                      <span className="ml-1.5 text-muted-foreground">×{s.paper_count}</span>
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {result && !result.loaded && (
        <Card>
          <CardContent className="py-6 text-center text-sm text-muted-foreground">
            The local gap analyzer is not loaded. Make sure module 1 is running and the SBERT
            index has been built (`python services/module1-integrity/training/train_gap_analyzer.py`).
          </CardContent>
        </Card>
      )}
    </div>
  );
}

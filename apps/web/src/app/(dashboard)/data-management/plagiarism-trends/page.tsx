"use client";

import { useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Database, Search, FileText, AlertTriangle, ExternalLink,
  ArrowUp, ArrowDown, Minus, Download, FileUp, X, BookOpen, Loader2, Files,
} from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import api, { apiPost } from "@/lib/api";

// ─── Types ────────────────────────────────────────────────────────────────

interface PaperRef {
  paper_id: string;
  title: string;
  url: string;
}

interface FlaggedPair {
  similarity: number;
  paper_a: PaperRef;
  paper_b: PaperRef;
}

interface YearlyTrend {
  topic: string;
  year: number;
  n_papers: number;
  avg_similarity: number;
  max_similarity: number;
  p95_similarity: number;
  n_high_similarity_pairs: number;
  trend_direction: string;
  top_pairs: FlaggedPair[];
}

interface TopicMatch {
  topic: string;
  similarity: number;
  n_records: number;
  n_papers_total: number;
  avg_similarity_overall: number;
  max_avg_similarity: number;
  n_high_similarity_pairs_total: number;
  latest_year: number;
  latest_trend_direction: string;
  yearly: YearlyTrend[];
}

interface RelatedPaper {
  paper_id: string;
  title: string;
  authors: string[];
  year: number | string | null;
  url: string;
  subject?: string | string[] | null;
  similarity: number;
  abstract_excerpt: string;
}

interface TopicSearchResponse {
  matches: TopicMatch[];
  related_papers?: RelatedPaper[];
  query?: string;
  total_topics: number;
  model_version: string;
  base_model: string;
  source: string;
}

interface FlaggedSentencePair {
  similarity: number;
  sentence_a: string;
  sentence_b: string;
  index_a: number;
  index_b: number;
}

interface CompareResponse {
  document_similarity: number;
  ngram_jaccard: number;
  ngram_overlap_in_a: number;
  ngram_overlap_in_b: number;
  risk_score: number;
  risk_level: string;
  flagged_pairs: FlaggedSentencePair[];
  n_sentences_a: number;
  n_sentences_b: number;
  title_a: string;
  title_b: string;
  model_version: string;
  source: string;
}

const SAMPLE_TOPICS = [
  "machine learning",
  "image processing",
  "covid-19",
  "deep learning",
  "natural language processing",
  "iot",
];

const directionConfig: Record<string, { color: string; icon: typeof ArrowUp }> = {
  increasing: { color: "text-red-600 bg-red-50 border-red-200", icon: ArrowUp },
  decreasing: { color: "text-green-600 bg-green-50 border-green-200", icon: ArrowDown },
  stable: { color: "text-blue-600 bg-blue-50 border-blue-200", icon: Minus },
  baseline: { color: "text-muted-foreground bg-secondary border-border", icon: Minus },
};

const riskColor: Record<string, string> = {
  high: "bg-red-100 text-red-700 border-red-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  low: "bg-yellow-50 text-yellow-700 border-yellow-200",
  minimal: "bg-emerald-50 text-emerald-700 border-emerald-200",
};

// ─── Component ────────────────────────────────────────────────────────────

export default function PlagiarismTrendsPage() {
  // Topic search state
  const [topic, setTopic] = useState("");
  const [search, setSearch] = useState<TopicSearchResponse | null>(null);
  const [searching, setSearching] = useState(false);

  // Compare-text state
  const [textA, setTextA] = useState("");
  const [textB, setTextB] = useState("");
  const [titleA, setTitleA] = useState("");
  const [titleB, setTitleB] = useState("");
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState("");

  // Compare-PDF state
  const [pdfA, setPdfA] = useState<File | null>(null);
  const [pdfB, setPdfB] = useState<File | null>(null);
  const pdfARef = useRef<HTMLInputElement>(null);
  const pdfBRef = useRef<HTMLInputElement>(null);
  const [pdfTitleA, setPdfTitleA] = useState("");
  const [pdfTitleB, setPdfTitleB] = useState("");
  const [pdfCompareResult, setPdfCompareResult] = useState<CompareResponse | null>(null);
  const [pdfComparing, setPdfComparing] = useState(false);

  const [tab, setTab] = useState<"trends" | "compare" | "compare-pdf">("trends");

  const handleSearch = async (queryTopic?: string) => {
    const q = (queryTopic ?? topic).trim();
    if (!q) return;
    setTopic(q);
    setSearching(true);
    setError("");
    try {
      const data = await apiPost<TopicSearchResponse>(API_ROUTES.module3.plagiarismTrendsSearch, {
        topic: q,
        top_k: 5,
      });
      setSearch(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
    }
  };

  const handleCompare = async () => {
    if (textA.trim().length < 20 || textB.trim().length < 20) return;
    setComparing(true);
    setError("");
    try {
      const data = await apiPost<CompareResponse>(API_ROUTES.module3.plagiarismCompare, {
        text_a: textA,
        text_b: textB,
        title_a: titleA || "Paper A",
        title_b: titleB || "Paper B",
        top_pairs: 5,
      });
      setCompareResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      setComparing(false);
    }
  };

  const validatePdf = (f: File | null): string | null => {
    if (!f) return null;
    if (!f.name.toLowerCase().endsWith(".pdf")) return "Only PDF files are supported.";
    if (f.size > 25 * 1024 * 1024) return "Each PDF must be ≤ 25 MB.";
    return null;
  };

  const handlePdfCompare = async () => {
    if (!pdfA || !pdfB) return;
    const eA = validatePdf(pdfA), eB = validatePdf(pdfB);
    if (eA || eB) { setError(eA || eB || ""); return; }

    setPdfComparing(true);
    setError("");
    setPdfCompareResult(null);
    try {
      const fd = new FormData();
      fd.append("file_a", pdfA);
      fd.append("file_b", pdfB);
      if (pdfTitleA.trim()) fd.append("title_a", pdfTitleA.trim());
      if (pdfTitleB.trim()) fd.append("title_b", pdfTitleB.trim());
      fd.append("top_pairs", "5");
      const resp = await api.post<CompareResponse>(
        API_ROUTES.module3.plagiarismComparePdf, fd, { timeout: 240_000 },
      );
      setPdfCompareResult(resp.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF comparison failed");
    } finally {
      setPdfComparing(false);
    }
  };

  const downloadHtml = (html: string, filename: string) => {
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadSearchReport = async () => {
    if (!search || !topic.trim()) return;
    try {
      const r = await api.post(
        API_ROUTES.module3.plagiarismTrendsSearchReport,
        { topic: topic.trim(), top_k: 5 },
        { responseType: "text" },
      );
      const safe = topic.replace(/[^a-z0-9]+/gi, "_");
      downloadHtml(r.data as string, `plagiarism-trends-${safe}-${Date.now()}.html`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not download report");
    }
  };

  const handleDownloadCompareReport = async (
    result: CompareResponse | null, ta: string, tb: string,
  ) => {
    if (!result) return;
    try {
      const r = await api.post(
        API_ROUTES.module3.plagiarismCompareReport,
        { result, title_a: ta || result.title_a || "Paper A", title_b: tb || result.title_b || "Paper B" },
        { responseType: "text" },
      );
      downloadHtml(r.data as string, `plagiarism-compare-${Date.now()}.html`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not download report");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Plagiarism Trends</h1>
        <p className="text-muted-foreground">
          Search topic-level plagiarism patterns across SLIIT papers, or compare two papers directly.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        <Button
          variant={tab === "trends" ? "default" : "outline"}
          size="sm"
          onClick={() => setTab("trends")}
        >
          <Search className="mr-2 h-4 w-4" /> Topic Trend Search
        </Button>
        <Button
          variant={tab === "compare" ? "default" : "outline"}
          size="sm"
          onClick={() => setTab("compare")}
        >
          <FileText className="mr-2 h-4 w-4" /> Compare Two Papers (text)
        </Button>
        <Button
          variant={tab === "compare-pdf" ? "default" : "outline"}
          size="sm"
          onClick={() => setTab("compare-pdf")}
        >
          <Files className="mr-2 h-4 w-4" /> Compare PDFs
        </Button>
      </div>

      {/* ── Tab: Topic search ──────────────────────────────────── */}
      {tab === "trends" && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Search by Topic</CardTitle>
              <CardDescription>
                Enter a topic — the system finds the closest SLIIT topic-buckets and shows their per-year plagiarism statistics.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="topic">Topic / category</Label>
                <Input
                  id="topic"
                  placeholder="e.g., machine learning"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                />
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="text-xs text-muted-foreground self-center">Try:</span>
                {SAMPLE_TOPICS.map((t) => (
                  <button
                    key={t}
                    onClick={() => handleSearch(t)}
                    className="rounded-full border bg-muted/50 px-3 py-1 text-xs hover:bg-accent transition-colors"
                  >
                    {t}
                  </button>
                ))}
              </div>
              <Button onClick={() => handleSearch()} disabled={searching || !topic.trim()}>
                {searching ? "Searching…" : "Search Trends"}
              </Button>
              {error && <p className="text-sm text-destructive">{error}</p>}
            </CardContent>
          </Card>

          {search && (
            <>
              <Card className="bg-muted/30">
                <CardContent className="p-3 flex flex-wrap items-center gap-3 text-sm">
                  <Badge variant="outline" className="bg-emerald-100 text-emerald-700 border-emerald-200">
                    <Database className="h-3 w-3 mr-1" /> Local SBERT trend index
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {search.matches.length} bucket match{search.matches.length === 1 ? "" : "es"}
                    {search.related_papers ? ` · ${search.related_papers.length} related papers` : ""}
                    {" · "}{search.total_topics} indexed topics
                  </span>
                  <Button size="sm" variant="outline" className="ml-auto" onClick={handleDownloadSearchReport}>
                    <Download className="mr-2 h-4 w-4" /> Download report
                  </Button>
                </CardContent>
              </Card>

              {search.related_papers && search.related_papers.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <BookOpen className="h-4 w-4" /> Related SLIIT papers
                    </CardTitle>
                    <CardDescription>
                      Papers from the SLIIT research library that match your query — useful when no
                      precomputed trend bucket is a close fit.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {search.related_papers.map((p) => (
                      <div key={p.paper_id} className="rounded-md border bg-muted/30 p-3 text-sm space-y-1">
                        <div className="flex items-start justify-between gap-2">
                          <p className="font-medium flex-1">{p.title}</p>
                          <Badge variant="secondary" className="text-[10px] shrink-0">
                            {(p.similarity * 100).toFixed(0)}% match
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {(p.authors || []).slice(0, 3).join(", ") || "Unknown authors"}
                          {p.year ? ` · ${p.year}` : ""}
                        </p>
                        {p.abstract_excerpt && (
                          <p className="text-xs italic text-muted-foreground">{p.abstract_excerpt}</p>
                        )}
                        {p.url && (
                          <a href={p.url} target="_blank" rel="noopener noreferrer"
                             className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
                            View on SLIIT RDA <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {search.matches.map((m, i) => (
                <Card key={i}>
                  <CardHeader>
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div>
                        <CardTitle className="text-base capitalize">{m.topic}</CardTitle>
                        <CardDescription>
                          {m.n_papers_total} papers · {m.n_records} years tracked · most recent: {m.latest_year}
                        </CardDescription>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {(m.similarity * 100).toFixed(0)}% match
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex flex-wrap gap-4 text-xs border-b pb-3">
                      <div>
                        <span className="text-muted-foreground">Avg similarity (overall): </span>
                        <span className="font-medium">{(m.avg_similarity_overall * 100).toFixed(1)}%</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Peak avg: </span>
                        <span className="font-medium">{(m.max_avg_similarity * 100).toFixed(1)}%</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">High-similarity pairs: </span>
                        <span className="font-medium">{m.n_high_similarity_pairs_total}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Latest direction: </span>
                        {(() => {
                          const cfg = directionConfig[m.latest_trend_direction] || directionConfig.baseline;
                          const Icon = cfg.icon;
                          return (
                            <Badge variant="outline" className={`text-xs ${cfg.color}`}>
                              <Icon className="h-3 w-3 mr-0.5" /> {m.latest_trend_direction}
                            </Badge>
                          );
                        })()}
                      </div>
                    </div>

                    {m.yearly && m.yearly.length > 0 && (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b text-left text-muted-foreground text-xs">
                              <th className="pb-2 pr-3">Year</th>
                              <th className="pb-2 pr-3">N papers</th>
                              <th className="pb-2 pr-3">Avg sim</th>
                              <th className="pb-2 pr-3">Max sim</th>
                              <th className="pb-2 pr-3">P95 sim</th>
                              <th className="pb-2 pr-3">High pairs</th>
                              <th className="pb-2">Trend</th>
                            </tr>
                          </thead>
                          <tbody>
                            {m.yearly.map((y, j) => {
                              const cfg = directionConfig[y.trend_direction] || directionConfig.baseline;
                              const Icon = cfg.icon;
                              return (
                                <tr key={j} className="border-b border-border/50">
                                  <td className="py-1.5 pr-3 font-medium">{y.year}</td>
                                  <td className="py-1.5 pr-3">{y.n_papers}</td>
                                  <td className="py-1.5 pr-3">{(y.avg_similarity * 100).toFixed(1)}%</td>
                                  <td className="py-1.5 pr-3">{(y.max_similarity * 100).toFixed(1)}%</td>
                                  <td className="py-1.5 pr-3">{(y.p95_similarity * 100).toFixed(1)}%</td>
                                  <td className="py-1.5 pr-3">{y.n_high_similarity_pairs}</td>
                                  <td className="py-1.5">
                                    <span className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs ${cfg.color}`}>
                                      <Icon className="h-3 w-3" /> {y.trend_direction}
                                    </span>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {m.yearly.some((y) => y.top_pairs.length > 0) && (
                      <div className="space-y-2">
                        <p className="text-xs font-medium text-muted-foreground">Most-similar paper pairs in this topic:</p>
                        {m.yearly.flatMap((y) =>
                          y.top_pairs.slice(0, 2).map((p, k) => (
                            <div key={`${y.year}-${k}`} className="rounded-md border bg-muted/30 p-2 text-xs space-y-1">
                              <div className="flex items-center justify-between">
                                <span className="font-medium text-amber-700">
                                  {(p.similarity * 100).toFixed(1)}% similarity · {y.year}
                                </span>
                              </div>
                              <p>
                                <span className="text-muted-foreground">A: </span>
                                <span>{p.paper_a.title}</span>
                                {p.paper_a.url && (
                                  <a
                                    href={p.paper_a.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="ml-1 text-primary hover:underline inline-flex items-center"
                                  >
                                    <ExternalLink className="h-3 w-3" />
                                  </a>
                                )}
                              </p>
                              <p>
                                <span className="text-muted-foreground">B: </span>
                                <span>{p.paper_b.title}</span>
                                {p.paper_b.url && (
                                  <a
                                    href={p.paper_b.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="ml-1 text-primary hover:underline inline-flex items-center"
                                  >
                                    <ExternalLink className="h-3 w-3" />
                                  </a>
                                )}
                              </p>
                            </div>
                          ))
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}

              {search.matches.length === 0 && (
                <Card>
                  <CardContent className="py-6 text-center text-sm text-muted-foreground">
                    No matching topics found. Try a broader query.
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </>
      )}

      {/* ── Tab: Compare two papers ─────────────────────────────── */}
      {tab === "compare" && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Compare Two Papers</CardTitle>
              <CardDescription>
                Paste two paper texts. The system computes SBERT similarity, n-gram overlap, and the most similar sentence pairs.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="title-a">Paper A title (optional)</Label>
                  <Input
                    id="title-a"
                    placeholder="e.g., Original paper"
                    value={titleA}
                    onChange={(e) => setTitleA(e.target.value)}
                  />
                  <Label htmlFor="text-a">Paper A text</Label>
                  <textarea
                    id="text-a"
                    className="flex min-h-[180px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    placeholder="Paste the full text of paper A..."
                    value={textA}
                    onChange={(e) => setTextA(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">{textA.length} chars</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="title-b">Paper B title (optional)</Label>
                  <Input
                    id="title-b"
                    placeholder="e.g., Submission to compare"
                    value={titleB}
                    onChange={(e) => setTitleB(e.target.value)}
                  />
                  <Label htmlFor="text-b">Paper B text</Label>
                  <textarea
                    id="text-b"
                    className="flex min-h-[180px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    placeholder="Paste the full text of paper B..."
                    value={textB}
                    onChange={(e) => setTextB(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">{textB.length} chars</p>
                </div>
              </div>
              <Button
                onClick={handleCompare}
                disabled={comparing || textA.trim().length < 20 || textB.trim().length < 20}
              >
                {comparing ? "Comparing…" : "Run Plagiarism Comparison"}
              </Button>
              {error && <p className="text-sm text-destructive">{error}</p>}
            </CardContent>
          </Card>

          {compareResult && (
            <>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5" /> Plagiarism Risk
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className={`uppercase ${riskColor[compareResult.risk_level] || ""}`}>
                        {compareResult.risk_level} · {(compareResult.risk_score * 100).toFixed(0)}%
                      </Badge>
                      <Button size="sm" variant="outline"
                        onClick={() => handleDownloadCompareReport(compareResult, titleA, titleB)}>
                        <Download className="mr-2 h-4 w-4" /> Download report
                      </Button>
                    </div>
                  </div>
                  <CardDescription>
                    {compareResult.title_a} ↔ {compareResult.title_b}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-xs text-muted-foreground">Document similarity (SBERT)</p>
                      <p className="text-2xl font-semibold">{(compareResult.document_similarity * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">N-gram Jaccard (4-grams)</p>
                      <p className="text-2xl font-semibold">{(compareResult.ngram_jaccard * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Overlap in A</p>
                      <p className="text-lg font-semibold">{(compareResult.ngram_overlap_in_a * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Overlap in B</p>
                      <p className="text-lg font-semibold">{(compareResult.ngram_overlap_in_b * 100).toFixed(1)}%</p>
                    </div>
                  </div>
                  <p className="mt-3 text-xs text-muted-foreground">
                    {compareResult.n_sentences_a} sentences in A, {compareResult.n_sentences_b} in B · {compareResult.model_version}
                  </p>
                </CardContent>
              </Card>

              {compareResult.flagged_pairs && compareResult.flagged_pairs.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Most Similar Sentence Pairs</CardTitle>
                    <CardDescription>
                      Top {compareResult.flagged_pairs.length} sentence-level matches across the two papers.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {compareResult.flagged_pairs.map((p, i) => (
                      <div key={i} className="rounded-md border p-3 text-sm space-y-2">
                        <Badge variant="outline" className={
                          p.similarity >= 0.85 ? riskColor.high
                          : p.similarity >= 0.7 ? riskColor.medium
                          : riskColor.low
                        }>
                          {(p.similarity * 100).toFixed(1)}% similar
                        </Badge>
                        <div className="border-l-2 border-blue-300 pl-3">
                          <p className="text-xs text-muted-foreground">A · sentence #{p.index_a + 1}</p>
                          <p>{p.sentence_a}</p>
                        </div>
                        <div className="border-l-2 border-emerald-300 pl-3">
                          <p className="text-xs text-muted-foreground">B · sentence #{p.index_b + 1}</p>
                          <p>{p.sentence_b}</p>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </>
      )}

      {/* ── Tab: Compare two PDFs ───────────────────────────────── */}
      {tab === "compare-pdf" && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Files className="h-5 w-5" /> Compare Two Research Papers (PDF)
              </CardTitle>
              <CardDescription>
                Drop two PDFs and we extract their text, then run the same SBERT + n-gram
                comparison used in the text tab. Each file ≤ 25 MB.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                {/* Paper A */}
                <div className="space-y-2">
                  <Label htmlFor="pdf-a-title">Paper A title (optional)</Label>
                  <Input id="pdf-a-title" placeholder="e.g., Original paper"
                    value={pdfTitleA} onChange={(e) => setPdfTitleA(e.target.value)} />
                  <Label>Paper A PDF</Label>
                  <div className="flex items-center gap-2">
                    <label htmlFor="pdf-a-file"
                      className="flex flex-1 items-center justify-center gap-2 rounded-md border border-dashed border-input bg-background px-3 py-6 text-sm text-muted-foreground cursor-pointer hover:bg-accent transition-colors">
                      <FileUp className="h-5 w-5" />
                      {pdfA ? (
                        <span className="text-foreground font-medium truncate max-w-[200px]">
                          {pdfA.name} <span className="text-xs text-muted-foreground">
                            ({(pdfA.size / 1024 / 1024).toFixed(2)} MB)
                          </span>
                        </span>
                      ) : <span>Click to choose paper A (.pdf)</span>}
                    </label>
                    <input ref={pdfARef} id="pdf-a-file" type="file" accept=".pdf,application/pdf"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0] || null;
                        const err = validatePdf(f);
                        if (err) { setError(err); setPdfA(null); return; }
                        setError(""); setPdfA(f);
                      }} />
                    {pdfA && (
                      <Button type="button" variant="ghost" size="icon"
                        onClick={() => { setPdfA(null); if (pdfARef.current) pdfARef.current.value = ""; }}>
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
                {/* Paper B */}
                <div className="space-y-2">
                  <Label htmlFor="pdf-b-title">Paper B title (optional)</Label>
                  <Input id="pdf-b-title" placeholder="e.g., Submission to compare"
                    value={pdfTitleB} onChange={(e) => setPdfTitleB(e.target.value)} />
                  <Label>Paper B PDF</Label>
                  <div className="flex items-center gap-2">
                    <label htmlFor="pdf-b-file"
                      className="flex flex-1 items-center justify-center gap-2 rounded-md border border-dashed border-input bg-background px-3 py-6 text-sm text-muted-foreground cursor-pointer hover:bg-accent transition-colors">
                      <FileUp className="h-5 w-5" />
                      {pdfB ? (
                        <span className="text-foreground font-medium truncate max-w-[200px]">
                          {pdfB.name} <span className="text-xs text-muted-foreground">
                            ({(pdfB.size / 1024 / 1024).toFixed(2)} MB)
                          </span>
                        </span>
                      ) : <span>Click to choose paper B (.pdf)</span>}
                    </label>
                    <input ref={pdfBRef} id="pdf-b-file" type="file" accept=".pdf,application/pdf"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0] || null;
                        const err = validatePdf(f);
                        if (err) { setError(err); setPdfB(null); return; }
                        setError(""); setPdfB(f);
                      }} />
                    {pdfB && (
                      <Button type="button" variant="ghost" size="icon"
                        onClick={() => { setPdfB(null); if (pdfBRef.current) pdfBRef.current.value = ""; }}>
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>

              <Button onClick={handlePdfCompare} disabled={pdfComparing || !pdfA || !pdfB}>
                {pdfComparing
                  ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Extracting & comparing…</>
                  : <>Run Plagiarism Comparison</>}
              </Button>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <p className="text-xs text-muted-foreground">
                The PDFs are held in memory only long enough to extract text — they&apos;re not stored.
              </p>
            </CardContent>
          </Card>

          {pdfCompareResult && (
            <>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5" /> Plagiarism Risk
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className={`uppercase ${riskColor[pdfCompareResult.risk_level] || ""}`}>
                        {pdfCompareResult.risk_level} · {(pdfCompareResult.risk_score * 100).toFixed(0)}%
                      </Badge>
                      <Button size="sm" variant="outline"
                        onClick={() => handleDownloadCompareReport(pdfCompareResult, pdfTitleA, pdfTitleB)}>
                        <Download className="mr-2 h-4 w-4" /> Download report
                      </Button>
                    </div>
                  </div>
                  <CardDescription>
                    {pdfCompareResult.title_a} ↔ {pdfCompareResult.title_b}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-xs text-muted-foreground">Document similarity (SBERT)</p>
                      <p className="text-2xl font-semibold">{(pdfCompareResult.document_similarity * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">N-gram Jaccard (4-grams)</p>
                      <p className="text-2xl font-semibold">{(pdfCompareResult.ngram_jaccard * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Overlap in A</p>
                      <p className="text-lg font-semibold">{(pdfCompareResult.ngram_overlap_in_a * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Overlap in B</p>
                      <p className="text-lg font-semibold">{(pdfCompareResult.ngram_overlap_in_b * 100).toFixed(1)}%</p>
                    </div>
                  </div>
                  <p className="mt-3 text-xs text-muted-foreground">
                    {pdfCompareResult.n_sentences_a} sentences in A,
                    {" "}{pdfCompareResult.n_sentences_b} in B · {pdfCompareResult.model_version}
                  </p>
                </CardContent>
              </Card>

              {pdfCompareResult.flagged_pairs && pdfCompareResult.flagged_pairs.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Most Similar Sentence Pairs</CardTitle>
                    <CardDescription>
                      Top {pdfCompareResult.flagged_pairs.length} sentence-level matches across the two PDFs.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {pdfCompareResult.flagged_pairs.map((p, i) => (
                      <div key={i} className="rounded-md border p-3 text-sm space-y-2">
                        <Badge variant="outline" className={
                          p.similarity >= 0.85 ? riskColor.high
                          : p.similarity >= 0.7 ? riskColor.medium
                          : riskColor.low
                        }>
                          {(p.similarity * 100).toFixed(1)}% similar
                        </Badge>
                        <div className="border-l-2 border-blue-300 pl-3">
                          <p className="text-xs text-muted-foreground">A · sentence #{p.index_a + 1}</p>
                          <p>{p.sentence_a}</p>
                        </div>
                        <div className="border-l-2 border-emerald-300 pl-3">
                          <p className="text-xs text-muted-foreground">B · sentence #{p.index_b + 1}</p>
                          <p>{p.sentence_b}</p>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}

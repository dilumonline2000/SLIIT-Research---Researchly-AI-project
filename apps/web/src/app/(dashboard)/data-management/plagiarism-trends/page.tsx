"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Database, Search, FileText, AlertTriangle, ExternalLink, ArrowUp, ArrowDown, Minus } from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

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

interface TopicSearchResponse {
  matches: TopicMatch[];
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

  // Compare state
  const [textA, setTextA] = useState("");
  const [textB, setTextB] = useState("");
  const [titleA, setTitleA] = useState("");
  const [titleB, setTitleB] = useState("");
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState("");

  const [tab, setTab] = useState<"trends" | "compare">("trends");

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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Plagiarism Trends</h1>
        <p className="text-muted-foreground">
          Search topic-level plagiarism patterns across SLIIT papers, or compare two papers directly.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
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
          <FileText className="mr-2 h-4 w-4" /> Compare Two Papers
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
                    {search.matches.length} matches from <strong>{search.total_topics}</strong> indexed topics ·
                    {" "}{search.base_model}
                  </span>
                </CardContent>
              </Card>

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
                    <Badge variant="outline" className={`uppercase ${riskColor[compareResult.risk_level] || ""}`}>
                      {compareResult.risk_level} · {(compareResult.risk_score * 100).toFixed(0)}%
                    </Badge>
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
    </div>
  );
}

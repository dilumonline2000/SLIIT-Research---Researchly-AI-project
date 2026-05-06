"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Card, CardContent, CardHeader, CardTitle, CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp, TrendingDown, Minus, AlertCircle, Sparkles, Lightbulb,
  Target, Download, BarChart3, GitCompareArrows, Loader2, Zap, CheckCircle2,
} from "lucide-react";
import {
  ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, LineChart,
} from "recharts";
import api from "@/lib/api";
import { apiGet, apiPost } from "@/lib/api";
import { API_ROUTES } from "@/lib/constants";

// ─── Types ────────────────────────────────────────────────────────────────

interface HistoricalPoint { year: number; count: number; type: "historical" }
interface ForecastPoint { year: number; count: number; lower: number; upper: number; type: "forecast" }
interface Accuracy { available: boolean; rmse: number; mae: number; nrmse: number; n_observations: number }
interface TrendStats {
  historical_total?: number;
  historical_peak?: { year: number; count: number };
  current_count?: number;
  forecast_end?: number;
}
interface Forecast {
  topic: string;
  horizon_years: number;
  historical: HistoricalPoint[];
  forecast: ForecastPoint[];
  trend_direction: string;
  growth_pct: number;
  interpretation: string;
  accuracy: Accuracy;
  model_type: string;
  data_range: string;
  model_version: string;
  stats: TrendStats;
}

interface EmergingTopic {
  topic: string; score: number; recent_slope: number; long_term_slope: number;
  latest_count: number; growth_ratio: number; growth_pct: number; interpretation: string;
}
interface Recommendation {
  topic: string; score: number; growth_pct: number; latest_count: number;
  saturation: number; rationale: string; suggested_title: string;
}
interface InsightsResponse {
  horizon: number;
  emerging: EmergingTopic[];
  recommendations: Recommendation[];
  model_version: string;
}
interface CompareResponse {
  forecasts: Forecast[];
  ranking: { topic: string; growth_pct: number; direction: string; current: number; forecast_end: number }[];
  horizon: number;
}

// ─── Constants ───────────────────────────────────────────────────────────

const DIRECTION_INFO: Record<string, { Icon: typeof TrendingUp; color: string; label: string; bg: string; ring: string }> = {
  rising:            { Icon: TrendingUp,   color: "text-emerald-600", label: "Rising",            bg: "bg-emerald-50", ring: "border-emerald-200" },
  declining:         { Icon: TrendingDown, color: "text-rose-600",    label: "Declining",         bg: "bg-rose-50",    ring: "border-rose-200" },
  stable:            { Icon: Minus,        color: "text-blue-600",    label: "Stable",            bg: "bg-blue-50",    ring: "border-blue-200" },
  insufficient_data: { Icon: AlertCircle,  color: "text-amber-600",   label: "Insufficient data", bg: "bg-amber-50",   ring: "border-amber-200" },
  unknown:           { Icon: AlertCircle,  color: "text-slate-500",   label: "Unknown",           bg: "bg-slate-50",   ring: "border-slate-200" },
};

// 8-colour palette for the comparison chart
const SERIES_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#06b6d4", "#8b5cf6", "#f97316", "#84cc16"];

// Friendly icons per trained topic bucket
const TOPIC_EMOJI: Record<string, string> = {
  computing:        "💻",
  engineering:      "🛠️",
  health:           "🩺",
  business:         "💼",
  social_sciences:  "📚",
  sciences:         "🔬",
  general:          "🧭",
};

// Static fallback used when the API hasn't responded yet (e.g. first paint or
// model still loading) so the chips are always visible.
const FALLBACK_TOPICS = ["computing", "engineering", "health", "business", "social_sciences", "sciences", "general"];

// Curated multi-domain comparison presets — useful viva demos
const COMPARE_PRESETS: { label: string; topics: string[]; tagline: string }[] = [
  { label: "Tech fields",          topics: ["computing", "engineering", "sciences"],            tagline: "Compare the three core technical domains" },
  { label: "Health × Computing",   topics: ["health", "computing"],                              tagline: "Trends at the medicine + technology intersection" },
  { label: "Humanities × Tech",    topics: ["business", "social_sciences", "computing"],         tagline: "Where business / social research meets computing" },
  { label: "Everything",           topics: ["computing", "engineering", "sciences", "health", "business", "social_sciences"], tagline: "All six trained domains overlaid" },
];

// ─── Helpers ─────────────────────────────────────────────────────────────

function renderInline(text: string) {
  const parts: React.ReactNode[] = [];
  const re = /\*\*([^*]+)\*\*/g;
  let i = 0; let key = 0; let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    if (m.index > i) parts.push(<span key={key++}>{text.slice(i, m.index)}</span>);
    parts.push(<strong key={key++}>{m[1]}</strong>);
    i = m.index + m[0].length;
  }
  if (i < text.length) parts.push(<span key={key++}>{text.slice(i)}</span>);
  return <>{parts}</>;
}

/** Build chart-ready rows that overlay historical, forecast mean, and a CI band. */
function buildSeries(f: Forecast) {
  const points: Array<{
    year: number; historical?: number; forecast?: number; lower?: number; upper?: number;
  }> = [];
  for (const p of f.historical) points.push({ year: p.year, historical: p.count });
  // Bridge: duplicate the last historical point as the start of the forecast curve
  // so the dashed line visually connects to the solid line.
  const lastH = f.historical[f.historical.length - 1];
  if (lastH && f.forecast.length > 0) {
    points.push({
      year: lastH.year,
      historical: lastH.count,
      forecast: lastH.count,
      lower: lastH.count,
      upper: lastH.count,
    });
  }
  for (const p of f.forecast) {
    points.push({ year: p.year, forecast: p.count, lower: p.lower, upper: p.upper });
  }
  return points;
}

/** Build merged comparison rows {year, [topic1]: count, [topic2]: count, ...} */
function buildComparisonSeries(forecasts: Forecast[]) {
  const map = new Map<number, Record<string, number | undefined>>();
  for (const f of forecasts) {
    for (const p of f.historical) {
      const row = map.get(p.year) || { year: p.year };
      row[f.topic] = p.count;
      map.set(p.year, row);
    }
    for (const p of f.forecast) {
      const row = map.get(p.year) || { year: p.year };
      row[f.topic] = p.count;
      row[`${f.topic}__forecast`] = p.count;
      map.set(p.year, row);
    }
  }
  return [...map.values()].sort((a, b) => (a.year as number) - (b.year as number));
}

// ─── Page ────────────────────────────────────────────────────────────────

type Tab = "overview" | "compare" | "insights";

export default function TrendsPage() {
  const [tab, setTab] = useState<Tab>("overview");

  // Overview state
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [availableTopics, setAvailableTopics] = useState<string[]>([]);
  const [horizon, setHorizon] = useState(3);
  const [filterTopic, setFilterTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Compare state
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [compareData, setCompareData] = useState<CompareResponse | null>(null);
  const [comparing, setComparing] = useState(false);

  // Insights state
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);

  // ─── Loaders ──────────────────────────────────────────────────

  const fetchForecasts = async (topic: string = "", h: number = horizon) => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ horizon: String(h) });
      if (topic.trim()) params.set("topic", topic.trim());
      const data = await apiGet<{ forecasts: Forecast[]; available_topics: string[] }>(
        `${API_ROUTES.module4.trends}?${params}`,
      );
      setForecasts(data.forecasts || []);
      setAvailableTopics(data.available_topics || []);
      // Pre-select up to 3 non-aggregate topics for the compare tab
      if (selectedTopics.length === 0) {
        const pick = (data.available_topics || []).filter((t) => t !== "all").slice(0, 3);
        setSelectedTopics(pick);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch forecasts");
    } finally {
      setLoading(false);
    }
  };

  const fetchCompare = async () => {
    if (selectedTopics.length === 0) return;
    setComparing(true);
    try {
      const data = await apiPost<CompareResponse>(API_ROUTES.module4.trendsCompare, {
        topics: selectedTopics, horizon,
      });
      setCompareData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Compare failed");
    } finally {
      setComparing(false);
    }
  };

  const fetchInsights = async () => {
    setInsightsLoading(true);
    try {
      const data = await apiGet<InsightsResponse>(`${API_ROUTES.module4.trendsInsights}?horizon=${horizon}&top_k=6`);
      setInsights(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch insights");
    } finally {
      setInsightsLoading(false);
    }
  };

  // Apply a quick-pick filter and immediately re-fetch
  const applyTopicChip = (topic: string) => {
    setFilterTopic(topic);
    void fetchForecasts(topic, horizon);
  };

  // Replace the comparison selection with a curated preset
  const applyComparePreset = (topics: string[]) => {
    setSelectedTopics(topics);
    setTab("compare");
  };

  const downloadReport = async () => {
    try {
      const r = await api.post(API_ROUTES.module4.trendsReport, {
        payload: { forecasts, insights },
      }, { responseType: "text" });
      const blob = new Blob([r.data], { type: "text/html" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `trend-report-${Date.now()}.html`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to download report");
    }
  };

  useEffect(() => {
    fetchForecasts("", horizon);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (tab === "compare" && !compareData && selectedTopics.length > 0) void fetchCompare();
    if (tab === "insights" && !insights) void fetchInsights();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  // Re-fetch compare/insights when horizon or selected topics change
  useEffect(() => {
    if (tab === "compare" && selectedTopics.length > 0) void fetchCompare();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [horizon, selectedTopics.join(",")]);
  useEffect(() => {
    if (tab === "insights") void fetchInsights();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [horizon]);

  // ─── Derived ──────────────────────────────────────────────────

  const heroStats = useMemo(() => {
    if (forecasts.length === 0) return null;
    const total = forecasts.reduce((s, f) => s + (f.stats.historical_total || 0), 0);
    const rising = forecasts.filter((f) => f.trend_direction === "rising").length;
    const fastest = forecasts.slice().sort((a, b) => b.growth_pct - a.growth_pct)[0];
    return { total, rising, fastest, total_topics: forecasts.length };
  }, [forecasts]);

  // ─── Render ───────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="rounded-2xl bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-600 p-6 text-white shadow-lg">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Sparkles className="h-7 w-7" /> Research Trend Intelligence
            </h1>
            <p className="mt-1 text-sm text-white/85 max-w-3xl">
              ARIMA forecasts on 4,219 SLIIT papers (2000–2026) with 95% confidence intervals,
              accuracy metrics, multi-domain comparison, and AI-suggested research directions.
            </p>
          </div>
          {heroStats && (
            <div className="flex flex-wrap gap-3">
              <Stat label="Topics tracked" value={heroStats.total_topics} />
              <Stat label="Historical papers" value={heroStats.total.toLocaleString()} />
              <Stat label="Rising domains" value={`${heroStats.rising}/${heroStats.total_topics}`} />
              {heroStats.fastest && (
                <Stat label="Fastest growth" value={`${heroStats.fastest.topic} ${heroStats.fastest.growth_pct >= 0 ? "+" : ""}${heroStats.fastest.growth_pct.toFixed(0)}%`} />
              )}
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <Card>
        <CardContent className="p-4 space-y-3">
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-1">
              <Label className="text-xs">Forecast horizon (years)</Label>
              <div className="flex items-center gap-2">
                <Input
                  type="range" min={1} max={10} value={horizon}
                  onChange={(e) => setHorizon(parseInt(e.target.value, 10))}
                  className="w-40 cursor-pointer"
                />
                <Badge variant="outline" className="font-mono">{horizon}y</Badge>
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Topic filter (optional)</Label>
              <Input
                className="w-56" placeholder="e.g., computing"
                value={filterTopic}
                onChange={(e) => setFilterTopic(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && fetchForecasts(filterTopic, horizon)}
              />
            </div>
            <Button onClick={() => fetchForecasts(filterTopic, horizon)} disabled={loading}>
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <BarChart3 className="mr-2 h-4 w-4" />}
              Refresh forecasts
            </Button>
            <Button variant="outline" className="ml-auto" onClick={downloadReport} disabled={!forecasts.length}>
              <Download className="mr-2 h-4 w-4" /> Download report (HTML)
            </Button>
          </div>

          {/* Try-out topics — always visible; uses a static fallback when the
              model hasn't responded yet so the UI is helpful from first paint. */}
          {(() => {
            const chipTopics = (availableTopics.length > 0 ? availableTopics : FALLBACK_TOPICS)
              .filter((t) => t !== "all");
            return (
              <div className="border-t pt-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs text-muted-foreground self-center mr-1">Try a topic:</span>
                  <button
                    onClick={() => applyTopicChip("")}
                    className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                      filterTopic === ""
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-muted/50 hover:bg-accent"
                    }`}
                    title="Show forecasts for every domain"
                  >
                    🌐 All domains
                  </button>
                  {chipTopics.map((t) => (
                    <button
                      key={t}
                      onClick={() => applyTopicChip(t)}
                      className={`rounded-full border px-3 py-1 text-xs transition-colors capitalize ${
                        filterTopic.toLowerCase() === t.toLowerCase()
                          ? "bg-primary text-primary-foreground border-primary"
                          : "bg-muted/50 hover:bg-accent"
                      }`}
                    >
                      {TOPIC_EMOJI[t] ?? "📊"} {t.replace(/_/g, " ")}
                    </button>
                  ))}
                </div>
                <p className="mt-2 text-[11px] text-muted-foreground">
                  Chips map to the trained ARIMA topic buckets in our SLIIT corpus
                  ({chipTopics.length} topics from 4,219 papers).
                </p>
              </div>
            );
          })()}
        </CardContent>
      </Card>

      {error && (
        <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 mt-0.5" /><span>{error}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex flex-wrap gap-2">
        <Button variant={tab === "overview" ? "default" : "outline"} size="sm" onClick={() => setTab("overview")}>
          <BarChart3 className="mr-2 h-4 w-4" /> Domain Overview
        </Button>
        <Button variant={tab === "compare" ? "default" : "outline"} size="sm" onClick={() => setTab("compare")}>
          <GitCompareArrows className="mr-2 h-4 w-4" /> Compare Domains
        </Button>
        <Button variant={tab === "insights" ? "default" : "outline"} size="sm" onClick={() => setTab("insights")}>
          <Lightbulb className="mr-2 h-4 w-4" /> Insights & Recommendations
        </Button>
      </div>

      {/* ── Tab: Overview ─────────────────────────────────── */}
      {tab === "overview" && (
        <div className="grid gap-4 lg:grid-cols-2">
          {forecasts.map((f) => <ForecastCard key={f.topic} forecast={f} />)}
          {!loading && forecasts.length === 0 && (
            <Card className="lg:col-span-2 border-amber-200 bg-amber-50/40">
              <CardContent className="py-6 space-y-2 text-sm">
                <div className="flex items-center gap-2 font-medium text-amber-800">
                  <AlertCircle className="h-4 w-4" /> No forecasts loaded
                </div>
                <p className="text-amber-900/90">
                  Module 4&apos;s trained ARIMA bundle isn&apos;t available right now. Common causes:
                </p>
                <ul className="list-disc pl-5 text-xs text-amber-900/90 space-y-0.5">
                  <li>Module 4 (port 8004) is not running.</li>
                  <li>
                    Python deps missing — check the service log for{" "}
                    <code className="rounded bg-amber-100 px-1">No module named &apos;statsmodels&apos;</code>{" "}
                    and run{" "}
                    <code className="rounded bg-amber-100 px-1">pip install statsmodels xgboost</code>.
                  </li>
                  <li>
                    Trained model file not built — run{" "}
                    <code className="rounded bg-amber-100 px-1">
                      python services/module4-analytics/training/train_trend_forecaster.py
                    </code>.
                  </li>
                </ul>
                <p className="text-xs text-amber-900/80 pt-1">
                  Once fixed, click <strong>Refresh forecasts</strong> above — the chips already
                  preview the seven trained topic buckets.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* ── Tab: Compare ──────────────────────────────────── */}
      {tab === "compare" && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Select domains to compare</CardTitle>
              <CardDescription>Pick 2–8 domains and the chart updates live, or load a preset.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* Quick-pick presets */}
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-muted-foreground self-center mr-1">Try a preset:</span>
                {COMPARE_PRESETS.map((p) => {
                  const isActive =
                    p.topics.length === selectedTopics.length &&
                    p.topics.every((t) => selectedTopics.includes(t));
                  return (
                    <button
                      key={p.label}
                      onClick={() => applyComparePreset(p.topics)}
                      title={p.tagline}
                      className={`rounded-md border px-3 py-1.5 text-xs transition-colors ${
                        isActive
                          ? "bg-primary text-primary-foreground border-primary"
                          : "bg-muted/50 hover:bg-accent"
                      }`}
                    >
                      <span className="font-medium">{p.label}</span>
                      <span className="ml-1.5 text-[10px] opacity-70">({p.topics.length})</span>
                    </button>
                  );
                })}
              </div>

              <div className="border-t pt-3">
                <p className="text-xs text-muted-foreground mb-2">Or pick individual domains:</p>
                <div className="flex flex-wrap gap-2">
                  {availableTopics.filter((t) => t !== "all").map((t) => {
                    const on = selectedTopics.includes(t);
                    return (
                      <button
                        key={t}
                        onClick={() => setSelectedTopics((prev) =>
                          prev.includes(t) ? prev.filter((x) => x !== t)
                            : prev.length < 8 ? [...prev, t] : prev,
                        )}
                        className={`rounded-full border px-3 py-1 text-xs transition-colors capitalize ${
                          on ? "bg-primary text-primary-foreground border-primary" : "bg-background hover:bg-accent"
                        }`}
                      >
                        {TOPIC_EMOJI[t] ?? "📊"} {t.replace(/_/g, " ")}
                      </button>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>

          {comparing && <Card><CardContent className="py-6 text-center text-sm text-muted-foreground"><Loader2 className="mx-auto h-4 w-4 animate-spin mb-2" /> Comparing…</CardContent></Card>}

          {compareData && compareData.forecasts.length > 0 && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Overlapping trend (historical + forecast)</CardTitle>
                  <CardDescription>
                    Solid lines = historical · dashed lines after the divider = ARIMA forecast (next {compareData.horizon} years)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={buildComparisonSeries(compareData.forecasts)}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="year" stroke="currentColor" opacity={0.7} />
                        <YAxis stroke="currentColor" opacity={0.7} />
                        <Tooltip
                          contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8 }}
                          labelStyle={{ color: "hsl(var(--foreground))" }}
                        />
                        <Legend />
                        {(() => {
                          const lastHistYear = compareData.forecasts[0]?.historical.slice(-1)[0]?.year;
                          return lastHistYear ? (
                            <ReferenceLine x={lastHistYear} stroke="#9ca3af" strokeDasharray="4 4"
                              label={{ value: "Forecast →", position: "top", fontSize: 11, fill: "#6b7280" }} />
                          ) : null;
                        })()}
                        {compareData.forecasts.map((f, i) => (
                          <Line
                            key={f.topic}
                            type="monotone"
                            dataKey={f.topic}
                            stroke={SERIES_COLORS[i % SERIES_COLORS.length]}
                            strokeWidth={2.2}
                            dot={false}
                            connectNulls
                            name={f.topic}
                          />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Growth ranking */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Growth ranking ({compareData.horizon}-year horizon)</CardTitle>
                  <CardDescription>Fastest-growing domains first.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {compareData.ranking.map((r, idx) => {
                      const dir = DIRECTION_INFO[r.direction] || DIRECTION_INFO.unknown;
                      const Icon = dir.Icon;
                      const color = SERIES_COLORS[
                        compareData.forecasts.findIndex((f) => f.topic === r.topic) % SERIES_COLORS.length
                      ];
                      return (
                        <div key={r.topic} className="flex items-center gap-3 rounded-md border bg-muted/30 p-3 text-sm">
                          <span className="font-mono text-xs w-6 text-muted-foreground">#{idx + 1}</span>
                          <span className="h-3 w-3 rounded-full shrink-0" style={{ background: color }} />
                          <span className="font-medium flex-1 capitalize">{r.topic}</span>
                          <span className="text-xs text-muted-foreground">
                            {r.current} → {r.forecast_end.toFixed(0)}
                          </span>
                          <Badge variant="outline" className={`${dir.bg} ${dir.color} ${dir.ring}`}>
                            <Icon className="h-3 w-3 mr-1" />
                            {r.growth_pct >= 0 ? "+" : ""}{r.growth_pct.toFixed(0)}%
                          </Badge>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </>
      )}

      {/* ── Tab: Insights ─────────────────────────────────── */}
      {tab === "insights" && (
        <>
          {insightsLoading && <Card><CardContent className="py-6 text-center text-sm text-muted-foreground"><Loader2 className="mx-auto h-4 w-4 animate-spin mb-2" />Computing insights…</CardContent></Card>}
          {insights && (
            <>
              {/* Visual storytelling — three-step panel */}
              <div className="grid gap-3 md:grid-cols-3">
                <StoryStep
                  icon={<BarChart3 className="h-5 w-5" />}
                  step="1"
                  title="Where we are"
                  body={`${forecasts.length} domains tracked across ${heroStats?.total.toLocaleString() ?? "—"} SLIIT papers; ${heroStats?.rising ?? 0} are currently rising.`}
                />
                <StoryStep
                  icon={<Zap className="h-5 w-5" />}
                  step="2"
                  title="What's emerging"
                  body={
                    insights.emerging[0]
                      ? `${insights.emerging[0].topic} has the steepest recent slope (+${insights.emerging[0].recent_slope.toFixed(1)}/yr).`
                      : "No clearly emerging topics detected — the corpus may be stable."
                  }
                />
                <StoryStep
                  icon={<Target className="h-5 w-5" />}
                  step="3"
                  title="Where to focus"
                  body={
                    insights.recommendations[0]
                      ? `${insights.recommendations[0].topic}: ${insights.recommendations[0].rationale.replace(/\*\*/g, "")}`
                      : "Run the analysis to see suggestions."
                  }
                />
              </div>

              {/* Emerging topics */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Zap className="h-4 w-4 text-amber-500" /> Emerging topics
                  </CardTitle>
                  <CardDescription>
                    Domains where the recent 4-year slope greatly exceeds the long-term slope.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {insights.emerging.map((e, i) => (
                    <div key={e.topic} className="rounded-md border bg-muted/30 p-3 text-sm flex items-start gap-3">
                      <span className="font-mono text-xs w-6 text-muted-foreground">#{i + 1}</span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium capitalize">{e.topic}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">{renderInline(e.interpretation)}</p>
                        <div className="mt-1.5 flex flex-wrap gap-3 text-[10px] text-muted-foreground">
                          <span>Recent slope: <strong>{e.recent_slope >= 0 ? "+" : ""}{e.recent_slope.toFixed(1)}/yr</strong></span>
                          <span>Long-term: {e.long_term_slope >= 0 ? "+" : ""}{e.long_term_slope.toFixed(1)}/yr</span>
                          <span>Latest count: {e.latest_count}</span>
                          <span>Growth ratio: ×{e.growth_ratio.toFixed(2)}</span>
                        </div>
                      </div>
                      <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                        +{e.growth_pct.toFixed(0)}%
                      </Badge>
                    </div>
                  ))}
                  {insights.emerging.length === 0 && (
                    <p className="text-xs text-muted-foreground text-center py-3">No emerging topics this horizon.</p>
                  )}
                </CardContent>
              </Card>

              {/* Recommendations */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Target className="h-4 w-4 text-emerald-600" /> Best areas to focus on
                  </CardTitle>
                  <CardDescription>
                    Combines projected growth with current saturation — high score = good growth, low competition.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {insights.recommendations.map((r, i) => {
                    const sat = r.saturation;
                    const satTone = sat < 0.4 ? "bg-emerald-100 text-emerald-700" : sat < 0.7 ? "bg-amber-100 text-amber-700" : "bg-rose-100 text-rose-700";
                    return (
                      <div key={r.topic} className="rounded-md border p-3 space-y-2">
                        <div className="flex items-start justify-between gap-2 flex-wrap">
                          <div className="flex items-center gap-2 flex-wrap">
                            <Badge variant="outline" className="font-mono text-[10px]">#{i + 1}</Badge>
                            <h3 className="font-semibold">{r.suggested_title}</h3>
                          </div>
                          <div className="flex gap-2">
                            <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
                              {r.growth_pct >= 0 ? "+" : ""}{r.growth_pct.toFixed(0)}% growth
                            </Badge>
                            <Badge variant="outline" className={satTone}>
                              {(sat * 100).toFixed(0)}% saturation
                            </Badge>
                          </div>
                        </div>
                        <p className="text-xs text-muted-foreground">{renderInline(r.rationale)}</p>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            </>
          )}
        </>
      )}
    </div>
  );
}

// ─── Sub-components ──────────────────────────────────────────────────────

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg bg-white/15 backdrop-blur-sm px-3 py-1.5 text-xs">
      <p className="text-white/70">{label}</p>
      <p className="font-semibold text-sm capitalize">{value}</p>
    </div>
  );
}

function StoryStep({ icon, step, title, body }: { icon: React.ReactNode; step: string; title: string; body: string }) {
  return (
    <Card>
      <CardContent className="p-4 space-y-2">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100 text-indigo-700">{icon}</span>
          <span className="text-xs text-muted-foreground">Step {step}</span>
        </div>
        <h3 className="font-semibold text-sm">{title}</h3>
        <p className="text-xs text-muted-foreground leading-relaxed">{body}</p>
      </CardContent>
    </Card>
  );
}

function ForecastCard({ forecast }: { forecast: Forecast }) {
  const dir = DIRECTION_INFO[forecast.trend_direction] || DIRECTION_INFO.unknown;
  const DirIcon = dir.Icon;
  const data = useMemo(() => buildSeries(forecast), [forecast]);
  const lastHistYear = forecast.historical[forecast.historical.length - 1]?.year;
  const peak = forecast.stats.historical_peak;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <CardTitle className="text-lg capitalize flex items-center gap-2">
              {forecast.topic.replace(/_/g, " ")}
              <Badge variant="outline" className="text-[10px]">{forecast.model_type}</Badge>
            </CardTitle>
            <CardDescription>
              Data: {forecast.data_range} · {forecast.historical.length} historical points
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={`${dir.bg} ${dir.color} ${dir.ring}`}>
              <DirIcon className="h-3 w-3 mr-1" /> {dir.label}
            </Badge>
            <Badge variant="outline" className="bg-indigo-50 text-indigo-700 border-indigo-200">
              {forecast.growth_pct >= 0 ? "+" : ""}{forecast.growth_pct.toFixed(0)}%
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data}>
              <defs>
                <linearGradient id={`ci-grad-${forecast.topic}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#10b981" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="year" stroke="currentColor" opacity={0.7} />
              <YAxis stroke="currentColor" opacity={0.7} />
              <Tooltip
                contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8 }}
                formatter={(value: number, name: string) => [
                  typeof value === "number" ? value.toFixed(1) : value,
                  name === "historical" ? "Historical" :
                    name === "forecast" ? "Forecast" :
                      name === "lower" ? "CI lower" :
                        name === "upper" ? "CI upper" : name,
                ]}
              />
              <Legend />
              {lastHistYear && (
                <ReferenceLine x={lastHistYear} stroke="#9ca3af" strokeDasharray="4 4"
                  label={{ value: "Forecast →", position: "top", fontSize: 10, fill: "#6b7280" }} />
              )}
              {/* Confidence interval band — drawn as upper area, hidden lower for delta */}
              <Area
                type="monotone" dataKey="upper" stackId="ci"
                stroke="none" fill={`url(#ci-grad-${forecast.topic})`} name="95% CI upper" />
              <Area
                type="monotone" dataKey="lower" stackId="ci"
                stroke="none" fill="hsl(var(--background))" name="95% CI lower" />
              <Line
                type="monotone" dataKey="historical" stroke="#6366f1" strokeWidth={2.5}
                dot={{ r: 2 }} connectNulls name="Historical"
              />
              <Line
                type="monotone" dataKey="forecast" stroke="#10b981" strokeWidth={2.5}
                strokeDasharray="6 4" dot={{ r: 3 }} connectNulls name="Forecast"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Insight + accuracy strip */}
        <p className="text-xs leading-relaxed mt-3 text-muted-foreground">
          {renderInline(forecast.interpretation)}
        </p>

        <div className="mt-3 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
          <MiniStat label="Current" value={forecast.stats.current_count ?? "—"} />
          <MiniStat label={`In ${forecast.horizon_years}y`} value={(forecast.stats.forecast_end ?? 0).toFixed(0)} />
          <MiniStat label="Peak year" value={peak ? `${peak.year} (${peak.count})` : "—"} />
          <MiniStat label="Total papers" value={forecast.stats.historical_total ?? "—"} />
        </div>

        {forecast.accuracy.available && (
          <div className="mt-2 rounded-md border bg-muted/30 p-2 text-[11px] text-muted-foreground flex items-center gap-3 flex-wrap">
            <CheckCircle2 className="h-3 w-3 text-emerald-600" />
            <span>Model accuracy:</span>
            <span>RMSE <strong>{forecast.accuracy.rmse.toFixed(2)}</strong></span>
            <span>MAE <strong>{forecast.accuracy.mae.toFixed(2)}</strong></span>
            <span>n = {forecast.accuracy.n_observations}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function MiniStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md bg-muted/40 p-2">
      <p className="text-muted-foreground text-[10px] uppercase tracking-wide">{label}</p>
      <p className="font-semibold tabular-nums">{value}</p>
    </div>
  );
}

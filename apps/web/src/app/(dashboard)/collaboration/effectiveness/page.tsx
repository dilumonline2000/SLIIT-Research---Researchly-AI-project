"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp, Search, Star, Mail, ArrowLeft, Loader2, Users, MessageSquare,
  ShieldCheck,
} from "lucide-react";
import { PageHero, SegmentedTabs } from "@/components/shared/PageHero";
import { API_ROUTES } from "@/lib/constants";
import { apiGet } from "@/lib/api";
import { getCache, setCache } from "@/lib/supervisorCache";

// ─── Types ────────────────────────────────────────────────────────────────

interface SupervisorSummary {
  key: string;
  source: "sliit" | "system";
  name: string;
  email: string | null;
  department: string | null;
  research_areas: string[];
  research_cluster: string | null;
  rank: string | null;
  level: string | null;
  availability: boolean | null;
  current_students: number | null;
  max_students: number | null;
  avg_stars: number | null;
  n_ratings: number;
  overall_score: number | null;
}

interface RecentFeedback {
  id: string;
  stars: number;
  feedback_text: string | null;
  overall_sentiment: string | null;
  sentiment_score: number | null;
  rater_name: string | null;
  rater_email: string | null;
  created_at: string | null;
}

interface EffectivenessDetail {
  supervisor: SupervisorSummary;
  overall_score: number;
  completion_rate: number;
  avg_feedback_sentiment: number;
  student_satisfaction: number;
  avg_stars: number | null;
  n_ratings: number;
  breakdown: Record<string, unknown>;
  recent_feedback: RecentFeedback[];
}

// ─── Cache key ────────────────────────────────────────────────────────────

const CACHE_KEY = "effectiveness-supervisors";

// ─── Star display ─────────────────────────────────────────────────────────

function StarDisplay({ value, size = 16 }: { value: number; size?: number }) {
  const full = Math.round(value);
  return (
    <span className="inline-flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          style={{ width: size, height: size }}
          className={i <= full ? "fill-amber-400 text-amber-400" : "text-muted-foreground/30"}
        />
      ))}
    </span>
  );
}

const sentimentColor = (s: string | null) => {
  if (s === "positive") return "text-emerald-700 bg-emerald-50 border-emerald-200";
  if (s === "negative") return "text-red-700 bg-red-50 border-red-200";
  return "text-amber-700 bg-amber-50 border-amber-200";
};

// ─── Page ─────────────────────────────────────────────────────────────────

export default function EffectivenessPage() {
  const [supervisors, setSupervisors] = useState<SupervisorSummary[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "sliit" | "system">("all");

  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [detail, setDetail] = useState<EffectivenessDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState("");

  // Load supervisor list — check module-level cache first
  useEffect(() => {
    const cached = getCache<SupervisorSummary[]>(CACHE_KEY);
    if (cached) {
      setSupervisors(cached);
      return;
    }
    let cancelled = false;
    setLoadingList(true);
    apiGet<{ supervisors: SupervisorSummary[]; total: number }>(API_ROUTES.module2.effectivenessList)
      .then((d) => {
        if (!cancelled) {
          setSupervisors(d.supervisors);
          setCache(CACHE_KEY, d.supervisors);
        }
      })
      .catch(() => { if (!cancelled) setSupervisors([]); })
      .finally(() => { if (!cancelled) setLoadingList(false); });
    return () => { cancelled = true; };
  }, []);

  // Load detail when a supervisor is selected
  useEffect(() => {
    if (!selectedKey) { setDetail(null); return; }
    let cancelled = false;
    setLoadingDetail(true);
    setError("");
    apiGet<EffectivenessDetail>(
      `${API_ROUTES.module2.effectivenessByKey}?supervisor_key=${encodeURIComponent(selectedKey)}`,
    )
      .then((d) => { if (!cancelled) setDetail(d); })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not load details");
      })
      .finally(() => { if (!cancelled) setLoadingDetail(false); });
    return () => { cancelled = true; };
  }, [selectedKey]);

  const filtered = useMemo(() => {
    let list = supervisors;
    if (filter !== "all") list = list.filter((s) => s.source === filter);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          (s.department || "").toLowerCase().includes(q) ||
          s.research_areas.join(" ").toLowerCase().includes(q),
      );
    }
    return list;
  }, [supervisors, search, filter]);

  // ── Detail view ──────────────────────────────────────────────────────
  if (selectedKey && (loadingDetail || detail || error)) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" size="sm" onClick={() => setSelectedKey(null)}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to all supervisors
        </Button>

        {loadingDetail && (
          <Card>
            <CardContent className="py-12 text-center text-sm text-muted-foreground">
              <Loader2 className="mx-auto h-5 w-5 animate-spin mb-2" />
              Loading effectiveness profile…
            </CardContent>
          </Card>
        )}

        {error && (
          <Card>
            <CardContent className="py-6 text-sm text-destructive">{error}</CardContent>
          </Card>
        )}

        {detail && (
          <>
            {/* Header card */}
            <Card className="overflow-hidden">
              <div className="bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 p-6 text-white">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h2 className="text-xl font-bold">
                        {detail.supervisor.rank ? `${detail.supervisor.rank} ` : ""}
                        {detail.supervisor.name}
                      </h2>
                      <Badge variant="outline" className="bg-white/15 border-white/30 text-white text-[11px]">
                        {detail.supervisor.source === "sliit" ? "SLIIT" : "System"}
                      </Badge>
                      {detail.supervisor.availability !== false ? (
                        <Badge variant="outline" className="bg-emerald-500/20 border-emerald-300/30 text-white text-[11px]">
                          Available
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="bg-red-500/20 border-red-300/30 text-white text-[11px]">
                          Not accepting
                        </Badge>
                      )}
                    </div>
                    {detail.supervisor.department && (
                      <p className="mt-1 text-sm text-white/85">
                        {detail.supervisor.department}
                        {detail.supervisor.research_cluster ? ` · ${detail.supervisor.research_cluster}` : ""}
                      </p>
                    )}
                  </div>
                  {detail.supervisor.email && (
                    <a
                      href={`mailto:${detail.supervisor.email}?subject=${encodeURIComponent("Research supervision enquiry")}`}
                      className="inline-flex items-center gap-2 rounded-md bg-white/15 hover:bg-white/25 backdrop-blur-sm px-3 py-2 text-sm font-medium transition-colors"
                    >
                      <Mail className="h-4 w-4" /> Contact via email
                    </a>
                  )}
                </div>

                {detail.supervisor.research_areas.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {detail.supervisor.research_areas.slice(0, 8).map((a) => (
                      <span key={a} className="rounded-full bg-white/15 px-2.5 py-0.5 text-[11px] backdrop-blur-sm">
                        {a}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Stat strip */}
              <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6">
                <div>
                  <p className="text-xs text-muted-foreground">Effectiveness</p>
                  <p className="text-2xl font-bold">{(detail.overall_score * 100).toFixed(0)}%</p>
                  <div className="h-1.5 mt-1 rounded-full bg-secondary overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-emerald-500 to-teal-400"
                      style={{ width: `${(detail.overall_score * 100).toFixed(0)}%` }}
                    />
                  </div>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Average rating</p>
                  <p className="text-2xl font-bold">
                    {detail.avg_stars !== null ? detail.avg_stars.toFixed(1) : "—"}
                  </p>
                  {detail.avg_stars !== null && <StarDisplay value={detail.avg_stars} />}
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Ratings received</p>
                  <p className="text-2xl font-bold">{detail.n_ratings}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Avg sentiment</p>
                  <p className="text-2xl font-bold">{detail.avg_feedback_sentiment.toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground">−1 to +1</p>
                </div>
              </CardContent>
            </Card>

            {/* Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Score breakdown</CardTitle>
                <CardDescription>How the effectiveness % was computed.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <Row label="Star score" value={detail.avg_stars !== null ? `${detail.avg_stars.toFixed(2)} / 5` : "—"} weight="40%" />
                <Row label="Avg sentiment" value={detail.avg_feedback_sentiment.toFixed(2)} weight="25%" />
                <Row label="Student satisfaction" value={`${(detail.student_satisfaction * 100).toFixed(0)}%`} weight="15%" />
                <Row label="Completion rate" value={`${(detail.completion_rate * 100).toFixed(0)}%`} weight="20%" />
              </CardContent>
            </Card>

            {/* Recent feedback */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 text-emerald-500" /> Recent feedback ({detail.recent_feedback.length})
                </CardTitle>
                <CardDescription>
                  Verified reviews from students who have worked with this supervisor.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {detail.recent_feedback.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No feedback yet. Be the first to{" "}
                    <a href="/collaboration/feedback" className="text-primary hover:underline">
                      leave a rating
                    </a>
                    .
                  </p>
                ) : (
                  detail.recent_feedback.map((fb) => (
                    <div key={fb.id} className="rounded-md border bg-muted/30 p-3 space-y-2">
                      {/* Reviewer identity */}
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <StarDisplay value={fb.stars} size={14} />
                          <div className="flex items-center gap-1.5">
                            <span className="text-xs font-medium">
                              {fb.rater_name || "Anonymous"}
                            </span>
                            {fb.rater_email && (
                              <span className="inline-flex items-center gap-1 rounded-full border bg-background px-2 py-0.5 text-[11px] text-muted-foreground">
                                <ShieldCheck className="h-3 w-3 text-emerald-500" />
                                {fb.rater_email}
                              </span>
                            )}
                          </div>
                        </div>
                        {fb.overall_sentiment && (
                          <Badge
                            variant="outline"
                            className={`text-[11px] ${sentimentColor(fb.overall_sentiment)}`}
                          >
                            {fb.overall_sentiment}
                          </Badge>
                        )}
                      </div>

                      {/* Comment */}
                      {fb.feedback_text ? (
                        <p className="text-sm leading-relaxed">{fb.feedback_text}</p>
                      ) : (
                        <p className="text-xs text-muted-foreground italic">(no written comment)</p>
                      )}

                      {/* Meta */}
                      <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                        {fb.created_at && (
                          <span>{new Date(fb.created_at).toLocaleDateString()}</span>
                        )}
                        {fb.sentiment_score !== null && (
                          <span>Sentiment score: {fb.sentiment_score?.toFixed(2)}</span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    );
  }

  // ── List view ────────────────────────────────────────────────────────
  return (
    <div className="space-y-6 pb-8">
      <PageHero
        theme="mentor"
        icon={TrendingUp}
        eyebrow="Mentor Network · Effectiveness"
        title="Supervisor Effectiveness"
        description="Browse all supervisors with their aggregate ratings and verified feedback. Click any row to see the full effectiveness breakdown and recent comments."
        stats={[
          { label: "Showing", value: filtered.length, icon: Users },
          { label: "Rated", value: filtered.filter((s) => s.n_ratings > 0).length, icon: Star },
        ]}
      />

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by name, department, or research area…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-11 rounded-xl bg-card pl-10 pr-10 shadow-soft"
          />
          {loadingList && (
            <Loader2 className="absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted-foreground" />
          )}
        </div>
        <SegmentedTabs
          theme="mentor"
          value={filter}
          onChange={setFilter}
          tabs={[
            { id: "all", label: "All" },
            { id: "sliit", label: "SLIIT" },
            { id: "system", label: "SYSTEM" },
          ]}
        />
      </div>

      <div className="grid gap-3 xl:grid-cols-2">
        {filtered.map((s) => (
          <Card
            key={s.key}
            className="group cursor-pointer transition-all hover:-translate-y-0.5 hover:border-emerald-500/30 hover:shadow-lg"
            onClick={() => setSelectedKey(s.key)}
          >
            <CardContent className="flex flex-wrap items-start gap-4 p-4 sm:p-5">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 font-display text-sm font-bold text-white shadow-sm">
                {s.name.split(/\s+/).filter((p) => !/^(dr|prof|mr|ms|mrs)\.?$/i.test(p)).slice(0, 2).map((p) => p[0]).join("").toUpperCase()}
              </div>
              <div className="min-w-0 flex-1 sm:min-w-[220px]">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-semibold">
                    {s.rank ? `${s.rank} ` : ""}{s.name}
                  </h3>
                  <Badge
                    variant="outline"
                    className={
                      s.source === "sliit"
                        ? "bg-blue-50 text-blue-700 border-blue-200 text-[11px]"
                        : "bg-purple-50 text-purple-700 border-purple-200 text-[11px]"
                    }
                  >
                    {s.source.toUpperCase()}
                  </Badge>
                  {s.availability === false && (
                    <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200 text-[11px]">
                      Unavailable
                    </Badge>
                  )}
                </div>
                {s.department && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {s.department}
                    {s.research_cluster ? ` · ${s.research_cluster}` : ""}
                  </p>
                )}
                {s.research_areas.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {s.research_areas.slice(0, 4).map((a) => (
                      <span key={a} className="text-[11px] rounded-full bg-muted px-2 py-0.5">
                        {a}
                      </span>
                    ))}
                    {s.research_areas.length > 4 && (
                      <span className="text-[11px] text-muted-foreground">
                        +{s.research_areas.length - 4}
                      </span>
                    )}
                  </div>
                )}
              </div>

              <div className="flex w-full items-center justify-between gap-6 border-t pt-3 text-right sm:w-auto sm:justify-end sm:border-0 sm:pt-0">
                <div className="min-w-[90px]">
                  <p className="text-[11px] text-muted-foreground uppercase tracking-wide">Effectiveness</p>
                  <p className="font-display text-xl font-bold text-emerald-600 dark:text-emerald-400">{((s.overall_score ?? 0) * 100).toFixed(0)}%</p>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400"
                      style={{ width: `${Math.round((s.overall_score ?? 0) * 100)}%` }}
                    />
                  </div>
                </div>
                <div>
                  <p className="text-[11px] text-muted-foreground uppercase tracking-wide">Rating</p>
                  {s.avg_stars !== null ? (
                    <div className="flex items-center gap-1">
                      <span className="text-lg font-semibold">{s.avg_stars.toFixed(1)}</span>
                      <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No ratings yet</p>
                  )}
                  <p className="text-[11px] text-muted-foreground">{s.n_ratings} ratings</p>
                </div>
                {s.email && (
                  <a
                    href={`mailto:${s.email}?subject=${encodeURIComponent("Research supervision enquiry")}`}
                    onClick={(e) => e.stopPropagation()}
                    title="Email supervisor"
                    className="rounded-lg border p-2 transition-colors hover:border-emerald-500/40 hover:bg-emerald-500/10"
                  >
                    <Mail className="h-4 w-4 text-muted-foreground" />
                  </a>
                )}
              </div>
            </CardContent>
          </Card>
        ))}

        {!loadingList && filtered.length === 0 && (
          <Card>
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              No supervisors match your filters.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function Row({ label, value, weight }: { label: string; value: string; weight: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <div className="flex items-center gap-3">
        <span className="font-medium">{value}</span>
        <Badge variant="secondary" className="text-[11px]">weight {weight}</Badge>
      </div>
    </div>
  );
}

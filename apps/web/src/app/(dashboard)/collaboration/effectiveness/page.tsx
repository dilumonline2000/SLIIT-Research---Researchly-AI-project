"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp, Search, Star, Mail, ArrowLeft, Loader2, Users, MessageSquare,
} from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiGet } from "@/lib/api";

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

// ─── Star display ────────────────────────────────────────────────────────

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

// ─── Page ────────────────────────────────────────────────────────────────

export default function EffectivenessPage() {
  const [supervisors, setSupervisors] = useState<SupervisorSummary[]>([]);
  const [loadingList, setLoadingList] = useState(false);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "sliit" | "system">("all");

  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [detail, setDetail] = useState<EffectivenessDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoadingList(true);
    apiGet<{ supervisors: SupervisorSummary[]; total: number }>(API_ROUTES.module2.effectivenessList)
      .then((d) => {
        if (!cancelled) setSupervisors(d.supervisors);
      })
      .catch(() => {
        if (!cancelled) setSupervisors([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingList(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedKey) {
      setDetail(null);
      return;
    }
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
      list = list.filter((s) =>
        s.name.toLowerCase().includes(q) ||
        (s.department || "").toLowerCase().includes(q) ||
        s.research_areas.join(" ").toLowerCase().includes(q),
      );
    }
    return list;
  }, [supervisors, search, filter]);

  // ── Detail view ─────────────────────────────────────────────
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
              <div className="bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-600 p-6 text-white">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <h2 className="text-xl font-bold">
                        {detail.supervisor.rank ? `${detail.supervisor.rank} ` : ""}{detail.supervisor.name}
                      </h2>
                      <Badge variant="outline" className="bg-white/15 border-white/30 text-white text-[10px]">
                        {detail.supervisor.source === "sliit" ? "SLIIT" : "System"}
                      </Badge>
                      {detail.supervisor.availability !== false ? (
                        <Badge variant="outline" className="bg-emerald-500/20 border-emerald-300/30 text-white text-[10px]">
                          Available
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="bg-red-500/20 border-red-300/30 text-white text-[10px]">
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
                    <div className="h-full bg-gradient-to-r from-purple-500 to-indigo-500"
                         style={{ width: `${(detail.overall_score * 100).toFixed(0)}%` }} />
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
                  <MessageSquare className="h-4 w-4" /> Recent feedback ({detail.recent_feedback.length})
                </CardTitle>
                <CardDescription>
                  Real comments from students who&apos;ve worked with this supervisor.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {detail.recent_feedback.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No feedback yet. Be the first to <a href="/collaboration/feedback" className="text-primary hover:underline">leave a rating</a>.
                  </p>
                ) : (
                  detail.recent_feedback.map((fb) => (
                    <div key={fb.id} className="rounded-md border bg-muted/30 p-3 space-y-1.5">
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-2">
                          <StarDisplay value={fb.stars} size={14} />
                          <span className="text-xs text-muted-foreground">
                            {fb.rater_name || "Anonymous"}
                          </span>
                        </div>
                        {fb.overall_sentiment && (
                          <Badge variant="outline" className={`text-[10px] ${sentimentColor(fb.overall_sentiment)}`}>
                            {fb.overall_sentiment}
                          </Badge>
                        )}
                      </div>
                      {fb.feedback_text ? (
                        <p className="text-sm leading-relaxed">{fb.feedback_text}</p>
                      ) : (
                        <p className="text-xs text-muted-foreground italic">(no written comment)</p>
                      )}
                      {fb.created_at && (
                        <p className="text-[10px] text-muted-foreground">
                          {new Date(fb.created_at).toLocaleDateString()}
                        </p>
                      )}
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

  // ── List view ───────────────────────────────────────────────
  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-600 p-6 text-white shadow-lg">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <TrendingUp className="h-7 w-7" /> Supervisor Effectiveness
        </h1>
        <p className="mt-1 text-sm text-white/85 max-w-2xl">
          Browse all supervisors with their aggregate ratings and feedback. Click any row to see the
          full effectiveness breakdown and recent comments.
        </p>
      </div>

      <Card>
        <CardContent className="p-3 flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 flex-1 min-w-[200px]">
            <Search className="h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by name, department, or research area..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="border-0 focus-visible:ring-0 shadow-none"
            />
          </div>
          <div className="flex gap-1">
            {(["all", "sliit", "system"] as const).map((f) => (
              <Button
                key={f}
                size="sm"
                variant={filter === f ? "default" : "outline"}
                onClick={() => setFilter(f)}
                className="text-xs"
              >
                {f === "all" ? "All" : f.toUpperCase()}
              </Button>
            ))}
          </div>
          {loadingList && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
          <Badge variant="outline" className="shrink-0">
            <Users className="h-3 w-3 mr-1" /> {filtered.length}
          </Badge>
        </CardContent>
      </Card>

      <div className="grid gap-3">
        {filtered.map((s) => (
          <Card
            key={s.key}
            className="hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => setSelectedKey(s.key)}
          >
            <CardContent className="p-4 flex items-start gap-4 flex-wrap">
              <div className="flex-1 min-w-[240px]">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-semibold">
                    {s.rank ? `${s.rank} ` : ""}{s.name}
                  </h3>
                  <Badge variant="outline" className={
                    s.source === "sliit"
                      ? "bg-blue-50 text-blue-700 border-blue-200 text-[10px]"
                      : "bg-purple-50 text-purple-700 border-purple-200 text-[10px]"
                  }>
                    {s.source.toUpperCase()}
                  </Badge>
                  {s.availability === false && (
                    <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200 text-[10px]">
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
                      <span key={a} className="text-[10px] rounded-full bg-muted px-2 py-0.5">
                        {a}
                      </span>
                    ))}
                    {s.research_areas.length > 4 && (
                      <span className="text-[10px] text-muted-foreground">+{s.research_areas.length - 4}</span>
                    )}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-6 text-right">
                <div>
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Effectiveness</p>
                  <p className="text-xl font-bold">{((s.overall_score ?? 0) * 100).toFixed(0)}%</p>
                </div>
                <div>
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Rating</p>
                  {s.avg_stars !== null ? (
                    <div className="flex items-center gap-1">
                      <span className="text-lg font-semibold">{s.avg_stars.toFixed(1)}</span>
                      <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No ratings yet</p>
                  )}
                  <p className="text-[10px] text-muted-foreground">{s.n_ratings} ratings</p>
                </div>
                {s.email && (
                  <a
                    href={`mailto:${s.email}?subject=${encodeURIComponent("Research supervision enquiry")}`}
                    onClick={(e) => e.stopPropagation()}
                    title="Email supervisor"
                    className="rounded-md border p-2 hover:bg-accent transition-colors"
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
        <Badge variant="secondary" className="text-[10px]">weight {weight}</Badge>
      </div>
    </div>
  );
}

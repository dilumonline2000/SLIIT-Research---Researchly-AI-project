"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Star, MessageSquare, CheckCircle2, AlertCircle, Loader2, User, Search,
} from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiGet, apiPost } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

// ─── Types ────────────────────────────────────────────────────────────────

interface SupervisorEntry {
  key: string;
  source: "sliit" | "system";
  name: string;
  email: string | null;
  department: string | null;
  research_cluster: string | null;
  research_areas: string[];
  rank: string | null;
  level: string | null;
  availability: boolean | null;
}

interface SubmitResponse {
  rating_id: string;
  supervisor_key: string;
  stars: number;
  overall_sentiment: string | null;
  overall_score: number | null;
}

const sentimentColor = (s: string | null) => {
  if (s === "positive") return "text-emerald-700 bg-emerald-50 border-emerald-200";
  if (s === "negative") return "text-red-700 bg-red-50 border-red-200";
  return "text-amber-700 bg-amber-50 border-amber-200";
};

// ─── Star rating ─────────────────────────────────────────────────────────

function StarPicker({
  value,
  onChange,
  size = 28,
}: {
  value: number;
  onChange: (n: number) => void;
  size?: number;
}) {
  const [hover, setHover] = useState(0);
  const display = hover || value;
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((i) => (
        <button
          key={i}
          type="button"
          onClick={() => onChange(i)}
          onMouseEnter={() => setHover(i)}
          onMouseLeave={() => setHover(0)}
          className="transition-transform hover:scale-110"
          aria-label={`${i} star${i > 1 ? "s" : ""}`}
        >
          <Star
            style={{ width: size, height: size }}
            className={
              i <= display
                ? "fill-amber-400 text-amber-400"
                : "text-muted-foreground/40"
            }
          />
        </button>
      ))}
      <span className="ml-2 text-sm text-muted-foreground tabular-nums">
        {value > 0 ? `${value} / 5` : "Pick a rating"}
      </span>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────

export default function FeedbackAnalysisPage() {
  const { user, profile } = useAuthStore();

  const [supervisors, setSupervisors] = useState<SupervisorEntry[]>([]);
  const [loadingSups, setLoadingSups] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedKey, setSelectedKey] = useState<string>("");

  const [stars, setStars] = useState(0);
  const [feedback, setFeedback] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<SubmitResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoadingSups(true);
    apiGet<{ supervisors: SupervisorEntry[]; total: number }>(API_ROUTES.module2.supervisorList)
      .then((d) => {
        if (!cancelled) setSupervisors(d.supervisors);
      })
      .catch(() => {
        if (!cancelled) setSupervisors([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingSups(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selected = useMemo(
    () => supervisors.find((s) => s.key === selectedKey) || null,
    [supervisors, selectedKey],
  );

  const filtered = useMemo(() => {
    if (!search.trim()) return supervisors;
    const q = search.toLowerCase();
    return supervisors.filter((s) =>
      s.name.toLowerCase().includes(q) ||
      (s.department || "").toLowerCase().includes(q) ||
      (s.research_areas.join(" ").toLowerCase()).includes(q),
    );
  }, [supervisors, search]);

  const handleSubmit = async () => {
    setError("");
    setResult(null);
    if (!selectedKey) {
      setError("Please select a supervisor first.");
      return;
    }
    if (stars < 1) {
      setError("Please give a star rating between 1 and 5.");
      return;
    }
    setSubmitting(true);
    try {
      const profileObj = profile as { full_name?: string } | null;
      const data = await apiPost<SubmitResponse>(API_ROUTES.module2.submitFeedback, {
        supervisor_key: selectedKey,
        stars,
        feedback_text: feedback.trim() || null,
        rater_id: user?.id ?? null,
        rater_name: profileObj?.full_name ?? null,
      });
      setResult(data);
      setStars(0);
      setFeedback("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit feedback.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-gradient-to-br from-amber-500 via-orange-500 to-pink-500 p-6 text-white shadow-lg">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <MessageSquare className="h-7 w-7" /> Supervisor Feedback
        </h1>
        <p className="mt-1 text-sm text-white/85 max-w-2xl">
          Rate a supervisor and leave written feedback. Your rating contributes to that
          supervisor&apos;s effectiveness score visible in the next tab.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">1 · Choose a supervisor</CardTitle>
          <CardDescription>
            Pick from {supervisors.length} supervisors (74 from SLIIT + system supervisors).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2 rounded-md border bg-background px-2">
            <Search className="h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by name, department, or research area..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="border-0 focus-visible:ring-0 shadow-none"
            />
            {loadingSups && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
          </div>

          <select
            value={selectedKey}
            onChange={(e) => setSelectedKey(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">— select supervisor —</option>
            {filtered.map((s) => (
              <option key={s.key} value={s.key}>
                {s.name} {s.department ? `· ${s.department}` : ""} {s.source === "sliit" ? "(SLIIT)" : "(System)"}
              </option>
            ))}
          </select>

          {selected && (
            <div className="rounded-md border bg-muted/30 p-3 text-sm space-y-1.5">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <span className="font-semibold">
                  {selected.rank ? `${selected.rank} ` : ""}{selected.name}
                </span>
                <Badge variant="outline" className={
                  selected.source === "sliit"
                    ? "bg-blue-50 text-blue-700 border-blue-200 text-[10px]"
                    : "bg-purple-50 text-purple-700 border-purple-200 text-[10px]"
                }>
                  {selected.source.toUpperCase()}
                </Badge>
                {selected.availability === false && (
                  <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200 text-[10px]">
                    Unavailable
                  </Badge>
                )}
              </div>
              {selected.department && (
                <p className="text-xs text-muted-foreground">
                  {selected.department}{selected.research_cluster ? ` · ${selected.research_cluster}` : ""}
                </p>
              )}
              {selected.research_areas.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-1">
                  {selected.research_areas.slice(0, 6).map((a) => (
                    <span key={a} className="rounded-full bg-background border px-2 py-0.5 text-[10px]">
                      {a}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">2 · Rate &amp; review</CardTitle>
          <CardDescription>
            Stars are mandatory. Written feedback is optional but adds rich context.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Your rating *</Label>
            <StarPicker value={stars} onChange={setStars} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="feedback">Written feedback (optional)</Label>
            <textarea
              id="feedback"
              className="flex min-h-[140px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="What stood out about this supervisor? Methodology guidance, communication, availability, support during writing…"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              If you write feedback, an aspect-based sentiment analysis is run automatically.
            </p>
          </div>

          <Button onClick={handleSubmit} disabled={submitting || !selectedKey || stars < 1}>
            {submitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Submitting…
              </>
            ) : (
              "Submit Feedback"
            )}
          </Button>

          {error && (
            <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {result && (
            <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm space-y-1">
              <div className="flex items-center gap-2 font-medium text-emerald-900">
                <CheckCircle2 className="h-4 w-4" />
                Feedback saved.
              </div>
              <div className="flex flex-wrap gap-2 text-xs">
                <Badge variant="outline" className="bg-white">
                  {result.stars} ★
                </Badge>
                {result.overall_sentiment && (
                  <Badge variant="outline" className={sentimentColor(result.overall_sentiment)}>
                    Sentiment: {result.overall_sentiment}
                  </Badge>
                )}
                {result.overall_score !== null && (
                  <Badge variant="outline" className="bg-white">
                    Score: {result.overall_score.toFixed(2)}
                  </Badge>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

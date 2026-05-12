"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import {
  ArrowLeft, ExternalLink, BookOpen, BarChart2, Mail, Loader2,
  Users, GraduationCap, Search, ChevronRight,
} from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiPost, apiGet } from "@/lib/api";

// ─── Types ────────────────────────────────────────────────────────────────

interface SupervisorMatch {
  supervisor_id: number;
  name: string;
  email: string;
  department: string;
  research_cluster: string;
  research_interests: string[];
  similarity_score: number;
  multi_factor_score: number;
  explanation: string;
  availability: boolean;
  current_students: number;
  max_students: number;
}

interface PaperEntry {
  paper_id: string;
  title: string;
  year: number | null;
  venue: string | null;
  url: string | null;
  doi: string | null;
}

interface SupervisorPapersResponse {
  supervisor_id: number;
  name: string;
  department: string;
  research_interests: string[];
  papers: PaperEntry[];
  total: number;
  year_distribution: Record<string, number>;
  topic_distribution: Array<{ name: string; value: number }>;
}

// ─── Constants ─────────────────────────────────────────────────────────────

const CHART_COLORS = [
  "#6366f1", "#8b5cf6", "#a78bfa", "#c084fc",
  "#7c3aed", "#4f46e5", "#4338ca", "#3730a3", "#ec4899", "#f43f5e",
];

// ─── Score bar ────────────────────────────────────────────────────────────

function ScoreBar({ value, color = "from-indigo-500 to-purple-500" }: { value: number; color?: string }) {
  return (
    <div className="h-1.5 w-full rounded-full bg-secondary overflow-hidden">
      <div
        className={`h-full rounded-full bg-gradient-to-r ${color}`}
        style={{ width: `${(value * 100).toFixed(0)}%` }}
      />
    </div>
  );
}

// ─── Detail view ─────────────────────────────────────────────────────────

function SupervisorDetailView({
  match,
  papers,
  loadingPapers,
  onBack,
}: {
  match: SupervisorMatch;
  papers: SupervisorPapersResponse | null;
  loadingPapers: boolean;
  onBack: () => void;
}) {
  const yearData = papers
    ? Object.entries(papers.year_distribution).map(([year, count]) => ({ year, count }))
    : [];

  const topicData = papers?.topic_distribution ?? [];

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" onClick={onBack}>
        <ArrowLeft className="mr-2 h-4 w-4" /> Back to matches
      </Button>

      {/* Header */}
      <Card className="overflow-hidden">
        <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 p-6 text-white">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <GraduationCap className="h-5 w-5 opacity-80" />
                <h2 className="text-xl font-bold">{match.name}</h2>
                <Badge variant="outline" className="bg-white/15 border-white/30 text-white text-[10px]">
                  SLIIT
                </Badge>
                <Badge
                  variant="outline"
                  className={`text-[10px] ${match.availability
                    ? "bg-emerald-500/20 border-emerald-300/30 text-white"
                    : "bg-red-500/20 border-red-300/30 text-white"}`}
                >
                  {match.availability ? "Available" : "Not accepting"}
                </Badge>
              </div>
              <p className="text-sm text-white/85">
                {match.department}
                {match.research_cluster ? ` · ${match.research_cluster}` : ""}
              </p>
            </div>
            <a
              href={`mailto:${match.email}?subject=${encodeURIComponent("Research Supervision Enquiry")}`}
              className="inline-flex items-center gap-2 rounded-md bg-white/15 hover:bg-white/25 backdrop-blur-sm px-3 py-2 text-sm font-medium transition-colors"
            >
              <Mail className="h-4 w-4" /> Contact via email
            </a>
          </div>

          {/* Match stats */}
          <div className="mt-4 grid grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-white/70 uppercase tracking-wide">Match Score</p>
              <p className="text-2xl font-bold">{(match.multi_factor_score * 100).toFixed(0)}%</p>
              <ScoreBar value={match.multi_factor_score} />
            </div>
            <div>
              <p className="text-xs text-white/70 uppercase tracking-wide">Similarity</p>
              <p className="text-2xl font-bold">{(match.similarity_score * 100).toFixed(0)}%</p>
              <ScoreBar value={match.similarity_score} color="from-pink-500 to-rose-500" />
            </div>
            <div>
              <p className="text-xs text-white/70 uppercase tracking-wide">Students</p>
              <p className="text-2xl font-bold">
                {match.current_students}
                <span className="text-base font-normal text-white/70">/{match.max_students}</span>
              </p>
            </div>
          </div>

          {/* Research interests tags */}
          {match.research_interests.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-1.5">
              {match.research_interests.map((ri) => (
                <span key={ri} className="rounded-full bg-white/15 px-2.5 py-0.5 text-[11px] backdrop-blur-sm">
                  {ri}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* AI explanation */}
        <CardContent className="pt-4">
          <p className="text-sm text-muted-foreground leading-relaxed">{match.explanation}</p>
        </CardContent>
      </Card>

      {/* Publications */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-indigo-500" />
            Research Publications
            {papers && (
              <Badge variant="secondary" className="ml-auto text-xs">
                {papers.total} found via Semantic Scholar
              </Badge>
            )}
          </CardTitle>
          <CardDescription>
            Academic papers published by this supervisor, sourced from Semantic Scholar.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingPapers && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground py-4">
              <Loader2 className="h-4 w-4 animate-spin" />
              Fetching publications from Semantic Scholar…
            </div>
          )}

          {!loadingPapers && papers && papers.papers.length === 0 && (
            <p className="text-sm text-muted-foreground italic">
              No publications found in Semantic Scholar for this supervisor.
              The research topic chart below is based on their stated research interests.
            </p>
          )}

          {!loadingPapers && papers && papers.papers.length > 0 && (
            <div className="grid gap-2 md:grid-cols-2">
              {papers.papers.map((paper, i) => (
                <div
                  key={paper.paper_id || i}
                  className="rounded-md border bg-muted/30 p-3 space-y-1.5 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start gap-2">
                    <div className="flex-1 min-w-0">
                      {paper.url ? (
                        <a
                          href={paper.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-medium text-primary hover:underline line-clamp-2 leading-snug"
                        >
                          {paper.title}
                          <ExternalLink className="inline ml-1 h-3 w-3 opacity-60" />
                        </a>
                      ) : (
                        <p className="text-sm font-medium line-clamp-2 leading-snug">{paper.title}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    {paper.year && (
                      <Badge variant="outline" className="text-[10px] font-mono">{paper.year}</Badge>
                    )}
                    {paper.venue && (
                      <span className="text-[10px] text-muted-foreground truncate max-w-[200px]">
                        {paper.venue}
                      </span>
                    )}
                    {paper.doi && (
                      <span className="text-[10px] text-muted-foreground font-mono">
                        DOI:{paper.doi.slice(0, 20)}…
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Analytics dashboard */}
      {!loadingPapers && papers && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart2 className="h-4 w-4 text-indigo-500" />
              Research Analytics Dashboard
            </CardTitle>
            <CardDescription>
              Visual overview of publication trends and research domain distribution.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-8 md:grid-cols-2">

            {/* Bar chart — publications by year */}
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                Publications by Year
              </h4>
              {yearData.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={yearData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                    <XAxis
                      dataKey="year"
                      tick={{ fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      allowDecimals={false}
                      tick={{ fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                      formatter={(val) => [`${val} paper${Number(val) !== 1 ? "s" : ""}`, "Publications"]}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {yearData.map((_, idx) => (
                        <Cell
                          key={idx}
                          fill={CHART_COLORS[idx % CHART_COLORS.length]}
                          fillOpacity={0.85}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[220px] flex items-center justify-center text-sm text-muted-foreground italic rounded-md border border-dashed">
                  Year data not available
                </div>
              )}
            </div>

            {/* Pie chart — research topics */}
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
                Research Topic Distribution
              </h4>
              {topicData.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={topicData}
                      cx="50%"
                      cy="45%"
                      outerRadius={75}
                      dataKey="value"
                      stroke="none"
                    >
                      {topicData.map((_, idx) => (
                        <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                      formatter={(_, name) => [String(name), ""]}
                    />
                    <Legend
                      iconType="circle"
                      iconSize={8}
                      formatter={(value) => (
                        <span style={{ fontSize: "10px", color: "hsl(var(--muted-foreground))" }}>
                          {value.length > 22 ? `${value.slice(0, 22)}…` : value}
                        </span>
                      )}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[220px] flex items-center justify-center text-sm text-muted-foreground italic rounded-md border border-dashed">
                  Topic data not available
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────

export default function SupervisorMatchingPage() {
  const [interests, setInterests] = useState("");
  const [abstract, setAbstract] = useState("");
  const [matches, setMatches] = useState<SupervisorMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [selectedMatch, setSelectedMatch] = useState<SupervisorMatch | null>(null);
  const [papers, setPapers] = useState<SupervisorPapersResponse | null>(null);
  const [loadingPapers, setLoadingPapers] = useState(false);

  const handleMatch = async () => {
    if (!interests.trim() && !abstract.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<{ matches: SupervisorMatch[] }>(
        API_ROUTES.module2.matchSupervisors,
        {
          student_id: "current",
          research_interests: interests.split(",").map((s) => s.trim()).filter(Boolean),
          abstract: abstract || undefined,
          top_k: 5,
        },
      );
      setMatches(data.matches);
      setSelectedMatch(null);
      setPapers(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Matching failed");
    } finally {
      setLoading(false);
    }
  };

  const handleViewProfile = async (match: SupervisorMatch) => {
    setSelectedMatch(match);
    setLoadingPapers(true);
    setPapers(null);
    try {
      const data = await apiGet<SupervisorPapersResponse>(
        API_ROUTES.module2.supervisorPapers(match.supervisor_id),
      );
      setPapers(data);
    } catch {
      // Show detail view even if papers fetch fails
    } finally {
      setLoadingPapers(false);
    }
  };

  const handleBack = () => {
    setSelectedMatch(null);
    setPapers(null);
  };

  if (selectedMatch) {
    return (
      <SupervisorDetailView
        match={selectedMatch}
        papers={papers}
        loadingPapers={loadingPapers}
        onBack={handleBack}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="rounded-2xl bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 p-6 text-white shadow-lg">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Users className="h-7 w-7" /> Supervisor Matching
        </h1>
        <p className="mt-1 text-sm text-white/85 max-w-2xl">
          Find the best-fit supervisors based on your research interests using AI-powered
          semantic matching. Click a result to view their full profile, publications, and analytics.
        </p>
      </div>

      {/* Search form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Search className="h-4 w-4" /> Your Research Profile
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="interests">Research interests (comma-separated)</Label>
            <Input
              id="interests"
              placeholder="e.g., Machine Learning, NLP, Computer Vision"
              value={interests}
              onChange={(e) => setInterests(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleMatch()}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="abstract">Research abstract (optional)</Label>
            <textarea
              id="abstract"
              className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Describe your research focus in more detail…"
              value={abstract}
              onChange={(e) => setAbstract(e.target.value)}
            />
          </div>
          <Button onClick={handleMatch} disabled={loading || (!interests.trim() && !abstract.trim())}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Finding supervisors…
              </>
            ) : (
              "Find Supervisors"
            )}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {/* Match results */}
      {matches.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">
            Top Matches
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              — click a supervisor to view full profile &amp; publications
            </span>
          </h2>
          {matches.map((m, i) => (
            <Card
              key={m.supervisor_id}
              className="hover:shadow-md transition-shadow cursor-pointer group"
              onClick={() => handleViewProfile(m)}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  {/* Rank badge */}
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
                    {i + 1}
                  </div>

                  <div className="flex-1 min-w-0 space-y-2">
                    {/* Name + badges */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-base">{m.name}</h3>
                      <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-[10px]">
                        SLIIT
                      </Badge>
                      {!m.availability && (
                        <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200 text-[10px]">
                          Not accepting
                        </Badge>
                      )}
                    </div>

                    {/* Department */}
                    <p className="text-xs text-muted-foreground">
                      {m.department}{m.research_cluster ? ` · ${m.research_cluster}` : ""}
                    </p>

                    {/* Explanation */}
                    <p className="text-sm text-muted-foreground leading-relaxed line-clamp-2">
                      {m.explanation}
                    </p>

                    {/* Match score bar */}
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">Match score</span>
                        <span className="font-semibold text-primary">
                          {(m.multi_factor_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <ScoreBar value={m.multi_factor_score} />
                    </div>

                    {/* Research interests */}
                    {m.research_interests.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {m.research_interests.slice(0, 5).map((ri) => (
                          <span
                            key={ri}
                            className="rounded-full bg-primary/10 px-2.5 py-0.5 text-[10px] font-medium text-primary"
                          >
                            {ri}
                          </span>
                        ))}
                        {m.research_interests.length > 5 && (
                          <span className="text-[10px] text-muted-foreground self-center">
                            +{m.research_interests.length - 5} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Right: CTA */}
                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <div className="text-right">
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Similarity</p>
                      <p className="text-sm font-semibold">{(m.similarity_score * 100).toFixed(1)}%</p>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-primary font-medium group-hover:gap-2 transition-all">
                      View profile <ChevronRight className="h-3.5 w-3.5" />
                    </div>
                    <a
                      href={`mailto:${m.email}?subject=${encodeURIComponent("Research Supervision Enquiry")}`}
                      onClick={(e) => e.stopPropagation()}
                      className="rounded-md border p-1.5 hover:bg-accent transition-colors"
                      title={`Email ${m.name}`}
                    >
                      <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                    </a>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

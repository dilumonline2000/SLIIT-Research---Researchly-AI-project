"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BookOpen, Users, Database, LineChart,
  ArrowUpRight, ArrowRight, AlertTriangle, TrendingUp, Sparkles,
  GraduationCap, Cpu, Target, Layers, FileText, MessageSquare,
  UploadCloud, Search, Lightbulb, CheckCircle2,
} from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MODULES, API_ROUTES } from "@/lib/constants";
import { apiGet } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { useAIProviderStore } from "@/stores/aiProviderStore";
import { MODEL_LABELS } from "@/components/shared/ModelStatusGrid";
import type { UploadedPaper } from "@/stores/paperStore";

const moduleIcons = { 1: BookOpen, 2: Users, 3: Database, 4: LineChart } as const;
const moduleHrefs = {
  1: "/citations",
  2: "/collaboration",
  3: "/data-management",
  4: "/analytics",
} as const;
const moduleGradients: Record<number, string> = {
  1: "from-blue-500 to-cyan-500",
  2: "from-emerald-500 to-teal-500",
  3: "from-amber-500 to-orange-500",
  4: "from-purple-500 to-fuchsia-500",
};

// Platform-wide figures — kept in sync with the public landing page
const PLATFORM_STATS = [
  {
    label: "Research papers trained",
    value: 3860,
    suffix: "+",
    hint: "SLIIT papers powering every AI model",
    icon: GraduationCap,
    gradient: "from-indigo-500 to-blue-500",
  },
  {
    label: "Faculty supervisors",
    value: 84,
    suffix: "",
    hint: "indexed for SBERT expertise matching",
    icon: Users,
    gradient: "from-emerald-500 to-teal-500",
  },
  {
    label: "Prediction accuracy",
    value: 98,
    suffix: "%",
    hint: "XGBoost research success predictor",
    icon: Target,
    gradient: "from-rose-500 to-orange-500",
  },
  {
    label: "Research domains",
    value: 7,
    suffix: "",
    hint: "covered by ARIMA trend forecasting",
    icon: Layers,
    gradient: "from-violet-500 to-fuchsia-500",
  },
];

interface DashboardData {
  total_proposals: number;
  avg_quality_score: number;
  top_trending_topics: string[];
  at_risk_projects: number;
  active_supervisors: number;
}

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.06, duration: 0.5, ease: [0.22, 1, 0.36, 1] as const },
  }),
};

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

function Skeleton({ className = "" }: { className?: string }) {
  return <span className={`inline-block animate-pulse rounded-md bg-muted ${className}`} />;
}

export default function DashboardPage() {
  const { profile } = useAuth();
  const { modelStatuses, isChecking } = useAIProviderStore();

  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [papers, setPapers] = useState<UploadedPaper[] | null>(null);
  const [sessionCount, setSessionCount] = useState<number | null>(null);
  const [hello, setHello] = useState("Welcome back");

  useEffect(() => {
    setHello(greeting());

    apiGet<DashboardData>(API_ROUTES.module4.dashboard)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));

    apiGet<{ papers: UploadedPaper[] }>(API_ROUTES.papers.list)
      .then((r) => setPapers(r.papers || []))
      .catch(() => setPapers([]));

    apiGet<{ sessions: unknown[]; count?: number }>(API_ROUTES.chat.sessions)
      .then((r) => setSessionCount(r.count ?? r.sessions?.length ?? 0))
      .catch(() => setSessionCount(0));
  }, []);

  const totalModels = Object.keys(MODEL_LABELS).length;
  const readyModels = Object.entries(modelStatuses).filter(
    ([k, s]) => k in MODEL_LABELS && s?.loaded,
  ).length;
  const readyPapers = papers?.filter((p) => p.processing_status === "ready").length ?? 0;
  const firstName = (profile?.full_name || "Researcher").split(" ")[0];

  // Personal workspace stats — always meaningful, even on a brand-new account
  const workspace = useMemo(
    () => [
      {
        label: "My papers",
        value: papers === null ? null : String(papers.length),
        hint:
          papers === null
            ? "loading your library…"
            : papers.length === 0
              ? "Upload your first PDF to get started"
              : `${readyPapers} ready for AI chat & analysis`,
        icon: FileText,
        href: papers?.length ? "/papers" : "/papers/upload",
        tone: "text-indigo-500 bg-indigo-500/10",
      },
      {
        label: "Chat sessions",
        value: sessionCount === null ? null : String(sessionCount),
        hint: sessionCount ? "conversations with your papers" : "Ask your first research question",
        icon: MessageSquare,
        href: sessionCount ? "/chat/history" : "/chat",
        tone: "text-sky-500 bg-sky-500/10",
      },
      {
        label: "AI models online",
        value: isChecking && readyModels === 0 ? null : `${readyModels}/${totalModels}`,
        hint: readyModels > 0 ? "local models trained & ready" : "using Gemini until models load",
        icon: Cpu,
        href: "/settings",
        tone: "text-emerald-500 bg-emerald-500/10",
        progress: totalModels ? readyModels / totalModels : 0,
      },
      {
        label: "Proposals",
        value: loading ? null : String(data?.total_proposals ?? 0),
        hint: data?.total_proposals
          ? `avg quality ${(data.avg_quality_score * 100).toFixed(0)}%`
          : "Draft one with the Proposal Generator",
        icon: Lightbulb,
        href: "/citations/proposal",
        tone: "text-amber-500 bg-amber-500/10",
      },
    ],
    [papers, readyPapers, sessionCount, isChecking, readyModels, totalModels, loading, data],
  );

  const quickActions = [
    { label: "Upload a paper", desc: "Add a PDF to your library", href: "/papers/upload", icon: UploadCloud, gradient: "from-indigo-500 to-violet-500" },
    { label: "Find a supervisor", desc: "AI-matched by expertise", href: "/collaboration/supervisor-match", icon: Users, gradient: "from-emerald-500 to-teal-500" },
    { label: "Spot research gaps", desc: "Discover what's missing", href: "/citations/gaps", icon: Search, gradient: "from-blue-500 to-cyan-500" },
    { label: "Forecast trends", desc: "See where fields are heading", href: "/analytics/trends", icon: TrendingUp, gradient: "from-purple-500 to-fuchsia-500" },
  ];

  return (
    <div className="space-y-6 pb-8 sm:space-y-8">

      {/* ── Welcome hero ───────────────────────────────────────────── */}
      <motion.section
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative overflow-hidden rounded-2xl border bg-gradient-to-br from-indigo-600 via-violet-600 to-fuchsia-600 p-5 text-white shadow-glow sm:p-8"
      >
        <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-white/10 blur-2xl" />
        <div className="pointer-events-none absolute -bottom-24 left-1/3 h-56 w-56 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-medium backdrop-blur-sm">
              <Sparkles className="h-3.5 w-3.5" /> R26-IT-116 · SLIIT
            </span>
            <h1 className="mt-3 text-2xl font-bold leading-tight sm:text-3xl lg:text-4xl">
              {hello}, {firstName} 👋
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-white/85 sm:text-base">
              Your AI research companion is ready. Explore papers, find the right mentor,
              and turn ideas into high-impact research — powered by models trained on
              3,860+ SLIIT research papers.
            </p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row lg:shrink-0">
            <Link
              href="/chat"
              className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-white px-5 text-sm font-semibold text-indigo-700 shadow-lg transition hover:bg-white/90"
            >
              <MessageSquare className="h-4 w-4" /> Start research chat
            </Link>
            <Link
              href="/papers/upload"
              className="inline-flex h-11 items-center justify-center gap-2 rounded-xl border border-white/30 bg-white/10 px-5 text-sm font-semibold text-white backdrop-blur-sm transition hover:bg-white/20"
            >
              <UploadCloud className="h-4 w-4" /> Upload paper
            </Link>
          </div>
        </div>
      </motion.section>

      {/* ── Platform knowledge base ───────────────────────────────── */}
      <section>
        <div className="mb-3 flex items-end justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold sm:text-xl">Platform knowledge base</h2>
            <p className="text-sm text-muted-foreground">What the Researchly AI engine has learned so far</p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
          {PLATFORM_STATS.map((s, i) => (
            <motion.div key={s.label} custom={i} initial="hidden" animate="visible" variants={fadeUp}>
              <Card className="group relative h-full overflow-hidden p-4 hover:shadow-lg sm:p-5">
                <div className={`absolute -right-6 -top-6 h-20 w-20 rounded-full bg-gradient-to-br ${s.gradient} opacity-10 transition-opacity group-hover:opacity-20`} />
                <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br ${s.gradient} text-white shadow-md`}>
                  <s.icon className="h-5 w-5" />
                </div>
                <p className="mt-3 font-display text-2xl font-bold tabular-nums sm:text-3xl">
                  {s.value.toLocaleString()}
                  <span className="text-gradient-brand">{s.suffix}</span>
                </p>
                <p className="mt-0.5 text-sm font-semibold">{s.label}</p>
                <p className="mt-1 text-xs leading-snug text-muted-foreground">{s.hint}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── My workspace ───────────────────────────────────────────── */}
      <section>
        <div className="mb-3">
          <h2 className="text-lg font-semibold sm:text-xl">My workspace</h2>
          <p className="text-sm text-muted-foreground">Your personal progress across Researchly AI</p>
        </div>
        <div className="grid grid-cols-1 gap-3 min-[480px]:grid-cols-2 sm:gap-4 xl:grid-cols-4">
          {workspace.map((w, i) => (
            <motion.div key={w.label} custom={i + 4} initial="hidden" animate="visible" variants={fadeUp}>
              <Link href={w.href} className="block h-full">
                <Card className="group flex h-full items-start gap-4 p-4 transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-lg sm:p-5">
                  <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${w.tone}`}>
                    <w.icon className="h-5 w-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{w.label}</p>
                      <ArrowUpRight className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
                    </div>
                    <p className="mt-1 font-display text-2xl font-bold tabular-nums">
                      {w.value === null ? <Skeleton className="h-7 w-14" /> : w.value}
                    </p>
                    {"progress" in w && typeof w.progress === "number" && (
                      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all"
                          style={{ width: `${Math.round(w.progress * 100)}%` }}
                        />
                      </div>
                    )}
                    <p className="mt-1.5 text-xs leading-snug text-muted-foreground">{w.hint}</p>
                  </div>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Research health + quick actions ───────────────────────── */}
      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              <CardTitle className="text-base">Research health</CardTitle>
            </div>
            <CardDescription>Live signals from the Insight Studio analytics engine</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              {
                label: "Average quality score",
                value: loading ? null : data?.total_proposals ? `${(data.avg_quality_score * 100).toFixed(0)}%` : "Not scored yet",
                icon: CheckCircle2,
                tone: "text-emerald-500",
              },
              {
                label: "Projects needing attention",
                value: loading ? null : data ? (data.at_risk_projects > 0 ? String(data.at_risk_projects) : "All on track") : "—",
                icon: AlertTriangle,
                tone: data?.at_risk_projects ? "text-rose-500" : "text-emerald-500",
              },
              {
                label: "Supervisors matched",
                value: loading ? null : data?.active_supervisors ? String(data.active_supervisors) : "84 available",
                icon: Users,
                tone: "text-violet-500",
              },
            ].map((row) => (
              <div key={row.label} className="flex items-center justify-between gap-3 rounded-xl border bg-muted/40 px-3.5 py-3">
                <span className="flex min-w-0 items-center gap-2.5 text-sm">
                  <row.icon className={`h-4 w-4 shrink-0 ${row.tone}`} />
                  <span className="truncate">{row.label}</span>
                </span>
                <span className="shrink-0 text-sm font-semibold tabular-nums">
                  {row.value === null ? <Skeleton className="h-5 w-12" /> : row.value}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <CardTitle className="text-base">Quick start</CardTitle>
            </div>
            <CardDescription>Jump straight into the most popular research tools</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {quickActions.map((a) => (
              <Link
                key={a.href}
                href={a.href}
                className="group flex items-center gap-3 rounded-xl border p-3 transition-all hover:border-primary/30 hover:bg-accent/50"
              >
                <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br ${a.gradient} text-white shadow-sm`}>
                  <a.icon className="h-5 w-5" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-semibold">{a.label}</span>
                  <span className="block truncate text-xs text-muted-foreground">{a.desc}</span>
                </span>
                <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
              </Link>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* ── Trending topics ─────────────────────────────────────────── */}
      {data?.top_trending_topics && data.top_trending_topics.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35, duration: 0.5 }}
        >
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-primary" />
                <CardTitle className="text-base">Trending Research Topics</CardTitle>
              </div>
              <CardDescription>Most active research areas across the SLIIT corpus</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {data.top_trending_topics.map((topic, i) => (
                  <motion.span
                    key={topic}
                    initial={{ opacity: 0, scale: 0.85 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.4 + i * 0.05 }}
                    className="rounded-full border border-primary/15 bg-primary/10 px-3 py-1 text-sm font-medium text-primary"
                  >
                    {topic}
                  </motion.span>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ── Learning spaces (modules) ───────────────────────────────── */}
      <section>
        <div className="mb-3">
          <h2 className="text-lg font-semibold sm:text-xl">Explore learning spaces</h2>
          <p className="text-sm text-muted-foreground">Four AI-powered studios built for every stage of your research</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {MODULES.map((mod, i) => {
            const Icon = moduleIcons[mod.id as keyof typeof moduleIcons];
            const href = moduleHrefs[mod.id as keyof typeof moduleHrefs];
            const gradient = moduleGradients[mod.id];
            return (
              <motion.div
                key={mod.id}
                custom={i}
                initial="hidden"
                animate="visible"
                variants={fadeUp}
                whileHover={{ y: -3 }}
                transition={{ type: "spring", stiffness: 300, damping: 25 }}
              >
                <Link href={href} className="block h-full">
                  <Card className="group relative h-full cursor-pointer overflow-hidden border transition-all duration-200 hover:border-primary/30 hover:shadow-lg">
                    <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${gradient}`} />
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${gradient} text-white shadow-md`}>
                          <Icon className="h-5 w-5" />
                        </div>
                        <div className="flex h-9 w-9 items-center justify-center rounded-full border bg-muted/50 transition-colors group-hover:border-primary/20 group-hover:bg-primary/5">
                          <ArrowUpRight className="h-4 w-4 text-muted-foreground transition-colors group-hover:text-primary" />
                        </div>
                      </div>
                      <p className={`pt-3 text-xs font-semibold uppercase tracking-wider bg-gradient-to-r ${gradient} bg-clip-text text-transparent`}>
                        {mod.space}
                      </p>
                      <CardTitle className="text-lg font-semibold">{mod.name}</CardTitle>
                      <CardDescription className="text-sm leading-relaxed">{mod.tagline} — {mod.description.toLowerCase()}.</CardDescription>
                      <div className="pt-2">
                        <span className="text-xs text-muted-foreground">
                          By <span className="font-medium text-foreground/80">{mod.owner}</span>
                        </span>
                      </div>
                    </CardHeader>
                  </Card>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

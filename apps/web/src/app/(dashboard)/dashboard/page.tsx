"use client";

import { useEffect, useState } from "react";
import {
  BookOpen, Users, Database, LineChart,
  ArrowUpRight, AlertTriangle, TrendingUp, Sparkles,
} from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MODULES, API_ROUTES } from "@/lib/constants";
import { apiGet } from "@/lib/api";

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
  4: "from-purple-500 to-violet-500",
};
const statColors = [
  { bg: "bg-blue-50 dark:bg-blue-950/30", icon: "text-blue-500", border: "border-blue-100 dark:border-blue-900/50" },
  { bg: "bg-emerald-50 dark:bg-emerald-950/30", icon: "text-emerald-500", border: "border-emerald-100 dark:border-emerald-900/50" },
  { bg: "bg-rose-50 dark:bg-rose-950/30", icon: "text-rose-500", border: "border-rose-100 dark:border-rose-900/50" },
  { bg: "bg-purple-50 dark:bg-purple-950/30", icon: "text-purple-500", border: "border-purple-100 dark:border-purple-900/50" },
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
    transition: { delay: i * 0.08, duration: 0.5, ease: [0.22, 1, 0.36, 1] as const },
  }),
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiGet<DashboardData>(API_ROUTES.module4.dashboard)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  const stats = [
    {
      label: "Proposals",
      value: data?.total_proposals ?? "—",
      hint: "total research proposals",
      icon: BookOpen,
      delta: null,
    },
    {
      label: "Avg Quality",
      value: data ? `${(data.avg_quality_score * 100).toFixed(0)}%` : "—",
      hint: "average quality score",
      icon: TrendingUp,
      delta: null,
    },
    {
      label: "At Risk",
      value: data?.at_risk_projects ?? "—",
      hint: "projects needing attention",
      icon: AlertTriangle,
      delta: null,
    },
    {
      label: "Supervisors",
      value: data?.active_supervisors ?? "—",
      hint: "actively matched",
      icon: Users,
      delta: null,
    },
  ];

  return (
    <div className="space-y-8 pb-8">

      {/* ── Header ─────────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex items-start justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Welcome to Researchly AI — your research workflow starts here.
          </p>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 rounded-full border bg-card px-3 py-1.5 text-xs text-muted-foreground">
          <Sparkles className="h-3.5 w-3.5 text-primary" />
          R26-IT-116 · SLIIT
        </div>
      </motion.div>

      {/* ── Stat cards ─────────────────────────────────────────────── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s, i) => {
          const color = statColors[i];
          return (
            <motion.div
              key={s.label}
              custom={i}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
            >
              <Card className={`border ${color.border} ${color.bg} shadow-sm hover:shadow-md transition-shadow`}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardDescription className="text-xs font-medium uppercase tracking-wide">
                      {s.label}
                    </CardDescription>
                    <div className={`flex h-8 w-8 items-center justify-center rounded-lg bg-white dark:bg-background/50 shadow-sm`}>
                      <s.icon className={`h-4 w-4 ${color.icon}`} />
                    </div>
                  </div>
                  <CardTitle className="text-3xl font-bold tabular-nums">
                    {loading ? (
                      <span className="inline-block h-8 w-16 animate-pulse rounded-md bg-muted" />
                    ) : (
                      s.value
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground">{s.hint}</p>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
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
                    className="rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary border border-primary/15"
                  >
                    {topic}
                  </motion.span>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ── Module cards ────────────────────────────────────────────── */}
      <div>
        <motion.h2
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mb-4 text-lg font-semibold"
        >
          Modules
        </motion.h2>
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
                whileHover={{ y: -3, scale: 1.01 }}
                transition={{ type: "spring", stiffness: 300, damping: 25 }}
              >
                <Link href={href} className="block h-full">
                  <Card className="h-full group cursor-pointer border hover:border-primary/20 hover:shadow-lg transition-all duration-200">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div
                          className={`flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br ${gradient} text-white shadow-md`}
                        >
                          <Icon className="h-5 w-5" />
                        </div>
                        <div className="flex h-8 w-8 items-center justify-center rounded-full border bg-muted/50 group-hover:border-primary/20 group-hover:bg-primary/5 transition-colors">
                          <ArrowUpRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                        </div>
                      </div>
                      <CardTitle className="pt-3 text-base font-semibold">{mod.name}</CardTitle>
                      <CardDescription className="text-sm leading-relaxed">{mod.description}</CardDescription>
                      <div className="pt-2">
                        <span className="text-xs text-muted-foreground">
                          By <span className="font-medium text-foreground/70">{mod.owner}</span>
                        </span>
                      </div>
                    </CardHeader>
                  </Card>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

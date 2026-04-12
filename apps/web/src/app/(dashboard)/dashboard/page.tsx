"use client";

import { useEffect, useState } from "react";
import { BookOpen, Users, Database, LineChart, ArrowUpRight, AlertTriangle, TrendingUp } from "lucide-react";
import Link from "next/link";
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

interface DashboardData {
  total_proposals: number;
  avg_quality_score: number;
  top_trending_topics: string[];
  at_risk_projects: number;
  active_supervisors: number;
}

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
    { label: "Proposals", value: data?.total_proposals ?? "—", hint: "total research proposals", icon: BookOpen },
    { label: "Avg Quality", value: data ? `${(data.avg_quality_score * 100).toFixed(0)}%` : "—", hint: "average quality score", icon: TrendingUp },
    { label: "At Risk", value: data?.at_risk_projects ?? "—", hint: "projects needing attention", icon: AlertTriangle },
    { label: "Supervisors", value: data?.active_supervisors ?? "—", hint: "actively matched", icon: Users },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome to Researchly AI — your research workflow starts here.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <Card key={s.label}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription>{s.label}</CardDescription>
                <s.icon className="h-4 w-4 text-muted-foreground" />
              </div>
              <CardTitle className="text-3xl">
                {loading ? <span className="animate-pulse">...</span> : s.value}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">{s.hint}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {data?.top_trending_topics && data.top_trending_topics.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Trending Topics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {data.top_trending_topics.map((topic) => (
                <span key={topic} className="rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
                  {topic}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div>
        <h2 className="mb-4 text-xl font-semibold">Modules</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {MODULES.map((mod) => {
            const Icon = moduleIcons[mod.id as keyof typeof moduleIcons];
            const href = moduleHrefs[mod.id as keyof typeof moduleHrefs];
            return (
              <Link key={mod.id} href={href}>
                <Card className="h-full transition-all hover:shadow-md hover:-translate-y-0.5">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${mod.color} text-white`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <CardTitle className="pt-3 text-lg">{mod.name}</CardTitle>
                    <CardDescription>{mod.description}</CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

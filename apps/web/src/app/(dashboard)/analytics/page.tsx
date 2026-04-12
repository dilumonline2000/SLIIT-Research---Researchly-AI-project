"use client";

import Link from "next/link";
import { TrendingUp, BarChart3, Network, Target, ArrowRight } from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  { title: "Trend Forecasting", desc: "ARIMA + Prophet ensemble forecasts for research topic popularity.", icon: TrendingUp, href: "/analytics/trends", color: "bg-purple-500" },
  { title: "Quality Scores", desc: "Multi-dimensional quality scoring: originality, citation impact, methodology, clarity.", icon: BarChart3, href: "/analytics/quality-scores", color: "bg-fuchsia-500" },
  { title: "Dashboards", desc: "Real-time D3.js dashboards aggregating proposals, quality, trending topics and at-risk projects.", icon: BarChart3, href: "/analytics/dashboards", color: "bg-violet-500" },
  { title: "Concept Mind Maps", desc: "GNN-based concept expansion and research idea mind-map generation.", icon: Network, href: "/analytics/mind-maps", color: "bg-indigo-500" },
  { title: "Success Prediction", desc: "ML-powered prediction of research project outcomes with actionable recommendations.", icon: Target, href: "/analytics/predictions", color: "bg-pink-500" },
];

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Research Performance Analytics</h1>
        <p className="text-muted-foreground">Module 4 · Owner: H W S S Jayasundara</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {features.map((f) => (
          <Link key={f.title} href={f.href}>
            <Card className="h-full transition-all hover:shadow-md hover:-translate-y-0.5 cursor-pointer">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${f.color} text-white`}>
                    <f.icon className="h-5 w-5" />
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
                <CardTitle className="pt-3 text-lg">{f.title}</CardTitle>
                <CardDescription>{f.desc}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

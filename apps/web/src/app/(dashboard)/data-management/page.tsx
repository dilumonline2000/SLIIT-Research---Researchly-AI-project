"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Database, Tag, FileText, BarChart3, Workflow, ShieldAlert, ArrowRight } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { API_ROUTES } from "@/lib/constants";
import { apiGet } from "@/lib/api";

interface QualityData {
  total_papers: number;
  completeness_score: number;
  consistency_score: number;
  duplicate_rate: number;
  sources: Record<string, number>;
}

const features = [
  { title: "Data Pipeline", desc: "Orchestrate scraping from IEEE, arXiv, ACM, SLIIT, Scholar and Semantic Scholar sources.", icon: Workflow, href: "/data-management/pipeline", color: "bg-amber-600" },
  { title: "Topic Categorization", desc: "Classify papers into research categories using SciBERT.", icon: Tag, href: "/data-management/categorization", color: "bg-amber-500" },
  { title: "Plagiarism Trends", desc: "Analyze plagiarism patterns and trends across the paper corpus.", icon: ShieldAlert, href: "/data-management/plagiarism-trends", color: "bg-red-500" },
  { title: "Summarizer", desc: "Generate abstractive summaries of research papers.", icon: FileText, href: "/data-management/summarizer", color: "bg-orange-500" },
];

export default function DataManagementPage() {
  const [quality, setQuality] = useState<QualityData | null>(null);

  useEffect(() => {
    apiGet<QualityData>(API_ROUTES.module3.quality)
      .then(setQuality)
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Research Data Collection & Management</h1>
        <p className="text-muted-foreground">Module 3 · Owner: N V Hewamanne</p>
      </div>

      {quality && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="pb-2"><CardDescription>Total Papers</CardDescription><CardTitle className="text-2xl">{quality.total_papers.toLocaleString()}</CardTitle></CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardDescription>Completeness</CardDescription><CardTitle className="text-2xl">{(quality.completeness_score * 100).toFixed(0)}%</CardTitle></CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardDescription>Consistency</CardDescription><CardTitle className="text-2xl">{(quality.consistency_score * 100).toFixed(0)}%</CardTitle></CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardDescription>Duplicate Rate</CardDescription><CardTitle className="text-2xl">{(quality.duplicate_rate * 100).toFixed(1)}%</CardTitle></CardHeader>
          </Card>
        </div>
      )}

      {quality && Object.keys(quality.sources).length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-lg">Papers by Source</CardTitle></CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              {Object.entries(quality.sources).sort((a, b) => b[1] - a[1]).map(([src, count]) => (
                <div key={src} className="rounded bg-secondary px-3 py-1 text-sm">
                  <span className="font-medium">{src}</span>: {count.toLocaleString()}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

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

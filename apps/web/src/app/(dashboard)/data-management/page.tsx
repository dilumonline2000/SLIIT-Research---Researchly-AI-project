"use client";

import { useEffect, useState } from "react";
import { Tag, FileText, Workflow, ShieldAlert, Archive, Globe } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FeatureHub, type HubFeature } from "@/components/shared/FeatureHub";
import { API_ROUTES } from "@/lib/constants";
import { apiGet } from "@/lib/api";

interface QualityData {
  total_papers: number;
  completeness_score: number;
  consistency_score: number;
  duplicate_rate: number;
  sources: Record<string, number>;
}

const features: HubFeature[] = [
  { title: "Data Pipeline", desc: "Orchestrate scraping from IEEE, arXiv, ACM, SLIIT, Scholar and Semantic Scholar sources.", icon: Workflow, href: "/data-management/pipeline", gradient: "from-amber-500 to-yellow-500" },
  { title: "Topic Categorization", desc: "Classify papers into research categories using SciBERT.", icon: Tag, href: "/data-management/categorization", gradient: "from-amber-500 to-orange-500" },
  { title: "Plagiarism Trends", desc: "Analyze plagiarism patterns and trends across the paper corpus.", icon: ShieldAlert, href: "/data-management/plagiarism-trends", gradient: "from-rose-500 to-red-500" },
  { title: "Summarizer", desc: "Generate abstractive summaries of research papers.", icon: FileText, href: "/data-management/summarizer", gradient: "from-orange-500 to-rose-500" },
];

export default function DataManagementPage() {
  const [quality, setQuality] = useState<QualityData | null>(null);

  useEffect(() => {
    apiGet<QualityData>(API_ROUTES.module3.quality)
      .then(setQuality)
      .catch(() => {});
  }, []);

  const sources = quality ? Object.entries(quality.sources).sort((a, b) => b[1] - a[1]) : [];
  const maxSource = Math.max(1, ...sources.map(([, c]) => c));

  return (
    <FeatureHub
      theme="vault"
      icon={Archive}
      title="Research Data Collection & Management"
      tagline="Collect, clean, classify and summarise research papers — the knowledge base that powers every Researchly AI model."
      owner="N V Hewamanne"
      features={features}
      stats={
        quality
          ? [
              { label: "Total papers", value: quality.total_papers.toLocaleString() },
              { label: "Completeness", value: `${(quality.completeness_score * 100).toFixed(0)}%` },
              { label: "Consistency", value: `${(quality.consistency_score * 100).toFixed(0)}%` },
              { label: "Duplicate rate", value: `${(quality.duplicate_rate * 100).toFixed(1)}%` },
            ]
          : undefined
      }
    >
      {sources.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Globe className="h-4 w-4 text-amber-500" /> Papers by Source
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
            {sources.map(([src, count]) => (
              <div key={src} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{src}</span>
                  <span className="tabular-nums text-muted-foreground">{count.toLocaleString()}</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-amber-500 to-orange-500"
                    style={{ width: `${(count / maxSource) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </FeatureHub>
  );
}

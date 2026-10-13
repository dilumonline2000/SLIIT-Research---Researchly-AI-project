"use client";

import { TrendingUp, BarChart3, Network, Target, FileUp, Telescope } from "lucide-react";
import { FeatureHub, type HubFeature } from "@/components/shared/FeatureHub";

const features: HubFeature[] = [
  { title: "Paper Quality Scoring", desc: "Upload a paper (PDF/text) — get scores for originality, citation impact, methodology, clarity + topic classification.", icon: FileUp, href: "/analytics/quality-scores", gradient: "from-fuchsia-500 to-pink-500", badge: "TRAINED" },
  { title: "Success Prediction", desc: "Predict if a paper/proposal will be successful (publishable, methodologically sound). 98% accuracy on SLIIT data.", icon: Target, href: "/analytics/predictions", gradient: "from-pink-500 to-rose-500", badge: "TRAINED" },
  { title: "Trend Forecasting", desc: "ARIMA forecasts on 4,219 SLIIT papers — predict publication trends for 6 research domains.", icon: TrendingUp, href: "/analytics/trends", gradient: "from-purple-500 to-violet-500", badge: "TRAINED" },
  { title: "Dashboards", desc: "Real-time D3.js dashboards aggregating proposals, quality, trending topics and at-risk projects.", icon: BarChart3, href: "/analytics/dashboards", gradient: "from-violet-500 to-indigo-500" },
  { title: "Concept Mind Maps", desc: "GNN-based concept expansion and research idea mind-map generation.", icon: Network, href: "/analytics/mind-maps", gradient: "from-indigo-500 to-blue-500" },
];

export default function AnalyticsPage() {
  return (
    <FeatureHub
      theme="insight"
      icon={Telescope}
      title="Research Performance Analytics"
      tagline="Score paper quality, predict research success, and forecast where your field is heading."
      owner="H W S S Jayasundara"
      features={features}
      stats={[
        { label: "Prediction accuracy", value: "98%" },
        { label: "Papers analysed", value: "4,219" },
      ]}
    />
  );
}

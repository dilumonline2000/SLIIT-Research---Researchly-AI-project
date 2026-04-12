"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TrendingUp, AlertTriangle, Users, FileText, Gauge } from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiGet } from "@/lib/api";

interface DashboardSnapshot {
  total_proposals: number;
  avg_quality_score: number;
  top_trending_topics: string[];
  at_risk_projects: number;
  active_supervisors: number;
}

export default function DashboardsPage() {
  const [data, setData] = useState<DashboardSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchSnapshot = async () => {
    setLoading(true);
    try {
      const snap = await apiGet<DashboardSnapshot>(API_ROUTES.module4.dashboard);
      setData(snap);
      setLastUpdated(new Date());
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSnapshot();
    const id = setInterval(fetchSnapshot, 30_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">Performance Dashboards</h1>
          <p className="text-muted-foreground">Cross-module KPI aggregation · auto-refresh every 30s.</p>
        </div>
        <div className="flex items-center gap-2">
          {lastUpdated && <span className="text-xs text-muted-foreground">Updated {lastUpdated.toLocaleTimeString()}</span>}
          <Button variant="outline" size="sm" onClick={fetchSnapshot} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
        </div>
      </div>

      {data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardDescription>Total Proposals</CardDescription>
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </div>
                <CardTitle className="text-3xl">{data.total_proposals.toLocaleString()}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardDescription>Avg Quality Score</CardDescription>
                  <Gauge className="h-4 w-4 text-muted-foreground" />
                </div>
                <CardTitle className="text-3xl">{(data.avg_quality_score * 100).toFixed(0)}%</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardDescription>At-Risk Projects</CardDescription>
                  <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                </div>
                <CardTitle className="text-3xl text-destructive">{data.at_risk_projects}</CardTitle>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardDescription>Active Supervisors</CardDescription>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </div>
                <CardTitle className="text-3xl">{data.active_supervisors}</CardTitle>
              </CardHeader>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-4 w-4" /> Top Trending Topics
              </CardTitle>
            </CardHeader>
            <CardContent>
              {data.top_trending_topics.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {data.top_trending_topics.map((topic, i) => (
                    <div key={topic} className="flex items-center gap-2 rounded-full bg-secondary px-3 py-1 text-sm">
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">{i + 1}</span>
                      {topic}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No trending topic data yet.</p>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {!data && !loading && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Failed to load dashboard snapshot. Ensure module4-analytics service is running.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

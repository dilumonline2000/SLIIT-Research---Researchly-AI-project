"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { API_ROUTES } from "@/lib/constants";
import { apiGet } from "@/lib/api";

interface TrendEntry {
  cohort_year: number;
  topic_area: string;
  avg_similarity: number;
  max_similarity: number;
  trend_direction: string;
}

const directionColors: Record<string, string> = {
  increasing: "text-red-600 bg-red-50 dark:bg-red-950",
  decreasing: "text-green-600 bg-green-50 dark:bg-green-950",
  stable: "text-blue-600 bg-blue-50 dark:bg-blue-950",
  baseline: "text-muted-foreground bg-secondary",
};

export default function PlagiarismTrendsPage() {
  const [trends, setTrends] = useState<TrendEntry[]>([]);
  const [yearFrom, setYearFrom] = useState(2020);
  const [yearTo, setYearTo] = useState(2026);
  const [loading, setLoading] = useState(true);

  const fetchTrends = async () => {
    setLoading(true);
    try {
      const data = await apiGet<{ trends: TrendEntry[] }>(
        `${API_ROUTES.module3.plagiarismTrends}?year_from=${yearFrom}&year_to=${yearTo}`,
      );
      setTrends(data.trends);
    } catch {
      setTrends([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTrends(); }, []); // initial load

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Plagiarism Trends</h1>
        <p className="text-muted-foreground">Aggregated plagiarism patterns across student cohorts and topic areas.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Filter</CardTitle></CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-2">
              <Label htmlFor="from">Year From</Label>
              <Input id="from" type="number" value={yearFrom} onChange={(e) => setYearFrom(Number(e.target.value))} className="w-28" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="to">Year To</Label>
              <Input id="to" type="number" value={yearTo} onChange={(e) => setYearTo(Number(e.target.value))} className="w-28" />
            </div>
            <Button onClick={fetchTrends} disabled={loading}>{loading ? "Loading..." : "Apply"}</Button>
          </div>
        </CardContent>
      </Card>

      {!loading && trends.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">No plagiarism trend data available yet. Populate the <code>plagiarism_trends</code> table to see results.</p>
          </CardContent>
        </Card>
      )}

      {trends.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-lg">Trends</CardTitle></CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-4">Year</th>
                    <th className="pb-2 pr-4">Topic</th>
                    <th className="pb-2 pr-4">Avg Similarity</th>
                    <th className="pb-2 pr-4">Max Similarity</th>
                    <th className="pb-2">Direction</th>
                  </tr>
                </thead>
                <tbody>
                  {trends.map((t, i) => (
                    <tr key={`${t.cohort_year}-${t.topic_area}-${i}`} className="border-b border-border/50">
                      <td className="py-1.5 pr-4 font-medium">{t.cohort_year}</td>
                      <td className="py-1.5 pr-4">{t.topic_area}</td>
                      <td className="py-1.5 pr-4">{(t.avg_similarity * 100).toFixed(1)}%</td>
                      <td className="py-1.5 pr-4">{(t.max_similarity * 100).toFixed(1)}%</td>
                      <td className="py-1.5">
                        <span className={`capitalize rounded px-2 py-0.5 text-xs font-medium ${directionColors[t.trend_direction] || ""}`}>
                          {t.trend_direction}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

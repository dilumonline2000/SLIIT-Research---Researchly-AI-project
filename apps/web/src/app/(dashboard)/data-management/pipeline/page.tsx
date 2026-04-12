"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiGet, apiPost } from "@/lib/api";

const SOURCES = ["arxiv", "semantic_scholar", "ieee", "acm", "sliit", "scholar"] as const;
type Source = typeof SOURCES[number];

interface ScrapeResponse { job_id: string; source: string; status: string; }
interface JobStatus { job_id: string; source: string; status: string; papers_collected: number; error?: string | null; }

export default function PipelinePage() {
  const [source, setSource] = useState<Source>("arxiv");
  const [query, setQuery] = useState("");
  const [maxPapers, setMaxPapers] = useState(100);
  const [jobs, setJobs] = useState<JobStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleStart = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await apiPost<ScrapeResponse>(API_ROUTES.module3.scrape, {
        source,
        query: query || undefined,
        max_papers: maxPapers,
      });
      setJobs((prev) => [{ ...res, papers_collected: 0 }, ...prev]);
    } catch (err: any) {
      setError(err.message || "Failed to start scrape job");
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async (jobId: string) => {
    try {
      const status = await apiGet<JobStatus>(API_ROUTES.module3.scrapeStatus(jobId));
      setJobs((prev) => prev.map((j) => (j.job_id === jobId ? status : j)));
    } catch {}
  };

  const statusColor = (s: string) =>
    s === "success" ? "text-green-600" : s === "failed" ? "text-destructive" : s === "running" ? "text-yellow-600" : "text-muted-foreground";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Data Pipeline</h1>
        <p className="text-muted-foreground">Orchestrate research paper scraping from multiple academic sources.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">Start Scrape Job</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Source</Label>
            <div className="flex flex-wrap gap-2">
              {SOURCES.map((s) => (
                <Button key={s} variant={source === s ? "default" : "outline"} size="sm" onClick={() => setSource(s)}>
                  {s}
                </Button>
              ))}
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="query">Query (optional)</Label>
            <Input id="query" placeholder="e.g., transformer architectures" value={query} onChange={(e) => setQuery(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="max">Max Papers</Label>
            <Input id="max" type="number" min={1} max={10000} value={maxPapers} onChange={(e) => setMaxPapers(Number(e.target.value))} />
          </div>
          <Button onClick={handleStart} disabled={loading}>
            {loading ? "Starting..." : "Start Job"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <p className="text-xs text-muted-foreground">Note: arxiv and semantic_scholar are active. Others return a 400 until their scrapers are wired up. Requires admin/coordinator role.</p>
        </CardContent>
      </Card>

      {jobs.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-lg">Jobs</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {jobs.map((job) => (
                <div key={job.job_id} className="flex items-center justify-between rounded border p-3">
                  <div>
                    <p className="text-sm font-medium">{job.source} · <span className="font-mono text-xs">{job.job_id}</span></p>
                    <p className={`text-xs ${statusColor(job.status)}`}>
                      {job.status} · {job.papers_collected} papers
                      {job.error && ` · ${job.error}`}
                    </p>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => handleRefresh(job.job_id)}>Refresh</Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

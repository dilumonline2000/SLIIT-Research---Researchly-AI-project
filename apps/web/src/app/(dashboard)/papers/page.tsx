"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Plus, FileText, CheckCircle2, Loader2, AlertCircle, Search, RefreshCw } from "lucide-react";
import { PaperGrid } from "@/components/papers/PaperGrid";
import { PageHero, heroButtonPrimary, heroButtonGhost, SegmentedTabs } from "@/components/shared/PageHero";
import { Input } from "@/components/ui/input";
import { apiGet } from "@/lib/api";
import { API_ROUTES } from "@/lib/constants";
import { usePaperStore, type UploadedPaper } from "@/stores/paperStore";

type Filter = "all" | "ready" | "processing" | "failed";

export default function PapersLibraryPage() {
  const { papers, setPapers, loading, setLoading } = usePaperStore();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const r = await apiGet<{ papers: UploadedPaper[] }>(API_ROUTES.papers.list);
      setPapers(r.papers || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [setPapers, setLoading]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const counts = useMemo(() => {
    const ready = papers.filter((p) => p.processing_status === "ready").length;
    const failed = papers.filter((p) => p.processing_status === "failed").length;
    return { ready, failed, processing: papers.length - ready - failed };
  }, [papers]);

  const visible = papers.filter((p) => {
    const status =
      p.processing_status === "ready" ? "ready" : p.processing_status === "failed" ? "failed" : "processing";
    if (filter !== "all" && status !== filter) return false;
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return (
      (p.title || "").toLowerCase().includes(q) ||
      (p.authors || []).join(" ").toLowerCase().includes(q) ||
      (p.keywords || []).join(" ").toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6 pb-8">
      <PageHero
        theme="library"
        icon={FileText}
        title="My Papers"
        description="Upload research papers, chat with them, and feed them into model training."
        actions={
          <>
            <Link href="/papers/upload" className={heroButtonPrimary}>
              <Plus className="h-4 w-4" /> Upload PDFs
            </Link>
            <button onClick={refresh} disabled={loading} className={heroButtonGhost}>
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Refresh
            </button>
          </>
        }
        stats={[
          { label: "Total papers", value: papers.length, icon: FileText },
          { label: "Ready for chat", value: counts.ready, icon: CheckCircle2 },
          { label: "Processing", value: counts.processing, icon: Loader2 },
          { label: "Need attention", value: counts.failed, icon: AlertCircle },
        ]}
      />

      {papers.length > 0 && (
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <SegmentedTabs<Filter>
            theme="library"
            value={filter}
            onChange={setFilter}
            tabs={[
              { id: "all", label: `All (${papers.length})` },
              { id: "ready", label: `Ready (${counts.ready})` },
              { id: "processing", label: `Processing (${counts.processing})` },
              { id: "failed", label: `Failed (${counts.failed})` },
            ]}
          />
          <div className="relative w-full lg:max-w-sm">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search by title, author or keyword…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="h-11 rounded-xl bg-card pl-10 shadow-soft"
            />
          </div>
        </div>
      )}

      {loading && papers.length === 0 ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-44 animate-pulse rounded-xl border bg-card" />
          ))}
        </div>
      ) : papers.length > 0 && visible.length === 0 ? (
        <div className="rounded-xl border border-dashed p-10 text-center text-sm text-muted-foreground">
          No papers match your filters.
        </div>
      ) : (
        <PaperGrid papers={visible} />
      )}
    </div>
  );
}

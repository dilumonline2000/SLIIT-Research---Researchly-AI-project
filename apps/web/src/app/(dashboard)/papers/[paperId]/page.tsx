"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { MessageSquare, RefreshCw, Trash2, FileText, ArrowLeft, Tag, ListTree, BarChart3 } from "lucide-react";
import { PageHero, heroButtonPrimary, heroButtonGhost } from "@/components/shared/PageHero";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiGet, apiPost, apiDelete } from "@/lib/api";
import { API_ROUTES } from "@/lib/constants";

interface PaperDetail {
  id: string;
  title: string | null;
  authors: string[] | null;
  abstract: string | null;
  keywords: string[] | null;
  publication_year: number | null;
  doi: string | null;
  page_count: number | null;
  processing_status: string;
  processing_error?: string | null;
  references_list?: { raw: string }[] | null;
  extracted_data?: {
    statistics?: Record<string, number>;
    sections?: { heading: string; content: string }[];
  };
}

export default function PaperDetailPage() {
  const params = useParams<{ paperId: string }>();
  const paperId = params.paperId;
  const [paper, setPaper] = useState<PaperDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    apiGet<PaperDetail>(API_ROUTES.papers.detail(paperId))
      .then((r) => !cancelled && setPaper(r))
      .catch(console.error)
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [paperId]);

  if (loading)
    return (
      <div className="space-y-4">
        <div className="h-40 animate-pulse rounded-2xl bg-muted" />
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {[0, 1, 2, 3].map((i) => <div key={i} className="h-20 animate-pulse rounded-xl bg-muted" />)}
        </div>
      </div>
    );
  if (!paper)
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed p-10 text-center">
        <FileText className="h-10 w-10 text-muted-foreground/50" />
        <p className="font-semibold">Paper not found</p>
        <Link href="/papers" className="text-sm font-medium text-primary hover:underline">Back to My Papers</Link>
      </div>
    );

  const stats = paper.extracted_data?.statistics ?? {};
  const sections = paper.extracted_data?.sections ?? [];

  const reprocess = async () => {
    await apiPost(API_ROUTES.papers.reprocess(paperId), {});
    alert("Reprocessing started.");
  };

  const remove = async () => {
    if (!confirm("Delete this paper and all its chunks?")) return;
    await apiDelete(API_ROUTES.papers.delete(paperId));
    window.location.href = "/papers";
  };

  const meta = [
    (paper.authors || []).join(", "),
    paper.publication_year ? String(paper.publication_year) : "",
    paper.doi ? `DOI: ${paper.doi}` : "",
  ].filter(Boolean).join(" · ");

  return (
    <div className="space-y-6 pb-8">
      <Link href="/papers" className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to My Papers
      </Link>

      <PageHero
        theme="library"
        icon={FileText}
        eyebrow={<span className="capitalize">Research Library · {paper.processing_status}</span>}
        title={<span className="break-words">{paper.title || "Untitled paper"}</span>}
        description={meta || undefined}
        actions={
          <>
            <Link href={`/papers/${paperId}/chat`} className={heroButtonPrimary}>
              <MessageSquare className="h-4 w-4" /> Chat with this paper
            </Link>
            <button onClick={reprocess} className={heroButtonGhost}>
              <RefreshCw className="h-4 w-4" /> Reprocess
            </button>
            <button onClick={remove} className={`${heroButtonGhost} hover:bg-rose-500/40`}>
              <Trash2 className="h-4 w-4" /> Delete
            </button>
          </>
        }
      />

      {Object.keys(stats).length > 0 && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {Object.entries(stats).map(([k, v]) => (
            <Card key={k} className="p-4">
              <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <BarChart3 className="h-3.5 w-3.5 text-violet-500" /> {k.replace(/_/g, " ")}
              </p>
              <p className="mt-1 font-display text-2xl font-bold tabular-nums">{Number(v).toLocaleString()}</p>
            </Card>
          ))}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {paper.abstract && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <FileText className="h-4 w-4 text-violet-500" /> Abstract
                </CardTitle>
              </CardHeader>
              <CardContent className="text-[15px] leading-relaxed text-foreground/85">{paper.abstract}</CardContent>
            </Card>
          )}

          {sections.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <ListTree className="h-4 w-4 text-violet-500" /> Sections ({sections.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {sections.slice(0, 8).map((s, i) => (
                  <div key={i} className="rounded-xl border-l-4 border-violet-500/60 bg-muted/40 px-4 py-3">
                    <h3 className="text-sm font-semibold">{s.heading}</h3>
                    <p className="mt-1 line-clamp-3 text-sm text-muted-foreground">{s.content}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        {paper.keywords && paper.keywords.length > 0 && (
          <Card className="h-fit">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Tag className="h-4 w-4 text-violet-500" /> Keywords
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {paper.keywords.map((k) => (
                  <span key={k} className="rounded-full bg-violet-500/10 px-3 py-1 text-xs font-medium text-violet-700 dark:text-violet-300">
                    {k}
                  </span>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { MessageSquare, RefreshCw, Trash2 } from "lucide-react";
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

  if (loading) return <p className="text-sm text-muted-foreground">Loading paper…</p>;
  if (!paper) return <p className="text-sm text-muted-foreground">Paper not found.</p>;

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

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{paper.title || "Untitled paper"}</h1>
          <p className="text-sm text-muted-foreground">
            {(paper.authors || []).join(", ")}
            {paper.publication_year ? ` · ${paper.publication_year}` : ""}
            {paper.doi ? ` · DOI: ${paper.doi}` : ""}
          </p>
        </div>
        <div className="flex gap-2">
          <Link href={`/papers/${paperId}/chat`}>
            <Button>
              <MessageSquare className="mr-2 h-4 w-4" />
              Chat with this paper
            </Button>
          </Link>
          <Button variant="outline" onClick={reprocess}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Reprocess
          </Button>
          <Button variant="outline" onClick={remove}>
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {Object.entries(stats).map(([k, v]) => (
          <Card key={k}>
            <CardContent className="p-4">
              <p className="text-xs uppercase text-muted-foreground">{k.replace(/_/g, " ")}</p>
              <p className="text-2xl font-bold">{v as number}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {paper.abstract && (
        <Card>
          <CardHeader>
            <CardTitle>Abstract</CardTitle>
          </CardHeader>
          <CardContent className="text-sm leading-relaxed">{paper.abstract}</CardContent>
        </Card>
      )}

      {paper.keywords && paper.keywords.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Keywords</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {paper.keywords.map((k) => (
                <span key={k} className="rounded-full bg-muted px-3 py-1 text-xs">
                  {k}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {sections.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Sections ({sections.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {sections.slice(0, 8).map((s, i) => (
              <div key={i}>
                <h3 className="text-sm font-semibold">{s.heading}</h3>
                <p className="line-clamp-3 text-xs text-muted-foreground">{s.content}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

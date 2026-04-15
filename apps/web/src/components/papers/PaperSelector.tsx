"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { API_ROUTES } from "@/lib/constants";
import { Card, CardContent } from "@/components/ui/card";
import type { UploadedPaper } from "@/stores/paperStore";

interface Props {
  selectedIds: string[];
  onChange: (ids: string[]) => void;
}

export function PaperSelector({ selectedIds, onChange }: Props) {
  const [papers, setPapers] = useState<UploadedPaper[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    apiGet<{ papers: UploadedPaper[] }>(API_ROUTES.papers.list)
      .then((r) => {
        if (!cancelled) setPapers(r.papers || []);
      })
      .catch(() => {})
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const toggle = (id: string) => {
    if (selectedIds.includes(id)) onChange(selectedIds.filter((s) => s !== id));
    else onChange([...selectedIds, id]);
  };

  if (loading) return <p className="text-sm text-muted-foreground">Loading papers…</p>;
  if (!papers.length)
    return <p className="text-sm text-muted-foreground">Upload papers first to chat with them.</p>;

  return (
    <Card>
      <CardContent className="max-h-72 space-y-2 overflow-y-auto p-3">
        {papers.map((p) => (
          <label
            key={p.id}
            className="flex cursor-pointer items-start gap-2 rounded-md p-2 hover:bg-accent"
          >
            <input
              type="checkbox"
              className="mt-1"
              checked={selectedIds.includes(p.id)}
              onChange={() => toggle(p.id)}
            />
            <div className="min-w-0 flex-1">
              <p className="line-clamp-1 text-sm font-medium">{p.title || "Untitled"}</p>
              <p className="line-clamp-1 text-xs text-muted-foreground">
                {(p.authors || []).slice(0, 3).join(", ")}
              </p>
            </div>
            <span className="text-xs text-muted-foreground">{p.processing_status}</span>
          </label>
        ))}
      </CardContent>
    </Card>
  );
}

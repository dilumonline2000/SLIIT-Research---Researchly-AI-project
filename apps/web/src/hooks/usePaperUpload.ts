"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { apiPost } from "@/lib/api";
import { API_ROUTES, PAPER_STORAGE_BUCKET } from "@/lib/constants";
import { usePaperStore, type UploadedPaper } from "@/stores/paperStore";

interface UploadProgress {
  fileName: string;
  status: "uploading" | "processing" | "ready" | "failed";
  paperId?: string;
  error?: string;
}

/**
 * Uploads PDFs directly to Supabase Storage, then asks the gateway to
 * trigger the extraction pipeline. Realtime status updates land via
 * Supabase Realtime on the uploaded_papers table.
 */
export function usePaperUpload() {
  const [uploads, setUploads] = useState<UploadProgress[]>([]);
  const upsertPaper = usePaperStore((s) => s.upsertPaper);

  const reset = () => setUploads([]);

  async function uploadFiles(files: File[]) {
    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) throw new Error("Not authenticated");

    const next: UploadProgress[] = files.map((f) => ({
      fileName: f.name,
      status: "uploading",
    }));
    setUploads(next);

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        const path = `${user.id}/${Date.now()}-${file.name}`;
        const { error: uploadErr } = await supabase.storage
          .from(PAPER_STORAGE_BUCKET)
          .upload(path, file, { upsert: false, contentType: file.type || "application/pdf" });
        if (uploadErr) throw uploadErr;

        const { data: pub } = supabase.storage.from(PAPER_STORAGE_BUCKET).getPublicUrl(path);

        // Insert paper row. The generated Database types don't yet include
        // uploaded_papers (added in migration 009), so we go through an
        // untyped handle to keep the build clean.
        const untyped = supabase as unknown as {
          from: (t: string) => {
            insert: (v: Record<string, unknown>) => {
              select: () => {
                single: () => Promise<{
                  data: { id: string } & Record<string, unknown>;
                  error: { message: string } | null;
                }>;
              };
            };
          };
        };
        const { data: paperRow, error: insertErr } = await untyped
          .from("uploaded_papers")
          .insert({
            user_id: user.id,
            original_filename: file.name,
            file_url: pub.publicUrl,
            file_size_bytes: file.size,
            processing_status: "uploading",
          })
          .select()
          .single();
        if (insertErr || !paperRow) throw insertErr ?? new Error("insert failed");

        upsertPaper(paperRow as unknown as UploadedPaper);

        // Trigger backend processing
        await apiPost(API_ROUTES.papers.process, { paper_id: paperRow.id });

        next[i] = { fileName: file.name, status: "processing", paperId: paperRow.id };
        setUploads([...next]);
      } catch (err) {
        next[i] = {
          fileName: file.name,
          status: "failed",
          error: err instanceof Error ? err.message : String(err),
        };
        setUploads([...next]);
      }
    }
  }

  return { uploads, uploadFiles, reset };
}

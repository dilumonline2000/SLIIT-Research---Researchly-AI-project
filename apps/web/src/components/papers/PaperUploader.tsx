"use client";

import { useCallback, useRef, useState } from "react";
import { UploadCloud, FileText, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { usePaperUpload } from "@/hooks/usePaperUpload";
import { cn } from "@/lib/utils";

export function PaperUploader({ onUploaded }: { onUploaded?: () => void }) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { uploads, uploadFiles } = usePaperUpload();

  const handleFiles = useCallback(
    async (files: File[]) => {
      const pdfs = files.filter((f) => f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf"));
      if (!pdfs.length) return;
      await uploadFiles(pdfs);
      onUploaded?.();
    },
    [uploadFiles, onUploaded],
  );

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragActive(false);
    handleFiles(Array.from(e.dataTransfer.files));
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed p-8 text-center transition-all sm:p-12",
            dragActive
              ? "scale-[1.01] border-primary bg-primary/10"
              : "border-border bg-gradient-to-b from-violet-500/[0.04] to-transparent hover:border-primary/50",
          )}
        >
          <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-glow animate-float">
            <UploadCloud className="h-8 w-8" />
          </span>
          <p className="text-lg font-semibold">Drag &amp; drop research PDFs</p>
          <p className="text-sm text-muted-foreground">or click to browse — multi-file supported</p>
          <input
            ref={inputRef}
            type="file"
            multiple
            accept="application/pdf,.pdf"
            className="hidden"
            onChange={(e) => handleFiles(Array.from(e.target.files || []))}
          />
          <Button
            onClick={(e) => {
              e.stopPropagation();
              inputRef.current?.click();
            }}
            className="bg-gradient-to-r from-indigo-600 to-violet-600 text-white"
          >
            Choose files
          </Button>
          <p className="text-xs text-muted-foreground">PDF only · stored privately in your account</p>
        </div>

        {uploads.length > 0 && (
          <div className="mt-6 space-y-2">
            {uploads.map((u) => (
              <div
                key={u.fileName}
                className="flex items-center justify-between gap-3 rounded-xl border bg-muted/30 px-3 py-2.5"
              >
                <div className="flex min-w-0 items-center gap-2.5 truncate">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-300">
                    <FileText className="h-4 w-4" />
                  </span>
                  <span className="truncate text-sm">{u.fileName}</span>
                </div>
                <div className="flex shrink-0 items-center gap-2 text-xs font-medium">
                  {u.status === "uploading" && (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin" />
                      <span>Uploading…</span>
                    </>
                  )}
                  {u.status === "processing" && (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin" />
                      <span>Processing…</span>
                    </>
                  )}
                  {u.status === "ready" && (
                    <>
                      <CheckCircle2 className="h-3 w-3 text-green-500" />
                      <span>Ready</span>
                    </>
                  )}
                  {u.status === "failed" && (
                    <>
                      <AlertCircle className="h-3 w-3 text-red-500" />
                      <span>{u.error || "Failed"}</span>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

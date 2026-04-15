"use client";

import { useRouter } from "next/navigation";
import { PaperUploader } from "@/components/papers/PaperUploader";

export default function UploadPaperPage() {
  const router = useRouter();
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Upload Research Papers</h1>
        <p className="text-sm text-muted-foreground">
          PDFs are uploaded directly to your private Supabase storage, then processed:
          extracted → chunked → embedded → indexed for RAG retrieval. Status updates appear live.
        </p>
      </div>

      <PaperUploader onUploaded={() => router.push("/papers")} />
    </div>
  );
}

"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { UploadCloud, FileSearch, Scissors, Binary, DatabaseZap, ArrowLeft } from "lucide-react";
import { PaperUploader } from "@/components/papers/PaperUploader";
import { PageHero, heroButtonGhost } from "@/components/shared/PageHero";

const STEPS = [
  { icon: FileSearch, label: "Extract", desc: "Text & metadata pulled from the PDF" },
  { icon: Scissors, label: "Chunk", desc: "Split into meaningful passages" },
  { icon: Binary, label: "Embed", desc: "SBERT vectors for every chunk" },
  { icon: DatabaseZap, label: "Index", desc: "Ready for RAG chat & search" },
];

export default function UploadPaperPage() {
  const router = useRouter();
  return (
    <div className="mx-auto max-w-4xl space-y-6 pb-8">
      <PageHero
        theme="library"
        icon={UploadCloud}
        title="Upload Research Papers"
        description="PDFs are uploaded directly to your private Supabase storage, then processed and indexed for RAG retrieval. Status updates appear live."
        actions={
          <Link href="/papers" className={heroButtonGhost}>
            <ArrowLeft className="h-4 w-4" /> My Papers
          </Link>
        }
      />

      {/* Processing pipeline */}
      <ol className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {STEPS.map((s, i) => (
          <li key={s.label} className="relative rounded-xl border bg-card p-4 shadow-soft">
            <span className="absolute right-3 top-3 font-display text-xs font-bold text-muted-foreground/60">
              0{i + 1}
            </span>
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 text-white">
              <s.icon className="h-4 w-4" />
            </span>
            <p className="mt-2.5 text-sm font-semibold">{s.label}</p>
            <p className="mt-0.5 text-xs leading-snug text-muted-foreground">{s.desc}</p>
          </li>
        ))}
      </ol>

      <PaperUploader onUploaded={() => router.push("/papers")} />
    </div>
  );
}

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function DataManagementPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Research Data Collection & Management</h1>
        <p className="text-muted-foreground">Module 3 · Owner: N V Hewamanne</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[
          { title: "Data Pipeline", desc: "Multi-source ETL (IEEE, arXiv, ACM, SLIIT, Scholar)" },
          { title: "Topic Categorization", desc: "SciBERT multi-label classifier" },
          { title: "Plagiarism Trends", desc: "SBERT pairwise similarity" },
          { title: "Summarizer", desc: "BART/T5 abstractive summarization" },
          { title: "Data Quality", desc: "Completeness + consistency metrics" },
        ].map((f) => (
          <Card key={f.title}>
            <CardHeader>
              <CardTitle className="text-lg">{f.title}</CardTitle>
              <CardDescription>{f.desc}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Scaffolded — implementation pending Phase 4.
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

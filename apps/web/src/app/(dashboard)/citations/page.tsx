import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function CitationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Research Integrity & Compliance</h1>
        <p className="text-muted-foreground">
          Module 1 · Owner: K D T Kariyawasam
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[
          { title: "Citation Parser", desc: "NER-based extraction + APA/IEEE formatting", href: "/citations/parser" },
          { title: "Gap Analysis", desc: "SBERT + BERTopic discovery", href: "/citations/gaps" },
          { title: "Proposal Generator", desc: "RAG + LoRA-tuned LLM", href: "/citations/proposal" },
          { title: "Plagiarism Checker", desc: "TF-IDF + SBERT similarity", href: "/citations/plagiarism" },
          { title: "Mind Map Builder", desc: "KeyBERT + NetworkX", href: "/citations/mindmap" },
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

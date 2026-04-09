import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function CollaborationPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Collaboration & Recommendation</h1>
        <p className="text-muted-foreground">Module 2 · Owner: S P U Gunathilaka</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[
          { title: "Supervisor Match", desc: "SBERT cosine similarity + multi-factor scoring" },
          { title: "Peer Connect", desc: "Hybrid CF + CBF recommendations" },
          { title: "Feedback Sentiment", desc: "BERT aspect-based sentiment (4 aspects)" },
          { title: "Effectiveness Score", desc: "Multi-dimensional evaluation" },
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

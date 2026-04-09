import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Research Performance Analytics</h1>
        <p className="text-muted-foreground">Module 4 · Owner: H W S S Jayasundara</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[
          { title: "Trend Forecasting", desc: "ARIMA + Prophet ensemble (MAPE < 22%)" },
          { title: "Quality Scoring", desc: "Weighted multi-dimensional metrics" },
          { title: "Interactive Dashboards", desc: "D3.js + Supabase Realtime" },
          { title: "Concept Mind Maps", desc: "GNN (GCN) + KeyBERT extraction" },
          { title: "Success Prediction", desc: "RF + XGBoost (F1 > 0.75)" },
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

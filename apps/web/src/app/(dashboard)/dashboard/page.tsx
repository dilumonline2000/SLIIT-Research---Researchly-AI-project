import { BookOpen, Users, Database, LineChart, ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MODULES } from "@/lib/constants";

const moduleIcons = { 1: BookOpen, 2: Users, 3: Database, 4: LineChart } as const;
const moduleHrefs = {
  1: "/citations",
  2: "/collaboration",
  3: "/data-management",
  4: "/analytics",
} as const;

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome to Researchly AI — your research workflow starts here.
        </p>
      </div>

      {/* Stats row (placeholder — wire to Supabase queries in Phase 4) */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Proposals", value: "—", hint: "drafts + submitted" },
          { label: "Citations parsed", value: "—", hint: "this month" },
          { label: "Quality score", value: "—", hint: "latest proposal" },
          { label: "Success likelihood", value: "—", hint: "ML prediction" },
        ].map((s) => (
          <Card key={s.label}>
            <CardHeader className="pb-2">
              <CardDescription>{s.label}</CardDescription>
              <CardTitle className="text-3xl">{s.value}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">{s.hint}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Module quick-links */}
      <div>
        <h2 className="mb-4 text-xl font-semibold">Modules</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {MODULES.map((mod) => {
            const Icon = moduleIcons[mod.id as keyof typeof moduleIcons];
            const href = moduleHrefs[mod.id as keyof typeof moduleHrefs];
            return (
              <Link key={mod.id} href={href}>
                <Card className="h-full transition-all hover:shadow-md hover:-translate-y-0.5">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div
                        className={`flex h-10 w-10 items-center justify-center rounded-lg ${mod.color} text-white`}
                      >
                        <Icon className="h-5 w-5" />
                      </div>
                      <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <CardTitle className="pt-3 text-lg">{mod.name}</CardTitle>
                    <CardDescription>{mod.description}</CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

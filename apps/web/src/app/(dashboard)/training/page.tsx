"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles, Clock, Layers, CheckCircle2, XCircle, Cpu, Play, Loader2 } from "lucide-react";
import { PageHero, heroButtonPrimary } from "@/components/shared/PageHero";
import { apiGet, apiPost } from "@/lib/api";
import { API_ROUTES } from "@/lib/constants";

interface TrainingStatus {
  pending: number;
  queued: number;
  completed: number;
  failed: number;
  by_model: Record<string, number>;
}

interface ModelVersion {
  id: string;
  model_name: string;
  version: string;
  is_active: boolean;
  metrics?: Record<string, number> | null;
  created_at?: string;
}

export default function TrainingDashboardPage() {
  const [status, setStatus] = useState<TrainingStatus | null>(null);
  const [models, setModels] = useState<ModelVersion[]>([]);
  const [triggering, setTriggering] = useState(false);

  const refresh = async () => {
    try {
      const [s, m] = await Promise.all([
        apiGet<TrainingStatus>(API_ROUTES.training.status),
        apiGet<{ models: ModelVersion[] }>(API_ROUTES.training.models),
      ]);
      setStatus(s);
      setModels(m.models || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const trigger = async () => {
    setTriggering(true);
    try {
      await apiPost(API_ROUTES.training.trigger, {});
      await refresh();
    } finally {
      setTriggering(false);
    }
  };

  const queueTiles = [
    { label: "Pending", value: status?.pending ?? 0, icon: Clock, tone: "from-amber-500 to-orange-500" },
    { label: "Queued", value: status?.queued ?? 0, icon: Layers, tone: "from-sky-500 to-indigo-500" },
    { label: "Completed", value: status?.completed ?? 0, icon: CheckCircle2, tone: "from-emerald-500 to-teal-500" },
    { label: "Failed", value: status?.failed ?? 0, icon: XCircle, tone: "from-rose-500 to-pink-500" },
  ];
  const byModel = status ? Object.entries(status.by_model) : [];
  const maxQueue = Math.max(1, ...byModel.map(([, c]) => c));

  return (
    <div className="space-y-6 pb-8">
      <PageHero
        theme="library"
        icon={Sparkles}
        title="Continuous Training"
        description="Every paper upload, chat Q&A, and feedback automatically feeds the training queue — so the models keep getting smarter."
        actions={
          <button onClick={trigger} disabled={triggering} className={heroButtonPrimary}>
            {triggering ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            {triggering ? "Triggering…" : "Trigger next batch"}
          </button>
        }
        stats={[
          { label: "Model versions", value: models.length, icon: Cpu },
          { label: "Active", value: models.filter((m) => m.is_active).length, icon: CheckCircle2 },
        ]}
      />

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {queueTiles.map((t) => (
          <Card key={t.label} className="relative overflow-hidden p-4">
            <div className={`absolute -right-5 -top-5 h-16 w-16 rounded-full bg-gradient-to-br ${t.tone} opacity-15`} />
            <span className={`flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br ${t.tone} text-white shadow-sm`}>
              <t.icon className="h-4 w-4" />
            </span>
            <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{t.label}</p>
            <p className="font-display text-2xl font-bold tabular-nums">{t.value}</p>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Layers className="h-4 w-4 text-violet-500" /> Queue by target model
            </CardTitle>
          </CardHeader>
          <CardContent>
            {byModel.length > 0 ? (
              <div className="space-y-3">
                {byModel.map(([model, count]) => (
                  <div key={model} className="space-y-1">
                    <div className="flex items-center justify-between gap-2 text-sm">
                      <span className="truncate font-mono text-xs sm:text-sm">{model}</span>
                      <span className="shrink-0 rounded-full bg-violet-500/10 px-2 py-0.5 text-xs font-semibold text-violet-700 dark:text-violet-300">
                        {count}
                      </span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500"
                        style={{ width: `${(count / maxQueue) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">
                No queue items yet.
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Cpu className="h-4 w-4 text-violet-500" /> Model versions
            </CardTitle>
          </CardHeader>
          <CardContent>
            {models.length === 0 ? (
              <p className="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">
                No model versions recorded yet.
              </p>
            ) : (
              <div className="-mx-2 overflow-x-auto">
                <table className="w-full min-w-[480px] text-sm">
                  <thead>
                    <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                      <th className="px-2 py-2 font-semibold">Model</th>
                      <th className="px-2 py-2 font-semibold">Version</th>
                      <th className="px-2 py-2 font-semibold">Status</th>
                      <th className="px-2 py-2 font-semibold">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {models.map((m) => (
                      <tr key={m.id} className="border-b last:border-0 hover:bg-muted/40">
                        <td className="px-2 py-2.5 font-mono text-xs sm:text-sm">{m.model_name}</td>
                        <td className="px-2 py-2.5">
                          <span className="rounded-md bg-muted px-1.5 py-0.5 font-mono text-xs">{m.version}</span>
                        </td>
                        <td className="px-2 py-2.5">
                          {m.is_active ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-600 dark:text-emerald-300">
                              <CheckCircle2 className="h-3 w-3" /> Active
                            </span>
                          ) : (
                            <span className="text-xs text-muted-foreground">Inactive</span>
                          )}
                        </td>
                        <td className="px-2 py-2.5 text-xs text-muted-foreground">
                          {m.created_at ? new Date(m.created_at).toLocaleString() : ""}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

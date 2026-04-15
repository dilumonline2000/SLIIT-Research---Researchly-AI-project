"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Continuous Training</h1>
          <p className="text-sm text-muted-foreground">
            Every paper upload, chat Q&amp;A, and feedback automatically feeds the queue.
          </p>
        </div>
        <Button onClick={trigger} disabled={triggering}>
          {triggering ? "Triggering…" : "Trigger next batch"}
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs uppercase text-muted-foreground">Pending</p>
            <p className="text-2xl font-bold">{status?.pending ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs uppercase text-muted-foreground">Queued</p>
            <p className="text-2xl font-bold">{status?.queued ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs uppercase text-muted-foreground">Completed</p>
            <p className="text-2xl font-bold">{status?.completed ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs uppercase text-muted-foreground">Failed</p>
            <p className="text-2xl font-bold">{status?.failed ?? 0}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Queue by target model</CardTitle>
        </CardHeader>
        <CardContent>
          {status && Object.keys(status.by_model).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(status.by_model).map(([model, count]) => (
                <div key={model} className="flex items-center justify-between text-sm">
                  <span className="font-mono">{model}</span>
                  <span className="rounded bg-muted px-2 py-0.5 text-xs">{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No queue items yet.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Model versions</CardTitle>
        </CardHeader>
        <CardContent>
          {models.length === 0 ? (
            <p className="text-sm text-muted-foreground">No model versions recorded yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs uppercase text-muted-foreground">
                  <th className="py-2">Model</th>
                  <th className="py-2">Version</th>
                  <th className="py-2">Active</th>
                  <th className="py-2">Created</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => (
                  <tr key={m.id} className="border-b">
                    <td className="py-2 font-mono">{m.model_name}</td>
                    <td className="py-2">{m.version}</td>
                    <td className="py-2">{m.is_active ? "✅" : "—"}</td>
                    <td className="py-2 text-xs text-muted-foreground">
                      {m.created_at ? new Date(m.created_at).toLocaleString() : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiGet } from "@/lib/api";

interface ForecastPoint {
  date: string;
  predicted: number;
  lower_bound: number;
  upper_bound: number;
}

interface Forecast {
  topic: string;
  model_type: string;
  horizon_months: number;
  points: ForecastPoint[];
}

export default function TrendsPage() {
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    apiGet<{ forecasts: Forecast[] }>(`${API_ROUTES.module4.trends}?horizon=12`)
      .then((data) => setForecasts(data.forecasts))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = filter
    ? forecasts.filter(f => f.topic.toLowerCase().includes(filter.toLowerCase()))
    : forecasts;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Trend Forecasting</h1>
        <p className="text-muted-foreground">Research topic popularity forecasts using ARIMA + Prophet.</p>
      </div>

      <div className="max-w-sm">
        <Label htmlFor="filter">Filter by topic</Label>
        <Input id="filter" placeholder="e.g., machine learning" value={filter} onChange={(e) => setFilter(e.target.value)} />
      </div>

      {loading && <p className="text-sm text-muted-foreground">Loading forecasts...</p>}

      {!loading && filtered.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">
              No forecasts available yet. Train the forecasting models first using: <code>python ml/training/train_forecaster.py</code>
            </p>
          </CardContent>
        </Card>
      )}

      {filtered.map((forecast) => (
        <Card key={forecast.topic}>
          <CardHeader>
            <CardTitle className="text-lg">
              {forecast.topic}
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                ({forecast.model_type} · {forecast.horizon_months} months)
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-4">Date</th>
                    <th className="pb-2 pr-4">Predicted</th>
                    <th className="pb-2 pr-4">Lower Bound</th>
                    <th className="pb-2">Upper Bound</th>
                  </tr>
                </thead>
                <tbody>
                  {forecast.points.map((p) => (
                    <tr key={p.date} className="border-b border-border/50">
                      <td className="py-1.5 pr-4">{p.date}</td>
                      <td className="py-1.5 pr-4 font-medium">{p.predicted.toFixed(1)}</td>
                      <td className="py-1.5 pr-4 text-muted-foreground">{p.lower_bound.toFixed(1)}</td>
                      <td className="py-1.5 text-muted-foreground">{p.upper_bound.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

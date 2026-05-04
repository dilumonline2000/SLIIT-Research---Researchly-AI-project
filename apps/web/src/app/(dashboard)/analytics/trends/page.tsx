"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TrendingUp, TrendingDown, Minus, AlertCircle } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Area, ComposedChart } from "recharts";
import { API_ROUTES } from "@/lib/constants";
import { apiGet } from "@/lib/api";

interface TrendPoint {
  year: number;
  count: number;
  type: "historical" | "forecast";
}

interface Forecast {
  topic: string;
  horizon_years: number;
  historical: TrendPoint[];
  forecast: TrendPoint[];
  trend_direction: "rising" | "declining" | "stable" | "insufficient_data" | "unknown";
  model_type: string;
  data_range: string;
  model_version: string;
}

interface ApiResponse {
  forecasts: Forecast[];
  available_topics: string[];
}

const DIRECTION_INFO: Record<string, { icon: React.ComponentType<{ className?: string }>; color: string; label: string }> = {
  rising: { icon: TrendingUp, color: "text-emerald-600", label: "Rising" },
  declining: { icon: TrendingDown, color: "text-rose-600", label: "Declining" },
  stable: { icon: Minus, color: "text-blue-600", label: "Stable" },
  insufficient_data: { icon: AlertCircle, color: "text-muted-foreground", label: "Insufficient data" },
  unknown: { icon: AlertCircle, color: "text-muted-foreground", label: "Unknown" },
};

export default function TrendsPage() {
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [availableTopics, setAvailableTopics] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("");
  const [horizon, setHorizon] = useState(3);

  const fetchForecasts = async (topic: string = "", h: number = 3) => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ horizon: h.toString() });
      if (topic.trim()) params.set("topic", topic.trim());
      const data = await apiGet<ApiResponse>(`${API_ROUTES.module4.trends}?${params}`);
      setForecasts(data.forecasts || []);
      setAvailableTopics(data.available_topics || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch forecasts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecasts("", horizon);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFilter = () => fetchForecasts(filter, horizon);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Trend Forecasting</h1>
        <p className="text-muted-foreground">
          ARIMA forecasts trained on 4,219 SLIIT papers (2000–2026). Predicts publication
          counts per research domain over the next few years.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filter Forecasts</CardTitle>
          <CardDescription>
            Available topics: {availableTopics.length > 0 ? availableTopics.join(", ") : "loading..."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[200px]">
              <label className="text-sm font-medium">Topic (optional)</label>
              <Input
                placeholder="e.g., computing, business, engineering"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Horizon (years)</label>
              <Input
                type="number"
                min={1}
                max={10}
                value={horizon}
                onChange={(e) => setHorizon(parseInt(e.target.value) || 3)}
                className="w-24"
              />
            </div>
            <Button onClick={handleFilter} disabled={loading}>
              {loading ? "Loading..." : "Update Forecasts"}
            </Button>
          </div>
          {error && (
            <p className="mt-3 text-sm text-destructive">{error}</p>
          )}
        </CardContent>
      </Card>

      {loading && forecasts.length === 0 && (
        <p className="text-sm text-muted-foreground">Loading forecasts...</p>
      )}

      {!loading && forecasts.length === 0 && !error && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">
              No forecasts available. Make sure Module 4 service is running on port 8004
              and trained models exist at <code>services/module4-analytics/models/</code>.
            </p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {forecasts.map((forecast) => {
          const dirInfo = DIRECTION_INFO[forecast.trend_direction] || DIRECTION_INFO.unknown;
          const DirIcon = dirInfo.icon;
          // Combine historical + forecast for unified chart
          const chartData = [
            ...forecast.historical.map((p) => ({ year: p.year, historical: p.count, forecast: null as number | null })),
            ...forecast.forecast.map((p) => ({ year: p.year, historical: null as number | null, forecast: p.count })),
          ];

          return (
            <Card key={forecast.topic}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg capitalize">
                      {forecast.topic.replace("_", " ")}
                    </CardTitle>
                    <CardDescription>
                      {forecast.model_type} · Data: {forecast.data_range}
                    </CardDescription>
                  </div>
                  <div className={`flex items-center gap-1 ${dirInfo.color}`}>
                    <DirIcon className="h-4 w-4" />
                    <span className="text-sm font-semibold">{dirInfo.label}</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="year" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="historical"
                        stroke="#8b5cf6"
                        strokeWidth={2}
                        name="Historical"
                        connectNulls
                        dot={{ r: 3 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="forecast"
                        stroke="#10b981"
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        name="Forecast"
                        connectNulls
                        dot={{ r: 4 }}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-md bg-muted p-2">
                    <p className="text-muted-foreground">Historical points</p>
                    <p className="text-lg font-semibold">{forecast.historical.length}</p>
                  </div>
                  <div className="rounded-md bg-muted p-2">
                    <p className="text-muted-foreground">Forecast (next {forecast.horizon_years}y)</p>
                    <p className="text-lg font-semibold">
                      {forecast.forecast.map((p) => p.count.toFixed(0)).join(" → ")}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

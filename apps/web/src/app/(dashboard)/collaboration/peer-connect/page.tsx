"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface PeerMatch {
  peer_id: string;
  similarity_score: number;
  shared_interests: string[];
  complementary_skills: string[];
  recommendation_type: string;
}

export default function PeerDiscoveryPage() {
  const [matches, setMatches] = useState<PeerMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleDiscover = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<{ matches: PeerMatch[] }>(API_ROUTES.module2.matchPeers, {
        student_id: "current",
        top_k: 10,
      });
      setMatches(data.matches);
    } catch (err: any) {
      setError(err.message || "Discovery failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Peer Discovery</h1>
        <p className="text-muted-foreground">Find research peers with shared or complementary interests.</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <Button onClick={handleDiscover} disabled={loading}>
            {loading ? "Searching..." : "Discover Peers"}
          </Button>
          {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {matches.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {matches.map((m) => (
            <Card key={m.peer_id}>
              <CardHeader>
                <CardTitle className="text-lg">
                  Peer {m.peer_id.slice(0, 8)}...
                  <span className="ml-2 text-sm font-normal text-muted-foreground">
                    {(m.similarity_score * 100).toFixed(0)}% match
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {m.shared_interests.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">Shared interests</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {m.shared_interests.map((s) => (
                        <span key={s} className="rounded bg-green-100 px-2 py-0.5 text-xs text-green-800 dark:bg-green-900 dark:text-green-200">{s}</span>
                      ))}
                    </div>
                  </div>
                )}
                {m.complementary_skills.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">Complementary skills</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {m.complementary_skills.map((s) => (
                        <span key={s} className="rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-800 dark:bg-blue-900 dark:text-blue-200">{s}</span>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

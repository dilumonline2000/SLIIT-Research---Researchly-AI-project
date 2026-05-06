"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Sun, Moon, Monitor } from "lucide-react";
import { AIProviderToggle } from "@/components/shared/AIProviderToggle";
import { ModelStatusGrid } from "@/components/shared/ModelStatusGrid";
import { useAIProviderStore } from "@/stores/aiProviderStore";
import { useThemeStore, type Theme } from "@/stores/themeStore";

const THEME_META: Record<Theme, { Icon: typeof Sun }> = {
  light:  { Icon: Sun },
  dark:   { Icon: Moon },
  system: { Icon: Monitor },
};

export default function SettingsPage() {
  const { theme, setTheme } = useThemeStore();
  const [notifications, setNotifications] = useState(true);
  const { checkLocalAvailability } = useAIProviderStore();

  // Force a fresh model status check every time the settings page opens
  useEffect(() => {
    checkLocalAvailability(true);
  }, [checkLocalAvailability]);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Customize the look and feel of the application.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Theme</Label>
            <div className="flex gap-2">
              {(["light", "dark", "system"] as const).map((t) => {
                const { Icon } = THEME_META[t];
                return (
                  <Button
                    key={t}
                    variant={theme === t ? "default" : "outline"}
                    size="sm"
                    onClick={() => setTheme(t)}
                  >
                    <Icon className="mr-2 h-4 w-4" />
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </Button>
                );
              })}
            </div>
            <p className="text-xs text-muted-foreground">
              Tip: there&apos;s also a quick toggle in the navbar for one-click switching.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
          <CardDescription>Configure how you receive updates.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Email notifications</p>
              <p className="text-xs text-muted-foreground">Receive updates about your research projects</p>
            </div>
            <button
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${notifications ? "bg-primary" : "bg-secondary"}`}
              onClick={() => setNotifications(!notifications)}
            >
              <span className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${notifications ? "translate-x-6" : "translate-x-1"}`} />
            </button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🤖 AI Provider Settings
          </CardTitle>
          <CardDescription>
            Switch between Google Gemini API and your locally trained research models.
            This setting applies to all AI features across the platform.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <AIProviderToggle />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 space-y-1">
              <p className="font-semibold text-blue-800 flex items-center gap-1.5">
                ⚡ Gemini API Mode
              </p>
              <ul className="text-blue-700 space-y-0.5 text-xs">
                <li>• Uses Google Gemini 1.5 Flash / Pro</li>
                <li>• Fast responses, handles any question</li>
                <li>• Requires internet connection</li>
                <li>• Uses your API key quota</li>
                <li>• Best for general questions</li>
              </ul>
            </div>
            <div className="p-3 rounded-lg bg-green-50 border border-green-200 space-y-1">
              <p className="font-semibold text-green-800 flex items-center gap-1.5">
                🧠 Local AI Mode
              </p>
              <ul className="text-green-700 space-y-0.5 text-xs">
                <li>• Uses your trained SBERT / SciBERT / BART models</li>
                <li>• Answers based on your research data</li>
                <li>• Works offline, no API cost</li>
                <li>• Improves as you upload more papers</li>
                <li>• Best for domain-specific research questions</li>
              </ul>
            </div>
          </div>

          <div className="border-t" />

          <div className="space-y-3">
            <h3 className="text-sm font-semibold">Local Model Status</h3>
            <ModelStatusGrid />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>About</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1 text-sm text-muted-foreground">
          <p>Researchly AI v0.1.0</p>
          <p>AI-Powered Research Paper Assistant & Collaboration Platform</p>
          <p>Project: R26-IT-116 · SLIIT</p>
        </CardContent>
      </Card>
    </div>
  );
}

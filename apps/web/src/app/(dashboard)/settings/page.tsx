"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { AIProviderToggle } from "@/components/shared/AIProviderToggle";
import { ModelStatusGrid } from "@/components/shared/ModelStatusGrid";

export default function SettingsPage() {
  const [theme, setTheme] = useState<"light" | "dark" | "system">("system");
  const [notifications, setNotifications] = useState(true);

  const handleThemeChange = (newTheme: "light" | "dark" | "system") => {
    setTheme(newTheme);
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else if (newTheme === "light") {
      document.documentElement.classList.remove("dark");
    } else {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      document.documentElement.classList.toggle("dark", prefersDark);
    }
  };

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
              {(["light", "dark", "system"] as const).map((t) => (
                <Button key={t} variant={theme === t ? "default" : "outline"} size="sm" onClick={() => handleThemeChange(t)}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </Button>
              ))}
            </div>
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

"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Sun, Moon, Monitor, ShieldCheck, ShieldOff, Settings as SettingsIcon, Palette, Bell, Cpu, Zap, Brain } from "lucide-react";
import { PageHero } from "@/components/shared/PageHero";
import { AIProviderToggle } from "@/components/shared/AIProviderToggle";
import { ModelStatusGrid } from "@/components/shared/ModelStatusGrid";
import { useAIProviderStore } from "@/stores/aiProviderStore";
import { useThemeStore, type Theme } from "@/stores/themeStore";
import { useCollaborationStore } from "@/stores/collaborationStore";

const THEME_META: Record<Theme, { Icon: typeof Sun }> = {
  light:  { Icon: Sun },
  dark:   { Icon: Moon },
  system: { Icon: Monitor },
};

export default function SettingsPage() {
  const { theme, setTheme } = useThemeStore();
  const [notifications, setNotifications] = useState(true);
  const { checkLocalAvailability, provider, modelStatuses } = useAIProviderStore();
  const { otpEnabled, setOtpEnabled } = useCollaborationStore();

  // Force a fresh model status check every time the settings page opens
  useEffect(() => {
    checkLocalAvailability(true);
  }, [checkLocalAvailability]);

  const loadedModels = Object.values(modelStatuses).filter((s) => s?.loaded).length;

  const iconChip = (Icon: typeof Sun, gradient: string) => (
    <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${gradient} text-white shadow-sm`}>
      <Icon className="h-4 w-4" />
    </span>
  );

  return (
    <div className="space-y-6 pb-8">
      <PageHero
        theme="account"
        icon={SettingsIcon}
        title="Settings"
        description="Personalise how Researchly AI looks, which AI engine powers it, and how collaboration features behave."
        stats={[
          { label: "Theme", value: <span className="capitalize">{theme}</span>, icon: THEME_META[theme].Icon },
          { label: "AI provider", value: <span className="capitalize">{provider}</span>, icon: Cpu },
          { label: "Feedback OTP", value: otpEnabled ? "On" : "Off", icon: ShieldCheck },
        ]}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2.5 text-lg">
              {iconChip(Palette, "from-indigo-500 to-fuchsia-500")} Appearance
            </CardTitle>
            <CardDescription>Customize the look and feel of the application.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Label>Theme</Label>
            <div className="grid grid-cols-3 gap-2 sm:gap-3">
              {(["light", "dark", "system"] as const).map((t) => {
                const { Icon } = THEME_META[t];
                const active = theme === t;
                return (
                  <button
                    key={t}
                    onClick={() => setTheme(t)}
                    aria-pressed={active}
                    className={`group overflow-hidden rounded-xl border-2 text-left transition-all ${
                      active ? "border-primary shadow-glow" : "border-border hover:border-primary/40"
                    }`}
                  >
                    {/* Mini preview */}
                    <div
                      className={`flex h-16 gap-1.5 p-2 ${
                        t === "light"
                          ? "bg-slate-100"
                          : t === "dark"
                            ? "bg-slate-900"
                            : "bg-gradient-to-r from-slate-100 from-50% to-slate-900 to-50%"
                      }`}
                    >
                      <div className={`w-1/4 rounded ${t === "dark" ? "bg-slate-800" : "bg-white"}`} />
                      <div className="flex flex-1 flex-col gap-1">
                        <div className="h-3 rounded bg-gradient-to-r from-indigo-500 to-fuchsia-500" />
                        <div className={`flex-1 rounded ${t === "dark" ? "bg-slate-800" : t === "light" ? "bg-white" : "bg-slate-500/40"}`} />
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 px-2.5 py-2 text-xs font-semibold sm:text-sm">
                      <Icon className={`h-4 w-4 ${active ? "text-primary" : "text-muted-foreground"}`} />
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </div>
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-muted-foreground">
              Tip: there&apos;s also a quick toggle in the navbar for one-click switching.
            </p>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2.5 text-lg">
                {iconChip(Bell, "from-sky-500 to-indigo-500")} Notifications
              </CardTitle>
              <CardDescription>Configure how you receive updates.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between gap-4 rounded-xl bg-muted/40 p-3.5">
                <div>
                  <p className="text-sm font-medium">Email notifications</p>
                  <p className="text-xs text-muted-foreground">Receive updates about your research projects</p>
                </div>
                <button
                  role="switch"
                  aria-checked={notifications}
                  className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors ${notifications ? "bg-primary" : "bg-secondary"}`}
                  onClick={() => setNotifications(!notifications)}
                >
                  <span className={`inline-block h-4 w-4 rounded-full bg-white shadow transition-transform ${notifications ? "translate-x-6" : "translate-x-1"}`} />
                </button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2.5 text-lg">
                {otpEnabled
                  ? iconChip(ShieldCheck, "from-emerald-500 to-teal-500")
                  : iconChip(ShieldOff, "from-slate-400 to-slate-600")}
                Collaboration Security
              </CardTitle>
              <CardDescription>
                Control security settings for the Supervisor Feedback feature.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between gap-4 rounded-xl bg-muted/40 p-3.5">
                <div className="space-y-1">
                  <Label className="text-sm font-medium">Email OTP Verification</Label>
                  <p className="max-w-sm text-xs text-muted-foreground">
                    When enabled, users must verify their email address with a one-time code before
                    submitting supervisor feedback. Disable this during demos or when SMTP is not
                    configured.
                  </p>
                </div>
                <button
                  role="switch"
                  aria-checked={otpEnabled}
                  onClick={() => setOtpEnabled(!otpEnabled)}
                  className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
                    otpEnabled ? "bg-primary" : "bg-secondary"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 rounded-full bg-white shadow transition-transform ${
                      otpEnabled ? "translate-x-6" : "translate-x-1"
                    }`}
                  />
                </button>
              </div>
              <div
                className={`rounded-xl border px-3.5 py-2.5 text-xs ${
                  otpEnabled
                    ? "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-200"
                    : "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-200"
                }`}
              >
                {otpEnabled ? (
                  <span>
                    <strong>Enabled</strong> — Feedback requires email verification. Configure{" "}
                    <code className="font-mono">SMTP_HOST</code>,{" "}
                    <code className="font-mono">SMTP_USER</code>,{" "}
                    <code className="font-mono">SMTP_PASS</code> in{" "}
                    <code className="break-all font-mono">services/module2-collaboration/.env</code> to send real
                    emails. If SMTP is not set up, the code will be shown on-screen.
                  </span>
                ) : (
                  <span>
                    <strong>Disabled</strong> — Feedback can be submitted without email verification.
                    Useful for demos and development.
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2.5 text-lg">
            {iconChip(Cpu, "from-violet-500 to-purple-600")} AI Provider Settings
          </CardTitle>
          <CardDescription>
            Switch between Google Gemini API and your locally trained research models.
            This setting applies to all AI features across the platform.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <AIProviderToggle />

          <div className="grid grid-cols-1 gap-4 text-sm md:grid-cols-2">
            <div className="space-y-2 rounded-xl border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/60 dark:bg-blue-950/30">
              <p className="flex items-center gap-2 font-semibold text-blue-800 dark:text-blue-200">
                <Zap className="h-4 w-4" /> Gemini API Mode
              </p>
              <ul className="space-y-1 text-xs text-blue-700 dark:text-blue-300">
                <li>• Uses Google Gemini 1.5 Flash / Pro</li>
                <li>• Fast responses, handles any question</li>
                <li>• Requires internet connection</li>
                <li>• Uses your API key quota</li>
                <li>• Best for general questions</li>
              </ul>
            </div>
            <div className="space-y-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900/60 dark:bg-emerald-950/30">
              <p className="flex items-center gap-2 font-semibold text-emerald-800 dark:text-emerald-200">
                <Brain className="h-4 w-4" /> Local AI Mode
              </p>
              <ul className="space-y-1 text-xs text-emerald-700 dark:text-emerald-300">
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
            <h3 className="flex items-center justify-between text-sm font-semibold">
              Local Model Status
              <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-600 dark:text-emerald-300">
                {loadedModels} loaded
              </span>
            </h3>
            <ModelStatusGrid />
          </div>
        </CardContent>
      </Card>

      <Card className="overflow-hidden">
        <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 via-violet-500 to-fuchsia-500 font-display text-xl font-bold text-white shadow-glow">
            R
          </span>
          <div className="space-y-0.5 text-sm">
            <p className="font-semibold">Researchly AI v0.1.0</p>
            <p className="text-muted-foreground">AI-Powered Research Paper Assistant & Collaboration Platform</p>
            <p className="text-muted-foreground">Project: R26-IT-116 · SLIIT</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowRight, type LucideIcon } from "lucide-react";
import { PageHero, HERO_THEMES, type HeroTheme, type HeroStat } from "./PageHero";
import { cn } from "@/lib/utils";

export interface HubFeature {
  title: string;
  desc: string;
  icon: LucideIcon;
  href: string;
  /** Tailwind gradient stops for the icon tile, e.g. "from-blue-500 to-cyan-500" */
  gradient: string;
  badge?: string;
}

interface FeatureHubProps {
  theme: HeroTheme;
  icon: LucideIcon;
  title: string;
  tagline: string;
  owner: string;
  features: HubFeature[];
  stats?: HeroStat[];
  /** Extra content between the hero and the tool grid */
  children?: ReactNode;
}

export function FeatureHub({ theme, icon, title, tagline, owner, features, stats, children }: FeatureHubProps) {
  const t = HERO_THEMES[theme];
  return (
    <div className="space-y-6 pb-8">
      <PageHero
        theme={theme}
        icon={icon}
        title={title}
        description={
          <>
            <p>{tagline}</p>
            <p className="mt-2 text-xs text-white/70">
              Led by <span className="font-semibold text-white">{owner}</span> · {features.length} AI tools
            </p>
          </>
        }
        stats={stats}
      />

      {children}

      <div>
        <div className="mb-3 flex items-end justify-between">
          <div>
            <h2 className="text-lg font-semibold sm:text-xl">Tools in {t.section}</h2>
            <p className="text-sm text-muted-foreground">Pick a tool to get started</p>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {features.map((f, i) => (
            <Link key={f.title} href={f.href} className="group block h-full">
              <div className="relative flex h-full flex-col overflow-hidden rounded-xl border bg-card p-5 shadow-soft transition-all duration-200 hover:-translate-y-1 hover:border-primary/30 hover:shadow-lg">
                <div className={cn("absolute -right-10 -top-10 h-32 w-32 rounded-full bg-gradient-to-br opacity-10 blur-xl transition-opacity group-hover:opacity-25", f.gradient)} />
                <div className="relative flex items-start justify-between">
                  <span className={cn("flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow-md transition-transform group-hover:scale-105", f.gradient)}>
                    <f.icon className="h-6 w-6" />
                  </span>
                  <div className="flex items-center gap-2">
                    {f.badge && (
                      <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-bold tracking-wide text-emerald-600 dark:text-emerald-300">
                        {f.badge}
                      </span>
                    )}
                    <span className="font-display text-sm font-bold text-muted-foreground/40">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                  </div>
                </div>
                <h3 className="relative mt-4 text-lg font-semibold">{f.title}</h3>
                <p className="relative mt-1.5 flex-1 text-sm leading-relaxed text-muted-foreground">{f.desc}</p>
                <span className={cn("relative mt-4 inline-flex items-center gap-1.5 text-sm font-semibold", t.text)}>
                  Open tool <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

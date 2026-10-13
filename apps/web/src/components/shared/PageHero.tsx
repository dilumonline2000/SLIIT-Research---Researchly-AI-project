import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Colour themes follow the sidebar sections so every page in a section
 * shares the same visual identity.
 */
export type HeroTheme = "home" | "library" | "integrity" | "mentor" | "vault" | "insight" | "account";

export const HERO_THEMES: Record<
  HeroTheme,
  { gradient: string; glow: string; section: string; accent: string; soft: string; text: string }
> = {
  home:      { gradient: "from-indigo-600 via-violet-600 to-fuchsia-600", glow: "bg-cyan-400/20",    section: "Home Base",        accent: "from-indigo-500 to-fuchsia-500", soft: "bg-indigo-500/10",  text: "text-indigo-600 dark:text-indigo-300" },
  library:   { gradient: "from-indigo-600 via-violet-600 to-purple-600",  glow: "bg-fuchsia-400/25", section: "Research Library", accent: "from-indigo-500 to-violet-500",  soft: "bg-violet-500/10",  text: "text-violet-600 dark:text-violet-300" },
  integrity: { gradient: "from-blue-600 via-indigo-600 to-cyan-600",      glow: "bg-cyan-300/25",    section: "Integrity Lab",    accent: "from-blue-500 to-cyan-500",      soft: "bg-blue-500/10",    text: "text-blue-600 dark:text-blue-300" },
  mentor:    { gradient: "from-emerald-600 via-teal-600 to-cyan-600",     glow: "bg-cyan-300/20",    section: "Mentor Network",   accent: "from-emerald-500 to-teal-500",   soft: "bg-emerald-500/10", text: "text-emerald-600 dark:text-emerald-300" },
  vault:     { gradient: "from-amber-500 via-orange-500 to-rose-500",     glow: "bg-yellow-300/25",  section: "Knowledge Vault",  accent: "from-amber-500 to-orange-500",   soft: "bg-amber-500/10",   text: "text-amber-600 dark:text-amber-300" },
  insight:   { gradient: "from-purple-600 via-violet-600 to-fuchsia-600", glow: "bg-pink-400/25",    section: "Insight Studio",   accent: "from-purple-500 to-fuchsia-500", soft: "bg-purple-500/10",  text: "text-purple-600 dark:text-purple-300" },
  account:   { gradient: "from-slate-800 via-indigo-900 to-slate-900",    glow: "bg-indigo-400/25",  section: "Your Space",       accent: "from-slate-600 to-indigo-600",   soft: "bg-slate-500/10",   text: "text-slate-600 dark:text-slate-300" },
};

export interface HeroStat {
  label: string;
  value: ReactNode;
  icon?: LucideIcon;
}

interface PageHeroProps {
  theme: HeroTheme;
  icon: LucideIcon;
  title: ReactNode;
  description?: ReactNode;
  /** Small label above the title — defaults to the section name */
  eyebrow?: ReactNode;
  /** Buttons / links rendered on the right (stacked below on mobile) */
  actions?: ReactNode;
  stats?: HeroStat[];
  /** Extra content rendered inside the hero, below everything else */
  children?: ReactNode;
  className?: string;
}

export function PageHero({
  theme,
  icon: Icon,
  title,
  description,
  eyebrow,
  actions,
  stats,
  children,
  className,
}: PageHeroProps) {
  const t = HERO_THEMES[theme];
  return (
    <section
      className={cn(
        "relative overflow-hidden rounded-2xl bg-gradient-to-br p-5 text-white shadow-lg sm:p-7",
        t.gradient,
        className,
      )}
    >
      {/* Decorative glows + dotted texture */}
      <div className="pointer-events-none absolute -right-16 -top-20 h-72 w-72 rounded-full bg-white/10 blur-2xl" />
      <div className={cn("pointer-events-none absolute -bottom-24 left-1/4 h-60 w-60 rounded-full blur-3xl", t.glow)} />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage: "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
          backgroundSize: "22px 22px",
        }}
      />
      <Icon className="pointer-events-none absolute -bottom-6 -right-4 hidden h-40 w-40 text-white/10 sm:block" strokeWidth={1.25} />

      <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0 max-w-3xl">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-medium backdrop-blur-sm">
            <Icon className="h-3.5 w-3.5" /> {eyebrow ?? t.section}
          </span>
          <h1 className="mt-3 text-2xl font-bold leading-tight sm:text-3xl">{title}</h1>
          {description && (
            <div className="mt-2 text-sm leading-relaxed text-white/85 sm:text-[15px]">{description}</div>
          )}
        </div>
        {actions && (
          <div className="relative flex flex-col gap-2 sm:flex-row sm:flex-wrap lg:shrink-0 lg:justify-end">
            {actions}
          </div>
        )}
      </div>

      {stats && stats.length > 0 && (
        <div className="relative mt-5 grid grid-cols-2 gap-2 sm:flex sm:flex-wrap sm:gap-3">
          {stats.map((s) => (
            <div
              key={s.label}
              className="min-w-0 rounded-xl border border-white/20 bg-white/10 px-3 py-2.5 backdrop-blur-sm sm:min-w-[140px] sm:px-4"
            >
              <p className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-white/75">
                {s.icon && <s.icon className="h-3.5 w-3.5 shrink-0" />}
                <span className="truncate">{s.label}</span>
              </p>
              <p className="mt-0.5 truncate font-display text-xl font-bold tabular-nums sm:text-2xl">{s.value}</p>
            </div>
          ))}
        </div>
      )}

      {children && <div className="relative mt-5">{children}</div>}
    </section>
  );
}

/** Light/translucent button style for use inside a PageHero `actions` slot */
export const heroButtonPrimary =
  "inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-white px-4 text-sm font-semibold text-slate-900 shadow-md transition hover:bg-white/90 disabled:opacity-60";
export const heroButtonGhost =
  "inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-white/30 bg-white/10 px-4 text-sm font-semibold text-white backdrop-blur-sm transition hover:bg-white/20 disabled:opacity-60";

// ─── Segmented tabs ───────────────────────────────────────────────────────

export interface SegmentedTab<T extends string> {
  id: T;
  label: ReactNode;
  icon?: LucideIcon;
  disabled?: boolean;
}

export function SegmentedTabs<T extends string>({
  tabs,
  value,
  onChange,
  theme = "home",
  className,
}: {
  tabs: SegmentedTab<T>[];
  value: T;
  onChange: (id: T) => void;
  theme?: HeroTheme;
  className?: string;
}) {
  const t = HERO_THEMES[theme];
  return (
    <div
      role="tablist"
      className={cn(
        "no-scrollbar flex w-full gap-1 overflow-x-auto rounded-xl border bg-card p-1 shadow-soft sm:w-fit",
        className,
      )}
    >
      {tabs.map((tab) => {
        const active = tab.id === value;
        return (
          <button
            key={tab.id}
            role="tab"
            type="button"
            aria-selected={active}
            disabled={tab.disabled}
            onClick={() => onChange(tab.id)}
            className={cn(
              "flex flex-1 shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-lg px-4 py-2 text-sm font-medium transition-all disabled:opacity-50 sm:flex-none",
              active
                ? cn("bg-gradient-to-r text-white shadow-sm", t.accent)
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
            )}
          >
            {tab.icon && <tab.icon className="h-4 w-4" />}
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

// ─── Section heading (inside pages) ───────────────────────────────────────

export function SectionTitle({
  icon: Icon,
  title,
  description,
  theme = "home",
  action,
}: {
  icon?: LucideIcon;
  title: ReactNode;
  description?: ReactNode;
  theme?: HeroTheme;
  action?: ReactNode;
}) {
  const t = HERO_THEMES[theme];
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex items-start gap-3">
        {Icon && (
          <span className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow-sm", t.accent)}>
            <Icon className="h-4 w-4" />
          </span>
        )}
        <div>
          <h2 className="text-lg font-semibold leading-tight sm:text-xl">{title}</h2>
          {description && <p className="mt-0.5 text-sm text-muted-foreground">{description}</p>}
        </div>
      </div>
      {action}
    </div>
  );
}

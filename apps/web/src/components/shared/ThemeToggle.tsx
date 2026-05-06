"use client";

import { useEffect, useState } from "react";
import { Sun, Moon, Monitor } from "lucide-react";
import { useThemeStore, type Theme } from "@/stores/themeStore";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

const META: Record<Theme, { label: string; tooltip: string; Icon: typeof Sun }> = {
  light:  { label: "Light",  tooltip: "Light mode (click for Dark)",  Icon: Sun },
  dark:   { label: "Dark",   tooltip: "Dark mode (click for System)", Icon: Moon },
  system: { label: "System", tooltip: "System theme (click for Light)", Icon: Monitor },
};

interface Props {
  /** Compact (icon-only) — default for navbar. */
  compact?: boolean;
}

export function ThemeToggle({ compact = true }: Props) {
  const { theme, toggleTheme, applyTheme } = useThemeStore();
  // Avoid hydration mismatch — render a stable placeholder until mounted.
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
    applyTheme();
  }, [applyTheme]);

  if (!mounted) {
    return (
      <button
        aria-label="Theme toggle"
        className={cn(
          "flex items-center justify-center rounded-md border bg-background",
          compact ? "h-8 w-8" : "h-9 px-3",
        )}
        disabled
      >
        <Monitor className="h-4 w-4 text-muted-foreground" />
      </button>
    );
  }

  const { Icon, tooltip, label } = META[theme];

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            onClick={toggleTheme}
            aria-label={`Toggle theme — current: ${label}`}
            className={cn(
              "flex items-center gap-1.5 rounded-md border bg-background transition-colors",
              "hover:bg-accent hover:text-accent-foreground",
              theme === "dark" && "border-indigo-200 dark:border-indigo-800",
              theme === "light" && "border-amber-200",
              compact ? "h-8 w-8 justify-center" : "h-9 px-3 text-sm font-medium",
            )}
          >
            <Icon
              className={cn(
                "h-4 w-4 transition-transform",
                theme === "dark" && "text-indigo-500",
                theme === "light" && "text-amber-500",
                theme === "system" && "text-muted-foreground",
              )}
            />
            {!compact && <span>{label}</span>}
          </button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p className="text-xs font-medium">{tooltip}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

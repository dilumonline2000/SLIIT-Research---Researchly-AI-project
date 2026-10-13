"use client";

import { LogOut, Menu, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/useAuth";
// import { AIProviderToggle } from "./AIProviderToggle";
import { ThemeToggle } from "./ThemeToggle";

interface NavbarProps {
  onMenuClick?: () => void;
}

export function Navbar({ onMenuClick }: NavbarProps) {
  const { profile, signOut } = useAuth();

  const handleSignOut = async () => {
    if (window.confirm("Are you sure you want to sign out?")) {
      await signOut();
    }
  };

  return (
    <header className="glass sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between gap-3 border-b px-3 sm:px-6">
      {/* Left: hamburger (mobile only) + brand (mobile) + search */}
      <div className="flex min-w-0 flex-1 items-center gap-2">
        <button
          onClick={onMenuClick}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border bg-background hover:bg-accent md:hidden"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 via-violet-500 to-fuchsia-500 font-display text-sm font-bold text-white sm:hidden">
          R
        </span>
        <div className="relative w-full max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search papers, authors, topics…"
            className="h-10 rounded-full border-transparent bg-muted/70 pl-10 focus-visible:border-input focus-visible:bg-background"
          />
        </div>
      </div>

      {/* Right */}
      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        <ThemeToggle compact />
        {/* <AIProviderToggle compact={true} /> */}
        <div className="hidden text-right lg:block">
          <p className="text-sm font-semibold leading-tight">{profile?.full_name ?? "User"}</p>
          <p className="text-xs capitalize text-muted-foreground">
            {profile?.role ?? "student"}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleSignOut}
          title="Sign out"
          aria-label="Sign out"
          className="h-10 w-10 gap-2 border-rose-200 p-0 text-rose-600 hover:bg-rose-50 hover:text-rose-700 dark:border-rose-900/60 dark:text-rose-400 dark:hover:bg-rose-950/40 sm:h-9 sm:w-auto sm:px-3"
        >
          <LogOut className="h-4 w-4" />
          <span className="hidden sm:inline">Sign Out</span>
        </Button>
      </div>
    </header>
  );
}

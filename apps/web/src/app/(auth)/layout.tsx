import Link from "next/link";
import { APP_NAME } from "@/lib/constants";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative flex min-h-screen min-h-[100svh] items-center justify-center overflow-hidden bg-background px-4 py-10">
      {/* Soft decorative glow — works in both themes */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -right-32 -top-32 h-[420px] w-[420px] rounded-full bg-indigo-500/15 blur-[100px]" />
        <div className="absolute -bottom-32 -left-32 h-[380px] w-[380px] rounded-full bg-fuchsia-500/10 blur-[100px]" />
      </div>
      <div className="relative w-full max-w-md">
        <Link
          href="/"
          className="mb-8 flex items-center justify-center gap-2.5 font-display text-xl font-bold"
        >
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-violet-500 to-fuchsia-500 text-white shadow-glow">
            R
          </span>
          {APP_NAME}
        </Link>
        {children}
      </div>
    </div>
  );
}

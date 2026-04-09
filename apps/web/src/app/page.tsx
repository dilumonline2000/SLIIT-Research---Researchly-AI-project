import Link from "next/link";
import { ArrowRight, BookOpen, Users, Database, LineChart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { APP_NAME, MODULES } from "@/lib/constants";

const moduleIcons = {
  1: BookOpen,
  2: Users,
  3: Database,
  4: LineChart,
} as const;

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/30">
      {/* Nav */}
      <header className="border-b">
        <div className="container flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2 font-bold text-xl">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              R
            </span>
            {APP_NAME}
          </Link>
          <nav className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost">Sign in</Button>
            </Link>
            <Link href="/register">
              <Button>Get started</Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="container py-24 text-center">
        <div className="mx-auto max-w-3xl">
          <div className="mb-4 inline-flex items-center rounded-full border bg-card px-4 py-1 text-sm text-muted-foreground">
            R26-IT-116 · SLIIT Research Project
          </div>
          <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
            AI-powered research,{" "}
            <span className="bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">
              accelerated
            </span>
          </h1>
          <p className="mt-6 text-lg text-muted-foreground">
            Citation management, supervisor matching, research data pipelines, and
            predictive performance analytics — all powered by state-of-the-art NLP and
            deep learning.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link href="/register">
              <Button size="lg" className="gap-2">
                Start for free <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="#modules">
              <Button size="lg" variant="outline">
                Explore modules
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Modules grid */}
      <section id="modules" className="container py-16">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold">Four integrated modules</h2>
          <p className="mt-4 text-muted-foreground">
            Each module is a specialized AI system — trained on 15,000+ scraped
            research papers and tuned for academic workflows.
          </p>
        </div>
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {MODULES.map((mod) => {
            const Icon = moduleIcons[mod.id as keyof typeof moduleIcons];
            return (
              <Card key={mod.id} className="transition-shadow hover:shadow-lg">
                <CardHeader>
                  <div
                    className={`mb-3 flex h-10 w-10 items-center justify-center rounded-lg ${mod.color} text-white`}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <CardTitle className="text-lg">{mod.name}</CardTitle>
                  <CardDescription className="line-clamp-3">
                    {mod.description}
                  </CardDescription>
                  <p className="pt-2 text-xs text-muted-foreground">By {mod.owner}</p>
                </CardHeader>
              </Card>
            );
          })}
        </div>
      </section>

      <footer className="mt-16 border-t py-8">
        <div className="container text-center text-sm text-muted-foreground">
          © {new Date().getFullYear()} {APP_NAME} · SLIIT Final-Year Research Project
        </div>
      </footer>
    </div>
  );
}

"use client";

import Link from "next/link";
import Image from "next/image";
import { useState, useEffect, useRef } from "react";
import { motion, useInView, useScroll, useTransform } from "framer-motion";
import {
  ArrowRight, BookOpen, Users, Database, LineChart,
  Zap, Shield, Brain, TrendingUp, Star, ChevronDown, Play,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { APP_NAME, MODULES } from "@/lib/constants";

// ── Animation variants ─────────────────────────────────────────────────────
const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] as const } },
};
const fadeIn = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.6 } },
};
const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12 } },
};
const slideLeft = {
  hidden: { opacity: 0, x: -30 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] as const } },
};

// ── Animated stat counter ──────────────────────────────────────────────────
function AnimatedStat({ value, label, suffix = "" }: { value: number; label: string; suffix?: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true });

  useEffect(() => {
    if (!inView) return;
    const steps = 60;
    const increment = value / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= value) { setCount(value); clearInterval(timer); }
      else setCount(Math.floor(current));
    }, 20);
    return () => clearInterval(timer);
  }, [inView, value]);

  return (
    <div ref={ref} className="text-center">
      <div className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent tabular-nums">
        {count.toLocaleString()}{suffix}
      </div>
      <div className="mt-1.5 text-sm text-slate-400">{label}</div>
    </div>
  );
}

// ── Team data ──────────────────────────────────────────────────────────────
const TEAM = [
  {
    key: "kariyawasam",
    short: "Dilum Kariyawasam",
    full: "K D T Kariyawasam",
    role: "Module 1 — Research Integrity",
    description:
      "Full-stack AI engineer specializing in NLP-driven citation parsing, research gap detection, and LLM-powered proposal generation pipelines.",
    image: "/images/team/kariyawasam.jpg",
    gradient: "from-blue-500 to-cyan-400",
    initials: "DK",
    objectPosition: "object-top",
  },
  {
    key: "gunathilaka",
    short: "Upadya Gunathilaka",
    full: "S P U Gunathilaka",
    role: "Module 2 — Collaboration",
    description:
      "Software engineer building SBERT-powered supervisor matching systems and peer discovery algorithms for academic research networks.",
    image: "/images/team/gunathilaka.png",
    gradient: "from-emerald-500 to-teal-400",
    initials: "UG",
    objectPosition: "object-center",
  },
  {
    key: "hewamanne",
    short: "Navod Hewamanne",
    full: "N V Hewamanne",
    role: "Module 3 — Data Management",
    description:
      "Data engineer designing scalable research data pipelines, topic classification systems, and AI-powered extractive summarization.",
    image: "/images/team/hewamanne.jpg",
    gradient: "from-amber-500 to-orange-400",
    initials: "NH",
    objectPosition: "object-top",
  },
  {
    key: "jayasundara",
    short: "Sankalpana Jayasundara",
    full: "H W S S Jayasundara",
    role: "Module 4 — Performance Analytics",
    description:
      "ML engineer developing XGBoost success predictors, ARIMA trend forecasters, and multi-dimensional quality scoring for academic research.",
    image: "/images/team/jayasundara.jpg",
    gradient: "from-purple-500 to-violet-400",
    initials: "SJ",
    objectPosition: "object-top",
  },
];

// ── Module config ──────────────────────────────────────────────────────────
const moduleIcons = { 1: BookOpen, 2: Users, 3: Database, 4: LineChart } as const;
const moduleGradients: Record<number, string> = {
  1: "from-blue-500 to-cyan-500",
  2: "from-emerald-500 to-teal-500",
  3: "from-amber-500 to-orange-500",
  4: "from-purple-500 to-violet-500",
};

// ─────────────────────────────────────────────────────────────────────────────
export default function LandingPage() {
  const [scrolled, setScrolled] = useState(false);
  const [imgErrors, setImgErrors] = useState<Record<string, boolean>>({});
  const heroRef = useRef<HTMLElement>(null);
  const { scrollY } = useScroll();
  const heroOpacity = useTransform(scrollY, [0, 500], [1, 0]);
  const heroY = useTransform(scrollY, [0, 500], [0, -60]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="min-h-screen bg-[#060914] text-white overflow-x-hidden">

      {/* ── Navbar ─────────────────────────────────────────────────── */}
      <header
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled ? "bg-[#060914]/90 backdrop-blur-md border-b border-white/5 shadow-lg" : ""
        }`}
      >
        <div className="container flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 font-bold text-lg">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white text-sm font-bold shadow-lg shadow-blue-500/25">
              R
            </span>
            <span className="bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
              {APP_NAME}
            </span>
          </Link>
          <nav className="flex items-center gap-1">
            {[
              { href: "#video", label: "Demo" },
              { href: "#modules", label: "Modules" },
              { href: "#team", label: "Team" },
            ].map((item) => (
              <a key={item.href} href={item.href}>
                <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                  {item.label}
                </Button>
              </a>
            ))}
            <div className="mx-2 h-4 w-px bg-white/10" />
            <Link href="/login">
              <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white">
                Sign in
              </Button>
            </Link>
            <Link href="/register">
              <Button
                size="sm"
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 border-0 shadow-lg shadow-blue-500/20"
              >
                Get started
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* ── Hero ───────────────────────────────────────────────────── */}
      <section
        ref={heroRef}
        className="relative min-h-screen flex flex-col items-center justify-center pt-16 overflow-hidden"
      >
        {/* Animated blobs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-[600px] h-[600px] rounded-full bg-blue-600/20 blur-[120px] animate-blob" />
          <div className="absolute -bottom-40 -left-40 w-[500px] h-[500px] rounded-full bg-purple-600/20 blur-[120px] animate-blob animation-delay-2000" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] rounded-full bg-cyan-600/10 blur-[100px] animate-blob animation-delay-4000" />
          {/* Subtle grid */}
          <div
            className="absolute inset-0 opacity-[0.04]"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff'%3E%3Cpath d='M0 0h1v60H0zm59 0h1v60h-1zM0 0v1h60V0zm0 59v1h60v-1z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
            }}
          />
        </div>

        <motion.div
          style={{ opacity: heroOpacity, y: heroY }}
          className="relative z-10 container text-center max-w-5xl px-4"
        >
          <motion.div variants={stagger} initial="hidden" animate="visible" className="space-y-6">
            <motion.div variants={fadeIn}>
              <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-sm text-slate-300 backdrop-blur-sm">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                R26-IT-116 · SLIIT Final-Year Research Project
              </span>
            </motion.div>

            <motion.h1
              variants={fadeUp}
              className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1]"
            >
              AI-powered research,{" "}
              <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
                accelerated
              </span>
            </motion.h1>

            <motion.p
              variants={fadeUp}
              className="mx-auto max-w-2xl text-lg text-slate-400 leading-relaxed"
            >
              Citation intelligence, supervisor matching, research data pipelines, and predictive
              performance analytics — all powered by state-of-the-art NLP and deep learning.{" "}
              <span className="text-white font-medium">Built on 3,860+ SLIIT research papers.</span>
            </motion.p>

            <motion.div
              variants={fadeUp}
              className="flex flex-wrap items-center justify-center gap-4 pt-2"
            >
              <Link href="/register">
                <Button
                  size="lg"
                  className="gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 border-0 shadow-xl shadow-blue-500/25 text-base px-8 h-12"
                >
                  Start for free <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <a href="#video">
                <Button
                  size="lg"
                  variant="outline"
                  className="gap-2 border-white/10 bg-white/5 hover:bg-white/10 text-white text-base px-8 h-12 backdrop-blur-sm"
                >
                  <Play className="h-4 w-4 fill-current" /> Watch demo
                </Button>
              </a>
            </motion.div>

            {/* Feature badges */}
            <motion.div
              variants={fadeIn}
              className="flex flex-wrap items-center justify-center gap-3 pt-2"
            >
              {[
                { icon: Zap, text: "Real-time RAG" },
                { icon: Shield, text: "98% Accuracy" },
                { icon: Brain, text: "Gemini 2.5 Flash" },
                { icon: TrendingUp, text: "ARIMA Forecasting" },
              ].map(({ icon: Icon, text }) => (
                <span
                  key={text}
                  className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-400"
                >
                  <Icon className="h-3 w-3 text-blue-400" />
                  {text}
                </span>
              ))}
            </motion.div>
          </motion.div>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2.5, duration: 1 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1.5 text-slate-500"
        >
          <span className="text-xs">Scroll to explore</span>
          <ChevronDown className="h-4 w-4 animate-bounce" />
        </motion.div>
      </section>

      {/* ── Stats bar ──────────────────────────────────────────────── */}
      <section className="relative z-10 border-y border-white/5 bg-white/[0.02] backdrop-blur-sm">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={stagger}
          className="container py-12 grid grid-cols-2 md:grid-cols-4 gap-8"
        >
          <motion.div variants={fadeUp}><AnimatedStat value={3860} suffix="+" label="Research Papers" /></motion.div>
          <motion.div variants={fadeUp}><AnimatedStat value={84} label="Faculty Supervisors" /></motion.div>
          <motion.div variants={fadeUp}><AnimatedStat value={98} suffix="%" label="Prediction Accuracy" /></motion.div>
          <motion.div variants={fadeUp}><AnimatedStat value={4} label="AI Modules" /></motion.div>
        </motion.div>
      </section>

      {/* ── YouTube Video ──────────────────────────────────────────── */}
      <section id="video" className="relative py-24">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-blue-600/10 blur-[100px] rounded-full" />
        </div>
        <div className="container relative z-10">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
            className="text-center mb-12"
          >
            <motion.div variants={fadeUp}>
              <span className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1.5 text-sm text-blue-400 mb-4">
                <Play className="h-3.5 w-3.5 fill-current" /> Product Demo
              </span>
            </motion.div>
            <motion.h2 variants={fadeUp} className="text-3xl sm:text-4xl font-bold">
              See Researchly AI{" "}
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                in action
              </span>
            </motion.h2>
            <motion.p variants={fadeUp} className="mt-4 text-slate-400 max-w-xl mx-auto">
              Watch how Researchly AI transforms the academic research workflow — from paper
              discovery to supervisor matching and publication success prediction.
            </motion.p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 40, scale: 0.97 }}
            whileInView={{ opacity: 1, y: 0, scale: 1 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            className="relative mx-auto max-w-5xl"
          >
            {/* Glow */}
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-600/30 via-purple-600/30 to-cyan-600/30 rounded-2xl blur-lg" />
            {/* Video */}
            <div className="relative rounded-2xl overflow-hidden border border-white/10 bg-black shadow-2xl shadow-blue-500/10">
              <div className="relative w-full" style={{ paddingBottom: "56.25%" }}>
                <iframe
                  src="https://www.youtube.com/embed/7BuNPmz995Q?rel=0&modestbranding=1&color=white"
                  title="Researchly AI Demo"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                  className="absolute inset-0 w-full h-full"
                />
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Modules ────────────────────────────────────────────────── */}
      <section id="modules" className="py-24 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-blue-950/10 to-transparent pointer-events-none" />
        <div className="container relative z-10">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
            className="text-center mb-16"
          >
            <motion.div variants={fadeUp}>
              <span className="inline-flex items-center gap-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-4 py-1.5 text-sm text-purple-400 mb-4">
                <Zap className="h-3.5 w-3.5" /> Four integrated modules
              </span>
            </motion.div>
            <motion.h2 variants={fadeUp} className="text-3xl sm:text-4xl font-bold">
              Everything your research needs,{" "}
              <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
                in one place
              </span>
            </motion.h2>
            <motion.p variants={fadeUp} className="mt-4 text-slate-400 max-w-2xl mx-auto">
              Each module is a specialized AI system trained on 3,860 institutional research papers
              and tuned for academic workflows.
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-80px" }}
            variants={stagger}
            className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4"
          >
            {MODULES.map((mod) => {
              const Icon = moduleIcons[mod.id as keyof typeof moduleIcons];
              const gradient = moduleGradients[mod.id];
              return (
                <motion.div
                  key={mod.id}
                  variants={fadeUp}
                  whileHover={{ y: -6, scale: 1.02 }}
                  transition={{ type: "spring", stiffness: 300, damping: 20 }}
                  className="group relative rounded-2xl border border-white/8 bg-white/[0.03] p-6 backdrop-blur-sm hover:border-white/15 hover:bg-white/[0.06] transition-colors cursor-default"
                >
                  <div
                    className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-300`}
                  />
                  <div
                    className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${gradient} shadow-lg text-white`}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="text-xs font-medium text-slate-500">Module {mod.id}</span>
                  <h3 className="mt-1 text-base font-semibold text-white mb-2">{mod.name}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{mod.description}</p>
                  <div className="mt-4 pt-4 border-t border-white/5">
                    <p className="text-xs text-slate-500">
                      <span className="text-slate-400">By</span> {mod.owner}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>

          {/* Tech highlights */}
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            variants={stagger}
            className="mt-10 grid gap-4 sm:grid-cols-3"
          >
            {[
              { icon: Brain, title: "Gemini 2.5 Flash", desc: "State-of-the-art LLM powering RAG chat, proposal generation, and content synthesis." },
              { icon: TrendingUp, title: "XGBoost + ARIMA", desc: "98% accurate success prediction and trend forecasting across 7 research domains." },
              { icon: Shield, title: "Supabase pgvector", desc: "Sub-100ms semantic search over 3,860 pre-computed SBERT research paper embeddings." },
            ].map(({ icon: Icon, title, desc }) => (
              <motion.div
                key={title}
                variants={slideLeft}
                className="flex gap-4 rounded-xl border border-white/8 bg-white/[0.02] p-5"
              >
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-500/15">
                  <Icon className="h-4 w-4 text-blue-400" />
                </div>
                <div>
                  <p className="font-medium text-white text-sm">{title}</p>
                  <p className="mt-1 text-xs text-slate-400 leading-relaxed">{desc}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── Team ───────────────────────────────────────────────────── */}
      <section id="team" className="py-24 relative">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/4 w-[400px] h-[400px] bg-purple-600/8 blur-[100px] rounded-full" />
          <div className="absolute bottom-0 right-1/4 w-[300px] h-[300px] bg-blue-600/8 blur-[80px] rounded-full" />
        </div>
        <div className="container relative z-10">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={stagger}
            className="text-center mb-16"
          >
            <motion.div variants={fadeUp}>
              <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-1.5 text-sm text-emerald-400 mb-4">
                <Star className="h-3.5 w-3.5" /> Meet the team
              </span>
            </motion.div>
            <motion.h2 variants={fadeUp} className="text-3xl sm:text-4xl font-bold">
              Built by{" "}
              <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                SLIIT engineers
              </span>
            </motion.h2>
            <motion.p variants={fadeUp} className="mt-4 text-slate-400 max-w-xl mx-auto">
              A team of four final-year software engineering students dedicated to advancing
              academic research through artificial intelligence.
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-80px" }}
            variants={stagger}
            className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4"
          >
            {TEAM.map((member) => (
              <motion.div
                key={member.key}
                variants={fadeUp}
                whileHover={{ y: -5 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                className="group relative rounded-2xl border border-white/8 bg-white/[0.03] overflow-hidden hover:border-white/15 transition-colors"
              >
                {/* Photo */}
                <div className={`relative h-52 bg-gradient-to-br ${member.gradient} overflow-hidden`}>
                  {!imgErrors[member.key] ? (
                    <Image
                      src={member.image}
                      alt={member.short}
                      fill
                      className={`object-cover ${member.objectPosition} transition-transform duration-500 group-hover:scale-105`}
                      onError={() =>
                        setImgErrors((prev) => ({ ...prev, [member.key]: true }))
                      }
                    />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-5xl font-bold text-white/30">{member.initials}</span>
                    </div>
                  )}
                  <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-[#0a0d1a] to-transparent" />
                </div>

                {/* Info */}
                <div className="p-5">
                  <h3 className="font-semibold text-white text-base">{member.short}</h3>
                  <p
                    className={`text-xs font-medium mt-0.5 bg-gradient-to-r ${member.gradient} bg-clip-text text-transparent`}
                  >
                    {member.role}
                  </p>
                  <p className="mt-3 text-xs text-slate-400 leading-relaxed">{member.description}</p>
                  <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
                    <span className="text-xs text-slate-500">Software Engineer</span>
                    <span className="text-xs text-slate-600">SLIIT</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── CTA Banner ─────────────────────────────────────────────── */}
      <section className="py-20">
        <div className="container">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
            className="relative rounded-3xl overflow-hidden border border-white/10"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600/20 via-purple-600/20 to-cyan-600/20" />
            <div className="absolute inset-0 bg-[#060914]/60 backdrop-blur-sm" />
            <div className="relative z-10 py-16 px-8 text-center">
              <h2 className="text-3xl sm:text-4xl font-bold mb-4">
                Ready to accelerate your research?
              </h2>
              <p className="text-slate-300 mb-8 max-w-md mx-auto">
                Join SLIIT researchers using AI to discover supervisors, analyse papers,
                and predict publication success.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-4">
                <Link href="/register">
                  <Button
                    size="lg"
                    className="gap-2 bg-white text-slate-900 hover:bg-slate-100 font-semibold px-8 h-12"
                  >
                    Get started free <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link href="/login">
                  <Button
                    size="lg"
                    variant="ghost"
                    className="border border-white/30 text-white hover:bg-white/10 hover:text-white px-8 h-12"
                  >
                    Sign in
                  </Button>
                </Link>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────── */}
      <footer className="border-t border-white/5 py-10">
        <div className="container">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-md bg-gradient-to-br from-blue-500 to-purple-600 text-white text-xs font-bold">
                R
              </span>
              <span className="text-sm font-semibold text-slate-300">{APP_NAME}</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-slate-500">
              <a href="#modules" className="hover:text-slate-300 transition-colors">Modules</a>
              <a href="#team" className="hover:text-slate-300 transition-colors">Team</a>
              <Link href="/login" className="hover:text-slate-300 transition-colors">Sign in</Link>
            </div>
            <p className="text-sm text-slate-500">
              © 2026 {APP_NAME} · R26-IT-116 · SLIIT
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

"use client";

import Link from "next/link";
import { Users, UserCheck, MessageSquare, Gauge, ArrowRight } from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  {
    title: "Supervisor Matching",
    desc: "Find the best-fit supervisors based on your research interests using AI-powered semantic matching.",
    icon: UserCheck,
    href: "/collaboration/supervisor-match",
    color: "bg-emerald-500",
  },
  {
    title: "Peer Discovery",
    desc: "Connect with peers who share similar research interests or have complementary skills.",
    icon: Users,
    href: "/collaboration/peer-connect",
    color: "bg-teal-500",
  },
  {
    title: "Feedback Analysis",
    desc: "Analyze academic feedback with aspect-based sentiment analysis across methodology, writing, originality, and data analysis.",
    icon: MessageSquare,
    href: "/collaboration/feedback",
    color: "bg-green-500",
  },
  {
    title: "Effectiveness Scoring",
    desc: "Measure supervision effectiveness via completion rates, feedback sentiment, and student satisfaction.",
    icon: Gauge,
    href: "/collaboration/effectiveness",
    color: "bg-cyan-500",
  },
];

export default function CollaborationPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Collaboration & Recommendation</h1>
        <p className="text-muted-foreground">Module 2 · Owner: S P U Gunathilaka</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {features.map((f) => (
          <Link key={f.title} href={f.href}>
            <Card className="h-full transition-all hover:shadow-md hover:-translate-y-0.5 cursor-pointer">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${f.color} text-white`}>
                    <f.icon className="h-5 w-5" />
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
                <CardTitle className="pt-3 text-lg">{f.title}</CardTitle>
                <CardDescription>{f.desc}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

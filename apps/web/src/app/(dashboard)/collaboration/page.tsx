"use client";

import { Users, UserCheck, MessageSquare, Gauge, Handshake } from "lucide-react";
import { FeatureHub, type HubFeature } from "@/components/shared/FeatureHub";

const features: HubFeature[] = [
  {
    title: "Supervisor Matching",
    desc: "Find the best-fit supervisors based on your research interests using AI-powered semantic matching.",
    icon: UserCheck,
    href: "/collaboration/supervisor-match",
    gradient: "from-emerald-500 to-teal-500",
  },
  {
    title: "Peer Discovery",
    desc: "Connect with peers who share similar research interests or have complementary skills.",
    icon: Users,
    href: "/collaboration/peer-connect",
    gradient: "from-teal-500 to-cyan-500",
  },
  {
    title: "Feedback Analysis",
    desc: "Analyze academic feedback with aspect-based sentiment analysis across methodology, writing, originality, and data analysis.",
    icon: MessageSquare,
    href: "/collaboration/feedback",
    gradient: "from-green-500 to-emerald-500",
  },
  {
    title: "Effectiveness Scoring",
    desc: "Measure supervision effectiveness via completion rates, feedback sentiment, and student satisfaction.",
    icon: Gauge,
    href: "/collaboration/effectiveness",
    gradient: "from-cyan-500 to-sky-500",
  },
];

export default function CollaborationPage() {
  return (
    <FeatureHub
      theme="mentor"
      icon={Handshake}
      title="Collaboration & Recommendation"
      tagline="Find the right supervisor, build your research squad, and learn from verified feedback — all matched by AI."
      owner="S P U Gunathilaka"
      features={features}
      stats={[
        { label: "Supervisors", value: "84" },
        { label: "Matching", value: "SBERT" },
      ]}
    />
  );
}

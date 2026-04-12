export const APP_NAME = "Researchly AI";
export const APP_DESCRIPTION =
  "AI-Powered Research Paper Assistant & Collaboration Platform";

export const API_GATEWAY_URL =
  process.env.NEXT_PUBLIC_API_GATEWAY_URL || "http://localhost:3001";

export const API_ROUTES = {
  auth: {
    register: "/api/v1/auth/register",
    login: "/api/v1/auth/login",
    me: "/api/v1/auth/me",
  },
  module1: {
    parseCitation: "/api/v1/citations/parse",
    formatCitation: "/api/v1/citations/format",
    analyzeGaps: "/api/v1/gaps/analyze",
    generateProposal: "/api/v1/proposals/generate",
    checkPlagiarism: "/api/v1/plagiarism/check",
    generateMindMap: "/api/v1/mindmaps/generate",
  },
  module2: {
    matchSupervisors: "/api/v1/matching/supervisors",
    matchPeers: "/api/v1/matching/peers",
    analyzeFeedback: "/api/v1/feedback/analyze",
    effectiveness: (id: string) => `/api/v1/effectiveness/${id}`,
  },
  module3: {
    scrape: "/api/v1/data/scrape",
    scrapeStatus: (id: string) => `/api/v1/data/scrape/${id}`,
    categorize: "/api/v1/data/categorize",
    plagiarismTrends: "/api/v1/data/plagiarism-trends",
    summarize: "/api/v1/data/summarize",
    quality: "/api/v1/data/quality",
  },
  module4: {
    trends: "/api/v1/analytics/trends",
    qualityScore: "/api/v1/analytics/quality-score",
    dashboard: "/api/v1/analytics/dashboard",
    mindmap: "/api/v1/analytics/mindmap",
    predict: "/api/v1/analytics/predict",
  },
} as const;

export const MODULES = [
  {
    id: 1,
    slug: "citations",
    name: "Research Integrity",
    owner: "K D T Kariyawasam",
    description: "Citation parsing, gap analysis, proposal generation, plagiarism detection",
    color: "bg-blue-500",
  },
  {
    id: 2,
    slug: "collaboration",
    name: "Collaboration",
    owner: "S P U Gunathilaka",
    description: "Supervisor matching, peer recommendation, feedback sentiment",
    color: "bg-emerald-500",
  },
  {
    id: 3,
    slug: "data-management",
    name: "Data Management",
    owner: "N V Hewamanne",
    description: "Data pipeline, topic categorization, summarization",
    color: "bg-amber-500",
  },
  {
    id: 4,
    slug: "analytics",
    name: "Performance Analytics",
    owner: "H W S S Jayasundara",
    description: "Trend forecasting, quality scoring, success prediction",
    color: "bg-purple-500",
  },
] as const;

# 🤖 CLAUDE CODE — CHAT SYSTEM REFACTOR PROMPT
## R26-IT-116 | AI-Powered Research Paper Assistant Platform
### Gemini API — General Chat + Module-Specific Paper Chats

---

## 📌 CONTEXT — READ FIRST

You are working on the existing **R26-IT-116 monorepo** (Next.js 14 + Express.js + Supabase).

The current state:
- ✅ Gemini API is already connected and working
- ✅ There is an existing research paper chat feature (paper upload + chat)
- ✅ 4 modules exist: Module 1 (Integrity), Module 2 (Collaboration), Module 3 (Data Management), Module 4 (Analytics)
- ❌ The current chat is a single combined feature — needs to be split

**What needs to change:**

| Current State | Target State |
|---|---|
| One research paper chat | General-purpose chat (Gemini) in sidebar/navbar |
| Paper upload + chat combined | Paper upload + chat INSIDE each module separately |
| Single chat context | Each module has its own specialized AI assistant persona |

---

## 🗂️ FILE STRUCTURE CHANGES

### Files to CREATE (new):
```
apps/web/src/
├── components/
│   ├── chat/
│   │   ├── GeneralChat.tsx              # NEW — floating general chat widget
│   │   ├── GeneralChatWindow.tsx        # NEW — full chat window
│   │   ├── GeneralChatMessage.tsx       # NEW — message bubble component
│   │   ├── GeneralChatInput.tsx         # NEW — input bar
│   │   └── ChatFAB.tsx                  # NEW — floating action button to open chat
│   │
│   ├── module1/
│   │   └── IntegrityPaperChat.tsx       # NEW — paper upload + chat for Module 1
│   │
│   ├── module2/
│   │   └── SupervisorChat.tsx           # NEW — supervisor-style guidance chat
│   │
│   ├── module3/
│   │   └── DataInsightChat.tsx          # NEW — data analysis assistant chat
│   │
│   └── module4/
│       └── AnalyticsChat.tsx            # NEW — analytics interpretation chat
│
├── app/(dashboard)/
│   └── chat/
│       └── page.tsx                     # UPDATE — now general chat full page
│
├── hooks/
│   ├── useGeneralChat.ts                # NEW
│   └── useModuleChat.ts                 # NEW — shared hook for module chats
│
├── lib/
│   └── gemini.ts                        # UPDATE — add new chat modes/personas
│
└── stores/
    └── generalChatStore.ts              # NEW — zustand store for general chat
```

### Files to UPDATE (existing):
```
apps/web/src/
├── components/shared/
│   └── Sidebar.tsx                      # UPDATE — add general chat icon/button
│
├── app/(dashboard)/
│   ├── citations/page.tsx               # UPDATE — embed IntegrityPaperChat
│   ├── collaboration/page.tsx           # UPDATE — embed SupervisorChat
│   ├── data-management/page.tsx         # UPDATE — embed DataInsightChat
│   └── analytics/page.tsx              # UPDATE — embed AnalyticsChat
│
└── app/(dashboard)/chat/
    └── page.tsx                         # UPDATE — change to general purpose
```

### Files to DELETE or REFACTOR:
```
# The old combined research paper chat component
# Move its paper-upload logic into IntegrityPaperChat.tsx
# Keep the UI shell but repurpose it for general chat
```

---

## ⚙️ GEMINI API CONFIGURATION

The Gemini API is already connected. Add these new configurations to `lib/gemini.ts`:

```typescript
// lib/gemini.ts

import { GoogleGenerativeAI } from "@google/generative-ai";

const genAI = new GoogleGenerativeAI(process.env.NEXT_PUBLIC_GEMINI_API_KEY!);

// ─── CHAT PERSONAS ───────────────────────────────────────────────

export const CHAT_PERSONAS = {

  // 1. GENERAL CHAT — no restrictions, general purpose
  general: {
    model: "gemini-1.5-flash",
    systemInstruction: `You are a helpful AI assistant integrated into a 
    university research platform called ResearchAI (R26-IT-116). 
    You can answer any question — research-related or general.
    You have knowledge about academic research, computer science, 
    software engineering, and general topics.
    Be friendly, concise, and helpful. 
    If the user asks about research, guide them toward using the 
    platform's specific features (citations, collaboration, data, analytics).`,
    config: {
      maxOutputTokens: 2048,
      temperature: 0.7,
    }
  },

  // 2. MODULE 1 — Research Integrity Assistant (with paper context)
  integrity: {
    model: "gemini-1.5-pro",  // Pro for document understanding
    systemInstruction: `You are a Research Integrity Assistant specializing in:
    - Citation formatting and validation (APA 7th, IEEE)
    - Identifying research gaps in literature
    - Evaluating research proposals
    - Detecting potential plagiarism patterns
    - Research methodology guidance
    - Academic writing best practices
    
    When a research paper is uploaded, analyze it thoroughly and answer 
    questions specifically about that paper's content, citations, methodology, 
    and research gaps. Always reference specific sections and page numbers.
    
    Keep responses academic, precise, and constructive.`,
    config: {
      maxOutputTokens: 4096,
      temperature: 0.3,  // Lower temp for accuracy
    }
  },

  // 3. MODULE 2 — Supervisor Guidance Chat
  collaboration: {
    model: "gemini-1.5-flash",
    systemInstruction: `You are an experienced Academic Supervisor AI providing 
    mentorship and guidance to university research students.
    
    Your role is to:
    - Give constructive feedback on research ideas and proposals
    - Guide students on research methodology choices
    - Suggest potential research supervisors and explain why they match
    - Help students find collaboration opportunities with peers
    - Provide encouragement and actionable next steps
    - Simulate the kind of guidance a real supervisor would give
    - Ask clarifying questions to better understand the student's research goals
    
    Tone: Warm, professional, encouraging, mentorship-style.
    Always end with a specific actionable suggestion or question.`,
    config: {
      maxOutputTokens: 2048,
      temperature: 0.6,
    }
  },

  // 4. MODULE 3 — Data & Research Collection Assistant
  dataManagement: {
    model: "gemini-1.5-flash",
    systemInstruction: `You are a Research Data Management Assistant.
    
    You help users:
    - Understand how their uploaded research papers are categorized
    - Interpret topic classification results and confidence scores
    - Explain plagiarism similarity scores and what they mean
    - Summarize complex research papers in plain language
    - Guide users on improving data quality of their submissions
    - Answer questions about the research data pipeline
    - Explain BERTopic clusters and emerging research themes
    
    When paper data is provided in context, reference specific 
    categorization results, similarity scores, and summaries.
    Be data-driven and precise.`,
    config: {
      maxOutputTokens: 2048,
      temperature: 0.4,
    }
  },

  // 5. MODULE 4 — Analytics Interpretation Assistant
  analytics: {
    model: "gemini-1.5-flash",
    systemInstruction: `You are a Research Analytics Interpreter AI.
    
    You help users understand:
    - Research trend predictions and what they mean for their work
    - Quality scores and how to improve them
    - Success prediction results and risk factors
    - Dashboard metrics and KPIs
    - How to act on analytics insights
    - Forecasting methodology (ARIMA, Prophet ensemble)
    - What the mind map connections reveal about their research domain
    
    When analytics data is provided in context (scores, trends, predictions),
    interpret them clearly and suggest specific improvements.
    Be data-driven, insightful, and actionable.`,
    config: {
      maxOutputTokens: 2048,
      temperature: 0.4,
    }
  },
} as const;

export type ChatPersona = keyof typeof CHAT_PERSONAS;

// ─── GENERAL CHAT (no paper context) ──────────────────────────────

export async function startGeneralChatSession() {
  const persona = CHAT_PERSONAS.general;
  const model = genAI.getGenerativeModel({
    model: persona.model,
    systemInstruction: persona.systemInstruction,
  });
  return model.startChat({
    generationConfig: persona.config,
    history: [],
  });
}

// ─── MODULE CHAT (with optional paper/data context) ───────────────

export async function startModuleChatSession(
  persona: ChatPersona,
  contextData?: string  // JSON string of paper content, analytics data, etc.
) {
  const personaConfig = CHAT_PERSONAS[persona];
  const model = genAI.getGenerativeModel({
    model: personaConfig.model,
    systemInstruction: personaConfig.systemInstruction,
  });

  // If context data provided (e.g. paper content), inject as first message
  const history = contextData
    ? [
        {
          role: "user" as const,
          parts: [{ text: `Here is the context data for this session:\n\n${contextData}` }],
        },
        {
          role: "model" as const,
          parts: [{ text: "I've reviewed the provided context and I'm ready to help you with questions about it." }],
        },
      ]
    : [];

  return model.startChat({
    generationConfig: personaConfig.config,
    history,
  });
}

// ─── STREAMING HELPER ─────────────────────────────────────────────

export async function sendMessageStreaming(
  chat: any,
  message: string,
  onChunk: (chunk: string) => void,
  onDone: () => void
) {
  const result = await chat.sendMessageStream(message);
  for await (const chunk of result.stream) {
    const text = chunk.text();
    if (text) onChunk(text);
  }
  onDone();
}
```

---

## 🟣 COMPONENT 1: General Chat (Floating Widget + Full Page)

### `components/chat/ChatFAB.tsx`
```
WHAT IT IS:
  A floating action button (bottom-right of every dashboard page)
  that opens/closes the GeneralChat panel.

DESIGN:
  - Circular button, 56px, primary color
  - Icon: MessageSquare (lucide-react)
  - Unread badge if there are messages
  - Smooth slide-up animation when chat opens
  - Appears on ALL dashboard pages
  - Does NOT appear inside module-specific chat panels

BEHAVIOR:
  - Click → slides up GeneralChatWindow panel (400px wide, 600px tall)
  - Click again → collapses
  - Chat history persists while navigating between pages (zustand store)
  - "Open full page" link → navigates to /chat full page view
```

### `components/chat/GeneralChatWindow.tsx`
```
WHAT IT IS:
  The floating chat panel (not full page). Shows inside a card overlay.

LAYOUT:
  ┌─────────────────────────┐
  │ 🤖 ResearchAI Assistant  [⤢] [✕] │  ← header with expand + close
  ├─────────────────────────┤
  │                         │
  │   [message bubbles]     │  ← scrollable message area
  │                         │
  ├─────────────────────────┤
  │ [Type anything...] [➤]  │  ← input bar
  └─────────────────────────┘

FEATURES:
  - Streaming responses (text appears word by word)
  - Markdown rendering (bold, code blocks, lists)
  - "New Chat" button clears history
  - Shows suggested prompts on empty state:
    * "What can this platform do?"
    * "Help me find a research topic"
    * "Explain citation formatting"
    * "What are current AI research trends?"
  - Message timestamps
  - Copy button on assistant messages

GEMINI INTEGRATION:
  - Uses startGeneralChatSession() from lib/gemini.ts
  - Persona: 'general'
  - Full conversation history maintained in generalChatStore
  - Streaming via sendMessageStreaming()
```

### `app/(dashboard)/chat/page.tsx` — UPDATE THIS
```
UPDATE the existing chat page to be a FULL PAGE general chat.

LAYOUT (full page, not floating):
  ┌──────────────────────────────────────────────────────┐
  │  Sidebar  │           General Chat                    │
  │           │  ┌──────────────────────────────────┐    │
  │           │  │ 🤖 ResearchAI — General Assistant │    │
  │           │  ├──────────────────────────────────┤    │
  │           │  │                                  │    │
  │           │  │    [chat messages area]           │    │
  │           │  │                                  │    │
  │           │  ├──────────────────────────────────┤    │
  │           │  │ [Input bar with send button]      │    │
  │           │  └──────────────────────────────────┘    │
  │           │                                          │
  │           │  Suggested: "Research tips" "Explain X"  │
  └──────────────────────────────────────────────────────┘

KEY DIFFERENCE FROM FLOATING:
  - Full height, wider layout
  - Left panel shows chat history sessions list
  - Can start new sessions
  - All sessions saved to Supabase chat_sessions table
  - No paper upload here (general chat only)

IMPORTANT: Remove all research paper upload functionality 
from this page. It should be PURELY a general chat.
```

---

## 🔵 COMPONENT 2: Module 1 — IntegrityPaperChat

### `components/module1/IntegrityPaperChat.tsx`
```
WHAT IT IS:
  A self-contained panel inside the Research Integrity page (/citations)
  where users can upload a research paper and chat with it.
  This is where the OLD paper-chat functionality moves to.

LAYOUT:
  ┌──────────────────────────────────────────────────────┐
  │  📄 Research Paper Assistant                          │
  │  "Upload a paper and ask anything about it"           │
  ├─────────────────┬────────────────────────────────────┤
  │                 │                                    │
  │  UPLOAD PANEL   │         CHAT PANEL                 │
  │                 │                                    │
  │  [Drop PDF here]│  ┌──────────────────────────────┐  │
  │  or click to    │  │ ← No paper uploaded yet       │  │
  │  browse         │  │   Upload a PDF to start      │  │
  │                 │  │   chatting about it           │  │
  │  ── or ──       │  └──────────────────────────────┘  │
  │                 │                                    │
  │  Select from    │  Once paper uploaded:              │
  │  your library   │  ┌──────────────────────────────┐  │
  │  [paper list]   │  │ 🤖 I've analyzed your paper.  │  │
  │                 │  │ Ask me anything about it...   │  │
  │                 │  │                              │  │
  │                 │  │ You: What is the methodology? │  │
  │                 │  │ 🤖 The paper uses...          │  │
  │                 │  ├──────────────────────────────┤  │
  │                 │  │ [Ask about this paper...]  ➤ │  │
  │                 │  └──────────────────────────────┘  │
  └─────────────────┴────────────────────────────────────┘

HOW IT WORKS:
  1. User uploads PDF → extract text using existing pdf_processor
  2. Extracted text passed as contextData to startModuleChatSession('integrity', paperText)
  3. Gemini gets paper content in context via history injection
  4. User asks questions → Gemini answers based on paper content
  5. Suggested questions appear after upload:
     - "What is the main research problem?"
     - "Summarize the methodology"
     - "What are the key findings?"
     - "Are there any research gaps mentioned?"
     - "List all citations in this paper"
     - "How can I improve this proposal?"

PAPER TEXT EXTRACTION (client-side for speed):
  - Use pdf-parse or pdfjs-dist npm package
  - Extract text directly in browser (no server roundtrip for basic extraction)
  - For large papers (>50 pages): truncate to first 30,000 chars + abstract
  - Show "Analyzing paper..." loading state while processing

GEMINI PERSONA: 'integrity'
  - Knows about citations, research gaps, methodology
  - References specific sections when answering
  - Suggests improvements to research proposals

PLACEMENT IN PAGE:
  - Add as a collapsible panel at the BOTTOM of /citations page
  - OR as a dedicated tab within the citations page
  - Show as "📄 Chat with a Paper" tab alongside existing tools
```

---

## 🟢 COMPONENT 3: Module 2 — SupervisorChat

### `components/module2/SupervisorChat.tsx`
```
WHAT IT IS:
  A supervisor-style guidance chat inside the Collaboration page (/collaboration)
  No paper upload needed. Pure conversational guidance.

CONCEPT:
  Simulates having a conversation with an academic supervisor.
  Students can get guidance on research direction, proposal feedback,
  supervisor selection advice, collaboration strategies.

LAYOUT:
  ┌──────────────────────────────────────────────────────┐
  │  👨‍🏫 Supervisor Guidance Chat                          │
  │  "Get mentorship-style guidance for your research"    │
  ├──────────────────────────────────────────────────────┤
  │                                                      │
  │  [Message bubbles — supervisor style]                 │
  │                                                      │
  │  🤖: Hello! I'm your AI research advisor. What are   │
  │      you working on today? Tell me about your         │
  │      research topic or any challenges you're facing.  │
  │                                                      │
  ├──────────────────────────────────────────────────────┤
  │  Quick prompts:                                       │
  │  [Review my proposal] [Find a supervisor] [Help with  │
  │   methodology] [Collaboration advice]                 │
  ├──────────────────────────────────────────────────────┤
  │  [Ask your supervisor AI...]                    [➤]  │
  └──────────────────────────────────────────────────────┘

SUGGESTED QUICK PROMPTS (shown as chips above input):
  - "Review my research proposal idea"
  - "Help me choose between two research topics"
  - "How do I find the right supervisor for my topic?"
  - "What makes a strong research methodology?"
  - "Give me feedback on my research question"
  - "How should I structure my literature review?"

SPECIAL FEATURE — Proposal Text Input:
  - "Paste your proposal" expandable area
  - Student pastes their proposal text
  - Gemini reviews it and gives structured feedback
  - Feedback format: Strengths / Weaknesses / Suggestions

GEMINI PERSONA: 'collaboration'
  - Warm, encouraging, mentorship tone
  - Asks follow-up questions
  - Ends every response with an actionable suggestion

PLACEMENT:
  - Right panel of /collaboration page
  - OR as a prominent card with "Chat with your AI Supervisor" CTA
  - Always visible without needing to upload anything
  
NO PAPER UPLOAD IN THIS COMPONENT.
```

---

## 🟠 COMPONENT 4: Module 3 — DataInsightChat

### `components/module3/DataInsightChat.tsx`
```
WHAT IT IS:
  A data-aware chat inside the Data Management page (/data-management)
  Helps users understand their categorization results, similarity scores,
  and summaries. Can also answer general data/research questions.

CONCEPT:
  When a user has processed papers in Module 3, this chat can explain
  what the results mean and suggest what to do with them.

LAYOUT:
  ┌──────────────────────────────────────────────────────┐
  │  📊 Data Insights Assistant                           │
  │  "Understand your research data"                      │
  ├──────────────────────────────────────────────────────┤
  │  Context (auto-loaded if data available):             │
  │  ✅ 1,247 papers processed  |  📂 12 topic categories │
  │  📈 Latest plagiarism trend: Stable                   │
  ├──────────────────────────────────────────────────────┤
  │  [Chat messages]                                      │
  ├──────────────────────────────────────────────────────┤
  │  Suggested:                                           │
  │  [Explain my topic scores] [What is my main topic?]   │
  │  [Is my similarity score high?] [Summarize this paper]│
  ├──────────────────────────────────────────────────────┤
  │  [Ask about your data...]                       [➤]  │
  └──────────────────────────────────────────────────────┘

AUTO-CONTEXT INJECTION:
  When user opens this chat, automatically inject current module 3 
  data as context (if available):
  
  ```typescript
  const contextData = JSON.stringify({
    totalPapers: stats.total,
    topicDistribution: stats.topics,        // {AI: 34%, IoT: 18%, ...}
    recentPlagiarismTrend: trends.latest,
    userPapers: userPapers.slice(0, 5),     // Last 5 uploaded papers
    qualityStats: stats.quality
  });
  // Pass to startModuleChatSession('dataManagement', contextData)
  ```

SUGGESTED QUESTIONS:
  - "What is the most common topic in my uploaded papers?"
  - "Explain my plagiarism similarity score"
  - "Summarize my latest uploaded paper"
  - "Are there any emerging research themes in my data?"
  - "Which of my papers has the highest quality score?"
  - "What topics should I focus on based on current trends?"

PAPER UPLOAD (lightweight version):
  - Simple upload button: "Upload paper for instant summary"
  - Extracts text → sends to Gemini for summarization
  - Returns short summary (not full Q&A like Module 1)
  - Shorter, simpler than IntegrityPaperChat

GEMINI PERSONA: 'dataManagement'
  - Data-driven, precise
  - References actual numbers and percentages
  - Explains ML concepts (BERTopic, SciBERT) in plain language

PLACEMENT:
  - Collapsible side panel or bottom panel on /data-management page
```

---

## 🔴 COMPONENT 5: Module 4 — AnalyticsChat

### `components/module4/AnalyticsChat.tsx`
```
WHAT IT IS:
  An analytics interpretation chat inside the Analytics page (/analytics)
  Helps users understand trend predictions, quality scores, 
  success predictions, and dashboard metrics.

CONCEPT:
  The dashboard shows numbers and charts — this chat EXPLAINS them
  and tells the user what actions to take.

LAYOUT:
  ┌──────────────────────────────────────────────────────┐
  │  📈 Analytics Interpreter                             │
  │  "Understand your research performance"               │
  ├──────────────────────────────────────────────────────┤
  │  Your snapshot:                                       │
  │  Quality Score: 72/100 | Risk: Medium | Trend: ↑ AI  │
  ├──────────────────────────────────────────────────────┤
  │  [Chat messages]                                      │
  │                                                      │
  │  🤖: Your quality score of 72 is good but there's    │
  │      room to improve. Your methodology section        │
  │      scored lowest (58). Want tips on improving it?  │
  │                                                      │
  ├──────────────────────────────────────────────────────┤
  │  [What does my quality score mean?] [How to improve] │
  │  [Explain risk prediction] [Which trend to follow?]   │
  ├──────────────────────────────────────────────────────┤
  │  [Ask about your analytics...]                  [➤]  │
  └──────────────────────────────────────────────────────┘

AUTO-CONTEXT INJECTION:
  Automatically loads current user's analytics data as context:
  
  ```typescript
  const contextData = JSON.stringify({
    qualityScore: {
      overall: 72,
      breakdown: { originality: 68, citations: 75, methodology: 58, clarity: 80 }
    },
    successPrediction: {
      probability: 0.64,
      riskLevel: "medium",
      topRiskFactors: ["Low milestone completion", "Infrequent commits"]
    },
    trendForecasts: [
      { topic: "AI/ML", direction: "rising", confidence: 0.87 },
      { topic: "IoT", direction: "stable", confidence: 0.71 }
    ],
    mindMapTopConcepts: ["Neural Networks", "NLP", "Computer Vision"]
  });
  // Pass to startModuleChatSession('analytics', contextData)
  ```

PROACTIVE INSIGHTS (shown without user asking):
  On chat open, Gemini automatically generates 2-3 insights:
  "Based on your current data, here are 3 things to focus on:
   1. Your methodology score (58) is dragging down your overall quality...
   2. The AI/ML trend is rising — your topic is well-aligned...
   3. Medium risk detected: you have 3 incomplete milestones..."

SUGGESTED QUESTIONS:
  - "How can I improve my quality score?"
  - "What does my risk level mean?"
  - "Which research trends should I follow?"
  - "Explain my mind map connections"
  - "Am I on track to complete my research on time?"
  - "What actions should I take this week?"

GEMINI PERSONA: 'analytics'
  - Interprets numbers clearly
  - Always gives actionable advice, not just descriptions
  - Uses the user's actual scores in responses

PLACEMENT:
  - "AI Insights" panel inside /analytics page
  - Positioned next to the main dashboard charts
```

---

## 🗄️ DATABASE — New Tables Needed

```sql
-- General chat sessions (for the global chat)
CREATE TABLE public.general_chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT,                           -- Auto-generated from first message
    message_count INTEGER DEFAULT 0,
    last_message_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- General chat messages
CREATE TABLE public.general_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES public.general_chat_sessions(id) ON DELETE CASCADE,
    role TEXT CHECK (role IN ('user', 'assistant')) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Module chat messages (for all 4 module chats)
-- Note: paper_chat_messages from previous implementation covers Module 1
-- Add module_context column to differentiate
CREATE TABLE public.module_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    module TEXT CHECK (module IN (
        'integrity',        -- Module 1
        'collaboration',    -- Module 2  
        'data_management',  -- Module 3
        'analytics'         -- Module 4
    )) NOT NULL,
    role TEXT CHECK (role IN ('user', 'assistant')) NOT NULL,
    content TEXT NOT NULL,
    context_data JSONB,     -- What data was injected as context
    paper_id UUID,          -- If Module 1 chat (linked to uploaded paper)
    session_ref TEXT,       -- Group messages by session
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS
ALTER TABLE public.general_chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.general_chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.module_chat_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "own_general_sessions" ON public.general_chat_sessions
    FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "own_general_messages" ON public.general_chat_messages
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.general_chat_sessions 
                WHERE id = session_id AND user_id = auth.uid())
    );
CREATE POLICY "own_module_messages" ON public.module_chat_messages
    FOR ALL USING (auth.uid() = user_id);

-- Indexes
CREATE INDEX idx_general_sessions_user ON public.general_chat_sessions(user_id);
CREATE INDEX idx_general_messages_session ON public.general_chat_messages(session_id);
CREATE INDEX idx_module_messages_user_module ON public.module_chat_messages(user_id, module);
```

---

## 🔗 API ROUTES — New Endpoints

```
Add to apps/api-gateway/src/routes/:

# General Chat
POST   /api/v1/chat/general/session          # Create new general chat session
GET    /api/v1/chat/general/sessions         # List user's sessions
GET    /api/v1/chat/general/sessions/:id     # Get session + messages
POST   /api/v1/chat/general/message          # Send message (streaming SSE)
DELETE /api/v1/chat/general/sessions/:id     # Delete session

# Module Chats (all saved to module_chat_messages)
POST   /api/v1/chat/module/:module/message   # module = integrity|collaboration|data_management|analytics
GET    /api/v1/chat/module/:module/history   # Get recent messages for this module
```

**Note:** Gemini API calls happen DIRECTLY from the frontend (client-side) using the existing Gemini API key setup. The backend routes above are only for saving messages to Supabase. This avoids unnecessary server roundtrips for streaming.

---

## 🎨 UI / UX GUIDELINES

### General Chat Widget (FAB):
- Position: `fixed bottom-6 right-6 z-50`
- Button: `rounded-full w-14 h-14 bg-primary shadow-lg`
- Chat panel: `fixed bottom-24 right-6 w-96 h-[600px] bg-background rounded-2xl shadow-2xl border`
- Animation: `animate-in slide-in-from-bottom-4 duration-200`

### Module Chat Panels:
- Each module chat should feel **native to that module's UI**
- Use the same color accent as the module:
  - Module 1 (Integrity): Blue
  - Module 2 (Collaboration): Green  
  - Module 3 (Data): Orange
  - Module 4 (Analytics): Purple
- Show as a collapsible panel with a "Chat" tab or side drawer
- Default: collapsed (don't take over the main UI)
- Expand button: `"💬 AI Assistant"` button in the module header

### Message Bubbles:
```
User messages: right-aligned, primary color background, white text
AI messages: left-aligned, muted background, with small AI avatar icon
Streaming: show cursor blinking while text streams in
Code blocks: syntax highlighted with copy button
Links: underlined, open in new tab
```

### Empty States:
Each module chat should have a helpful empty state with:
- Module-specific icon
- Tagline (e.g., "Ask me about your research paper")
- 3-4 suggested question chips to click

---

## 📋 IMPLEMENTATION STEPS (Do in this order)

```
STEP 1: Update lib/gemini.ts
  - Add CHAT_PERSONAS object
  - Add startGeneralChatSession()
  - Add startModuleChatSession()
  - Add sendMessageStreaming()
  - Keep existing Gemini config intact

STEP 2: Create Database Tables
  - Run Supabase migrations for 3 new tables
  - Add RLS policies
  - Add indexes

STEP 3: Build GeneralChat components
  - ChatFAB.tsx (floating button)
  - GeneralChatWindow.tsx (floating panel)
  - GeneralChatInput.tsx
  - GeneralChatMessage.tsx
  - generalChatStore.ts (zustand)
  - useGeneralChat.ts hook

STEP 4: Update /chat full page
  - Remove paper upload from this page
  - Make it purely general conversation
  - Add session history sidebar

STEP 5: Add ChatFAB to dashboard layout
  - Import ChatFAB in app/(dashboard)/layout.tsx
  - Appears on all dashboard pages

STEP 6: Build Module 1 — IntegrityPaperChat
  - Move old paper-upload-chat logic here
  - Add to /citations page as a tab or panel

STEP 7: Build Module 2 — SupervisorChat
  - Pure conversational, no upload
  - Add to /collaboration page

STEP 8: Build Module 3 — DataInsightChat
  - Auto-inject module 3 stats as context
  - Add to /data-management page

STEP 9: Build Module 4 — AnalyticsChat
  - Auto-inject user's analytics data as context
  - Add proactive insights on open
  - Add to /analytics page

STEP 10: Connect API routes
  - Message saving endpoints
  - Session management

STEP 11: Remove/cleanup old code
  - Delete or repurpose old combined chat component
  - Ensure no broken imports
```

---

## ⚠️ CRITICAL RULES

1. **Gemini API key stays on frontend** (`NEXT_PUBLIC_GEMINI_API_KEY`) — already working, don't move it to backend
2. **Streaming must work** — use `sendMessageStream()` not `sendMessage()` for all chats
3. **Each module chat is independent** — Module 1 chat knows nothing about Module 4 data unless explicitly passed
4. **General chat has NO system restrictions** — users can ask anything (research or not)
5. **Module chats are persona-specific** — Module 2 chat always acts as supervisor, Module 4 always as analytics interpreter
6. **Paper upload ONLY in Module 1 chat** — not in Module 2, 3, or 4 chats
7. **Auto-context in Module 3 & 4** — automatically inject relevant data without user having to do anything
8. **Don't break existing functionality** — paper processing pipeline from before stays intact
9. **Chat history saved to Supabase** — all messages persist across page refreshes
10. **Mobile responsive** — all chat components must work on mobile screens
```

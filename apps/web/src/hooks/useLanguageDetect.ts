"use client";

import { useState, useCallback } from "react";
import { apiPost } from "@/lib/api";
import { API_ROUTES } from "@/lib/constants";

export interface DetectResult {
  language: string;
  confidence: number;
  is_singlish: boolean;
}

const SINHALA_RE = /[\u0D80-\u0DFF]/;
const TAMIL_RE = /[\u0B80-\u0BFF]/;
const SINGLISH_TRIGGERS = new Set([
  "eka",
  "meka",
  "gana",
  "kiyanna",
  "karanawa",
  "karanna",
  "mokakda",
  "kohomada",
  "tiyenawa",
  "puluwan",
]);

function quickDetect(text: string): DetectResult {
  if (SINHALA_RE.test(text)) return { language: "si", confidence: 1, is_singlish: false };
  if (TAMIL_RE.test(text)) return { language: "ta", confidence: 1, is_singlish: false };
  const tokens = (text.toLowerCase().match(/[a-z']+/g) || []).filter((t) =>
    SINGLISH_TRIGGERS.has(t),
  );
  if (tokens.length > 0)
    return { language: "singlish", confidence: 0.8, is_singlish: true };
  return { language: "en", confidence: 0.6, is_singlish: false };
}

export function useLanguageDetect() {
  const [result, setResult] = useState<DetectResult | null>(null);

  const detectLocal = useCallback((text: string) => {
    const r = quickDetect(text);
    setResult(r);
    return r;
  }, []);

  const detectRemote = useCallback(async (text: string) => {
    const r = await apiPost<DetectResult>(API_ROUTES.language.detect, { text });
    setResult(r);
    return r;
  }, []);

  return { result, detectLocal, detectRemote };
}

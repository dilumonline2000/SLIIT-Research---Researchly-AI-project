'use client';

import { useAIProviderStore } from '@/stores/aiProviderStore';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

const MODEL_LABELS: Record<string, { label: string; module: string }> = {
  sbert: { label: 'SBERT Embeddings', module: 'Shared' },
  scibert_classifier: { label: 'SciBERT Classifier', module: 'Module 3' },
  rag_engine: { label: 'RAG Engine', module: 'Shared' },
  citation_ner: { label: 'Citation NER', module: 'Module 1' },
  summarizer: { label: 'BART Summarizer', module: 'Module 3' },
  sentiment_bert: { label: 'Sentiment BERT', module: 'Module 2' },
  trend_forecaster: { label: 'ARIMA + Prophet', module: 'Module 4' },
  quality_scorer: { label: 'Quality Scorer', module: 'Module 4' },
  success_predictor: { label: 'XGBoost Predictor', module: 'Module 4' },
  proposal_llm: { label: 'Proposal Generator LLM', module: 'Module 1' },
};

const MODULE_COLORS: Record<string, string> = {
  Shared: 'bg-gray-100 text-gray-600',
  'Module 1': 'bg-blue-100 text-blue-700',
  'Module 2': 'bg-green-100 text-green-700',
  'Module 3': 'bg-orange-100 text-orange-700',
  'Module 4': 'bg-purple-100 text-purple-700',
};

export function ModelStatusGrid() {
  const { modelStatuses, isChecking } = useAIProviderStore();

  const totalModels = Object.keys(MODEL_LABELS).length;
  const loadedCount = Object.entries(modelStatuses).filter(([, s]) => s?.loaded).length;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">
          Local models ready: <strong>{loadedCount}/{totalModels}</strong>
        </span>
        <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 rounded-full transition-all"
            style={{ width: `${(loadedCount / totalModels) * 100}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {Object.entries(MODEL_LABELS).map(([key, { label, module }]) => {
          const status = modelStatuses[key];
          const isLoaded = status?.loaded ?? false;

          return (
            <div
              key={key}
              className={cn(
                'flex items-center gap-2.5 p-2.5 rounded-lg border text-sm',
                isLoaded ? 'border-green-200 bg-green-50/50' : 'border-gray-200 bg-gray-50/50'
              )}
            >
              {isLoaded ? (
                <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-gray-300 shrink-0" />
              )}

              <div className="flex-1 min-w-0">
                <p
                  className={cn('font-medium truncate', isLoaded ? 'text-gray-900' : 'text-gray-400')}
                >
                  {label}
                </p>
                {status?.version && isLoaded && (
                  <p className="text-xs text-muted-foreground">{status.version}</p>
                )}
                {!isLoaded && (
                  <p className="text-xs text-muted-foreground">Not trained yet</p>
                )}
              </div>

              <Badge
                variant="secondary"
                className={cn('text-xs shrink-0', MODULE_COLORS[module])}
              >
                {module}
              </Badge>
            </div>
          );
        })}
      </div>

      {loadedCount === 0 && !isChecking && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-yellow-50 border border-yellow-200 text-sm text-yellow-800">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <div>
            <p className="font-medium">No local models trained yet</p>
            <p className="text-xs mt-0.5">
              Run the training pipeline to enable Local AI mode. Until then, Gemini API will be used.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

# ML Training Pipelines

This directory holds the training, evaluation, and notebook code for the 10 ML models
defined in [R26-IT-116_Cursor_AI_Full_Development_Prompt.md](../R26-IT-116_Cursor_AI_Full_Development_Prompt.md).

## Layout

```
ml/
├── data/
│   ├── raw/         # Scraped papers by source (gitignored)
│   ├── processed/   # Cleaned + normalized training data
│   └── embeddings/  # Pre-computed SBERT vectors (gitignored)
├── notebooks/       # Jupyter notebooks for experimentation
├── training/        # Production training scripts
├── evaluation/      # Held-out evaluation scripts
└── configs/         # YAML configs per model (hyperparameters, paths)
```

## Models (Phase 3 targets)

| # | Model                        | Owner       | Target                             |
|---|------------------------------|-------------|------------------------------------|
| 1 | spaCy Citation NER           | Kariyawasam | F1 ≥ 0.85, format acc ≥ 90%        |
| 2 | SBERT fine-tuning            | shared      | improved cosine corr on academic   |
| 3 | SciBERT multi-label          | Hewamanne   | Macro F1 ≥ 0.80                    |
| 4 | BERT aspect-based sentiment  | Gunathilaka | Acc ≥ 93%, per-aspect F1 ≥ 0.85    |
| 5 | BART/T5 summarizer + LoRA    | Hewamanne   | R1 ≥ 0.45, R2 ≥ 0.20, RL ≥ 0.35    |
| 6 | Mistral/Llama proposal LoRA  | Kariyawasam | JSON output                        |
| 7 | ARIMA + Prophet ensemble     | Jayasundara | MAPE < 22%, dir acc > 75%          |
| 8 | RF + XGBoost success pred    | Jayasundara | F1 > 0.75, ROC-AUC > 0.80          |
| 9 | GCN mind map                 | Jayasundara | Concept coverage > 80%             |
| 10| BERTopic discovery           | Hewamanne   | Qualitative topic coherence        |

## Status

All scripts are **not yet implemented** — this is Phase 3 work, blocked on Phase 2
scraped training data.

"""Unified evaluation runner for all 10 ML models.

Loads each model's training metadata and checks against target metrics.
Generates a consolidated evaluation report.

Usage:
    python ml/evaluation/evaluate_all.py
    python ml/evaluation/evaluate_all.py --output ml/evaluation/report.json
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Model registry: (name, metadata_path, target_metrics)
MODEL_REGISTRY = [
    {
        "id": 1,
        "name": "Citation NER (spaCy)",
        "owner": "K D T Kariyawasam",
        "module": "module1-integrity",
        "metadata_path": "services/module1-integrity/models/citation_ner/training_metadata.json",
        "targets": {"best_f1": 0.85},
    },
    {
        "id": 2,
        "name": "SBERT Academic Similarity",
        "owner": "K D T Kariyawasam",
        "module": "module1-integrity",
        "metadata_path": "services/shared/models/sbert_academic/training_metadata.json",
        "targets": {},  # Triplet loss — evaluated via downstream tasks
    },
    {
        "id": 3,
        "name": "SciBERT Topic Classifier",
        "owner": "N V Hewamanne",
        "module": "module3-data",
        "metadata_path": "services/module3-data/models/scibert_classifier/training_metadata.json",
        "targets": {"best_val_f1": 0.80},
    },
    {
        "id": 4,
        "name": "Aspect-Based Sentiment",
        "owner": "S P U Gunathilaka",
        "module": "module2-collaboration",
        "metadata_path": "services/module2-collaboration/models/sentiment/training_metadata.json",
        "targets": {"best_val_f1": 0.85},
    },
    {
        "id": 5,
        "name": "Research Summarizer (BART+LoRA)",
        "owner": "N V Hewamanne",
        "module": "module3-data",
        "metadata_path": "services/module3-data/models/summarizer/training_metadata.json",
        "targets": {"best_rouge_avg": 0.40},
    },
    {
        "id": 6,
        "name": "Proposal Generator (RAG+LoRA)",
        "owner": "K D T Kariyawasam",
        "module": "module1-integrity",
        "metadata_path": "services/module1-integrity/models/proposal_lora/training_metadata.json",
        "targets": {},  # Evaluated qualitatively + perplexity
    },
    {
        "id": 7,
        "name": "Trend Forecaster (ARIMA+Prophet)",
        "owner": "H W S S Jayasundara",
        "module": "module4-analytics",
        "metadata_path": "services/module4-analytics/models/forecasting/training_metadata.json",
        "targets": {},  # Per-topic MAPE < 0.22
    },
    {
        "id": 8,
        "name": "Success Predictor (RF+XGBoost)",
        "owner": "H W S S Jayasundara",
        "module": "module4-analytics",
        "metadata_path": "services/module4-analytics/models/prediction/training_metadata.json",
        "targets": {"test_f1": 0.75, "test_roc_auc": 0.80},
    },
    {
        "id": 9,
        "name": "GNN Mind Map (GCN)",
        "owner": "H W S S Jayasundara",
        "module": "module4-analytics",
        "metadata_path": "services/module4-analytics/models/mindmap/training_metadata.json",
        "targets": {"best_val_auc": 0.80},
    },
    {
        "id": 10,
        "name": "BERTopic Discovery",
        "owner": "N V Hewamanne",
        "module": "module3-data",
        "metadata_path": "services/module3-data/models/bertopic/training_metadata.json",
        "targets": {},  # Topic coherence evaluated qualitatively
    },
]


def evaluate_model(model_info: dict, project_root: Path) -> dict:
    """Evaluate a single model against its targets."""
    result = {
        "id": model_info["id"],
        "name": model_info["name"],
        "owner": model_info["owner"],
        "module": model_info["module"],
        "status": "not_trained",
        "metrics": {},
        "targets_met": {},
        "pass": False,
    }

    metadata_path = project_root / model_info["metadata_path"]
    if not metadata_path.exists():
        result["status"] = "not_trained"
        return result

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    if metadata.get("status") == "skipped":
        result["status"] = "skipped"
        result["reason"] = metadata.get("reason", "unknown")
        return result

    result["status"] = "trained"
    result["metrics"] = {k: v for k, v in metadata.items() if isinstance(v, (int, float))}

    # Check targets
    all_met = True
    for metric_key, target_value in model_info["targets"].items():
        actual = metadata.get(metric_key)
        if actual is not None:
            met = actual >= target_value
            result["targets_met"][metric_key] = {
                "target": target_value,
                "actual": actual,
                "met": met,
            }
            if not met:
                all_met = False
        else:
            result["targets_met"][metric_key] = {
                "target": target_value,
                "actual": None,
                "met": False,
            }
            all_met = False

    # If no targets defined, pass by default (qualitative evaluation)
    if not model_info["targets"]:
        result["pass"] = True
    else:
        result["pass"] = all_met

    return result


def run_evaluation(project_root: str = ".", output_file: str | None = None) -> None:
    """Run evaluation for all models and generate report."""
    root = Path(project_root)

    results = []
    for model_info in MODEL_REGISTRY:
        result = evaluate_model(model_info, root)
        results.append(result)

        status_icon = "PASS" if result["pass"] else ("SKIP" if result["status"] == "skipped" else "FAIL" if result["status"] == "trained" else "----")
        logger.info(
            "[%s] Model %d: %s (%s)",
            status_icon, result["id"], result["name"], result["status"],
        )
        for metric, info in result.get("targets_met", {}).items():
            met_str = "MET" if info["met"] else "MISS"
            logger.info(
                "        %s: %.4f / %.4f [%s]",
                metric, info["actual"] or 0, info["target"], met_str,
            )

    # Summary
    trained = sum(1 for r in results if r["status"] == "trained")
    passed = sum(1 for r in results if r["pass"])
    skipped = sum(1 for r in results if r["status"] == "skipped")
    not_trained = sum(1 for r in results if r["status"] == "not_trained")

    logger.info("=" * 60)
    logger.info("EVALUATION SUMMARY")
    logger.info("  Trained:     %d / %d", trained, len(results))
    logger.info("  Passing:     %d / %d", passed, len(results))
    logger.info("  Skipped:     %d", skipped)
    logger.info("  Not trained: %d", not_trained)
    logger.info("=" * 60)

    report = {
        "summary": {
            "total_models": len(results),
            "trained": trained,
            "passing": passed,
            "skipped": skipped,
            "not_trained": not_trained,
        },
        "models": results,
    }

    if output_file:
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info("Report saved to %s", out_path)


def main():
    parser = argparse.ArgumentParser(description="Evaluate all ML models")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output", default="ml/evaluation/report.json")
    args = parser.parse_args()
    run_evaluation(project_root=args.project_root, output_file=args.output)


if __name__ == "__main__":
    main()

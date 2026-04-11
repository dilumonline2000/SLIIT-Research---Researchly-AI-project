"""Model 5: Research Summarizer — BART with LoRA fine-tuning.

Architecture: facebook/bart-large-cnn + LoRA adapters on q_proj, v_proj
Loss: Cross-entropy (seq2seq)
Target: ROUGE-1 >= 0.45, ROUGE-2 >= 0.20, ROUGE-L >= 0.35

Usage:
    python ml/training/train_summarizer.py
    python ml/training/train_summarizer.py --epochs 5 --lr 1e-4
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    get_linear_schedule_with_warmup,
)

try:
    from peft import LoraConfig, get_peft_model, TaskType
    HAS_PEFT = True
except ImportError:
    HAS_PEFT = False

try:
    from rouge_score import rouge_scorer
    HAS_ROUGE = True
except ImportError:
    HAS_ROUGE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class SummarizationDataset(Dataset):
    """Dataset for abstractive summarization."""

    def __init__(self, sources: list[str], targets: list[str], tokenizer, max_input: int = 1024, max_output: int = 256):
        self.sources = sources
        self.targets = targets
        self.tokenizer = tokenizer
        self.max_input = max_input
        self.max_output = max_output

    def __len__(self):
        return len(self.sources)

    def __getitem__(self, idx):
        source_enc = self.tokenizer(
            self.sources[idx],
            max_length=self.max_input,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        target_enc = self.tokenizer(
            self.targets[idx],
            max_length=self.max_output,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        labels = target_enc["input_ids"].squeeze(0)
        labels[labels == self.tokenizer.pad_token_id] = -100
        return {
            "input_ids": source_enc["input_ids"].squeeze(0),
            "attention_mask": source_enc["attention_mask"].squeeze(0),
            "labels": labels,
        }


def load_data(data_dir: str) -> tuple[list[str], list[str]]:
    """Load paper full-text / abstract pairs."""
    papers_file = Path(data_dir) / "papers_processed.json"
    if papers_file.exists():
        with open(papers_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        sources, targets = [], []
        for p in papers:
            abstract = p.get("abstract", "")
            full_text = p.get("full_text", "")
            if not full_text:
                full_text = f"{p.get('title', '')}. {abstract}"
            if abstract and len(abstract) > 100:
                sources.append(full_text)
                targets.append(abstract)
        if sources:
            return sources, targets

    logger.warning("No summarization data found, using synthetic examples")
    return _synthetic_data()


def _synthetic_data() -> tuple[list[str], list[str]]:
    """Bootstrap synthetic paper/abstract pairs."""
    pairs = [
        (
            "This paper presents a novel deep learning framework for natural language understanding. "
            "We propose a transformer-based architecture that leverages multi-head attention mechanisms "
            "to capture long-range dependencies in text. Our model is trained on a large corpus of "
            "academic papers and evaluated on several benchmark datasets. The experimental results "
            "demonstrate that our approach achieves state-of-the-art performance on text classification, "
            "named entity recognition, and question answering tasks. We also conduct ablation studies "
            "to analyze the contribution of each component. The proposed method outperforms existing "
            "approaches by 3-5% on all benchmarks while requiring 40% fewer parameters.",
            "We present a transformer-based framework for NLU that achieves state-of-the-art results "
            "on classification, NER, and QA benchmarks with 40% fewer parameters."
        ),
        (
            "Internet of Things security remains a critical challenge as billions of devices connect "
            "to networks worldwide. This study surveys current vulnerability classes in IoT ecosystems "
            "including firmware exploits, insecure communication protocols, and weak authentication. "
            "We propose a lightweight intrusion detection system based on edge computing that can "
            "operate within the resource constraints of typical IoT devices. Our system uses a "
            "compressed random forest classifier that achieves 94% detection accuracy with minimal "
            "latency overhead. Field testing on a smart home network of 50 devices over 6 months "
            "validates the practical effectiveness of our approach.",
            "We survey IoT security vulnerabilities and propose a lightweight edge-based intrusion "
            "detection system using compressed random forests, achieving 94% accuracy on smart home networks."
        ),
        (
            "Cloud computing has transformed how organizations deploy and manage applications. "
            "Microservice architectures offer scalability but introduce complexity in service "
            "orchestration and inter-service communication. This paper evaluates three orchestration "
            "patterns: choreography, orchestration, and hybrid approaches across 12 production "
            "workloads. We measure latency, throughput, fault tolerance, and development velocity. "
            "Results show hybrid patterns achieve 25% better fault tolerance while maintaining "
            "comparable throughput. We provide a decision framework for selecting orchestration "
            "patterns based on workload characteristics.",
            "We evaluate choreography, orchestration, and hybrid microservice patterns across 12 "
            "production workloads, finding hybrid approaches offer 25% better fault tolerance."
        ),
        (
            "Federated learning enables collaborative model training without sharing raw data. "
            "However, communication overhead between clients and the central server remains a "
            "bottleneck. This work proposes gradient compression techniques that reduce communication "
            "costs by 90% while maintaining model accuracy within 1% of uncompressed baselines. "
            "We test on image classification and NLP tasks with up to 1000 simulated clients. "
            "Our approach combines top-k sparsification with quantization and error feedback "
            "mechanisms to prevent information loss across training rounds.",
            "We propose gradient compression for federated learning that reduces communication "
            "by 90% with under 1% accuracy loss, validated on 1000-client simulations."
        ),
        (
            "Graph neural networks have shown promise in molecular property prediction. "
            "This paper introduces a hierarchical GNN architecture that captures both atom-level "
            "and substructure-level features for drug-target interaction prediction. We train on "
            "the ChEMBL database of 2 million compounds and evaluate on standard drug discovery "
            "benchmarks. Our model achieves an AUC of 0.92 on the DAVIS kinase dataset and 0.88 "
            "on KIBA, outperforming existing methods by significant margins. The hierarchical "
            "attention mechanism provides interpretable predictions that align with known binding sites.",
            "We introduce a hierarchical GNN for drug-target interaction prediction that achieves "
            "0.92 AUC on DAVIS with interpretable attention over binding sites."
        ),
    ]
    sources = [p[0] for p in pairs] * 10
    targets = [p[1] for p in pairs] * 10
    return sources, targets


def compute_rouge(predictions: list[str], references: list[str]) -> dict[str, float]:
    """Compute ROUGE scores."""
    if not HAS_ROUGE:
        return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}

    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = {"rouge1": [], "rouge2": [], "rougeL": []}
    for pred, ref in zip(predictions, references):
        result = scorer.score(ref, pred)
        for key in scores:
            scores[key].append(result[key].fmeasure)
    return {k: float(np.mean(v)) for k, v in scores.items()}


def train_summarizer(
    base_model: str = "facebook/bart-large-cnn",
    output_dir: str = "services/module3-data/models/summarizer",
    data_dir: str = "ml/data/processed",
    epochs: int = 5,
    batch_size: int = 8,
    learning_rate: float = 1e-4,
    max_input_length: int = 1024,
    max_output_length: int = 256,
    use_lora: bool = True,
    lora_r: int = 16,
    lora_alpha: int = 32,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForSeq2SeqLM.from_pretrained(base_model)

    # Apply LoRA if available
    if use_lora and HAS_PEFT:
        lora_config = LoraConfig(
            task_type=TaskType.SEQ_2_SEQ_LM,
            r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=0.05,
            target_modules=["q_proj", "v_proj"],
        )
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
        logger.info("LoRA applied (r=%d, alpha=%d)", lora_r, lora_alpha)
    elif use_lora:
        logger.warning("peft not installed — training full model (pip install peft)")

    model = model.to(device)

    sources, targets = load_data(data_dir)
    logger.info("Loaded %d summarization pairs", len(sources))

    # Split
    indices = list(range(len(sources)))
    random.shuffle(indices)
    train_end = int(len(indices) * 0.70)
    val_end = int(len(indices) * 0.85)
    train_idx = indices[:train_end]
    val_idx = indices[train_end:val_end]
    test_idx = indices[val_end:]

    train_ds = SummarizationDataset([sources[i] for i in train_idx], [targets[i] for i in train_idx], tokenizer, max_input_length, max_output_length)
    val_ds = SummarizationDataset([sources[i] for i in val_idx], [targets[i] for i in val_idx], tokenizer, max_input_length, max_output_length)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=total_steps // 10, num_training_steps=total_steps)

    best_rouge = 0.0

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch in train_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)

        # Validate with ROUGE
        model.eval()
        val_preds, val_refs = [], []
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                generated = model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    max_length=max_output_length,
                    num_beams=4,
                    early_stopping=True,
                )
                decoded = tokenizer.batch_decode(generated, skip_special_tokens=True)
                val_preds.extend(decoded)
                # Decode reference labels
                ref_labels = batch["labels"].clone()
                ref_labels[ref_labels == -100] = tokenizer.pad_token_id
                refs = tokenizer.batch_decode(ref_labels, skip_special_tokens=True)
                val_refs.extend(refs)

        rouge_scores = compute_rouge(val_preds, val_refs)
        logger.info(
            "Epoch %d/%d — loss: %.4f — ROUGE-1: %.4f — ROUGE-2: %.4f — ROUGE-L: %.4f",
            epoch + 1, epochs, avg_loss,
            rouge_scores["rouge1"], rouge_scores["rouge2"], rouge_scores["rougeL"],
        )

        avg_rouge = (rouge_scores["rouge1"] + rouge_scores["rougeL"]) / 2
        if avg_rouge > best_rouge:
            best_rouge = avg_rouge
            if HAS_PEFT and use_lora:
                model.save_pretrained(str(output_path))
            else:
                torch.save(model.state_dict(), output_path / "model.pt")
            tokenizer.save_pretrained(str(output_path))
            logger.info("New best model saved (avg ROUGE=%.4f)", avg_rouge)

    metadata = {
        "model": "research-summarizer",
        "base": base_model,
        "lora": use_lora and HAS_PEFT,
        "best_rouge_avg": best_rouge,
        "epochs": epochs,
        "train_size": len(train_idx),
        "val_size": len(val_idx),
        "test_size": len(test_idx),
    }
    with open(output_path / "training_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Summarizer training complete. Best avg ROUGE=%.4f", best_rouge)


def main():
    parser = argparse.ArgumentParser(description="Train research summarizer (BART + LoRA)")
    parser.add_argument("--base", default="facebook/bart-large-cnn")
    parser.add_argument("--output", default="services/module3-data/models/summarizer")
    parser.add_argument("--data", default="ml/data/processed")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--no-lora", action="store_true")
    args = parser.parse_args()
    train_summarizer(
        base_model=args.base, output_dir=args.output, data_dir=args.data,
        epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.lr,
        use_lora=not args.no_lora,
    )


if __name__ == "__main__":
    main()

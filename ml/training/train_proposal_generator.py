"""Model 6: Proposal Generator — RAG + LoRA fine-tuned LLM.

Architecture: Mistral-7B-Instruct (or fallback) + LoRA adapters + RAG retrieval
Loss: Cross-entropy (causal LM)
Output: Structured proposal (problem_statement, objectives, methodology, expected_outcomes)

Usage:
    python ml/training/train_proposal_generator.py
    python ml/training/train_proposal_generator.py --base mistralai/Mistral-7B-Instruct-v0.2 --epochs 3
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from pathlib import Path

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    get_linear_schedule_with_warmup,
    BitsAndBytesConfig,
)

try:
    from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
    HAS_PEFT = True
except ImportError:
    HAS_PEFT = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROPOSAL_TEMPLATE = """### Instruction
Based on the following research context, generate a structured research proposal.

### Context
{context}

### Research Gap
{gap}

### Proposal
{proposal}"""


class ProposalDataset(Dataset):
    """Dataset for proposal generation training."""

    def __init__(self, examples: list[dict], tokenizer, max_length: int = 2048):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ex = self.examples[idx]
        text = PROPOSAL_TEMPLATE.format(
            context=ex["context"],
            gap=ex["gap"],
            proposal=json.dumps(ex["proposal"], indent=2),
        )
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        input_ids = encoding["input_ids"].squeeze(0)
        labels = input_ids.clone()
        # Mask everything before "### Proposal" as -100
        proposal_marker = self.tokenizer.encode("### Proposal", add_special_tokens=False)
        for i in range(len(input_ids) - len(proposal_marker)):
            if input_ids[i:i + len(proposal_marker)].tolist() == proposal_marker:
                labels[:i + len(proposal_marker)] = -100
                break
        labels[input_ids == self.tokenizer.pad_token_id] = -100
        return {
            "input_ids": input_ids,
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": labels,
        }


def load_data(data_dir: str) -> list[dict]:
    """Load proposal training data."""
    proposals_file = Path(data_dir) / "proposals_training.json"
    if proposals_file.exists():
        with open(proposals_file, "r", encoding="utf-8") as f:
            return json.load(f)

    logger.warning("No proposal data found, using synthetic examples")
    return _synthetic_data()


def _synthetic_data() -> list[dict]:
    """Bootstrap synthetic proposal data."""
    examples = [
        {
            "context": "Recent advances in federated learning have enabled privacy-preserving model training across distributed data sources. However, communication efficiency remains a bottleneck in large-scale deployments with thousands of edge devices.",
            "gap": "Existing gradient compression methods for federated learning do not adequately address heterogeneous device capabilities and network conditions.",
            "proposal": {
                "problem_statement": "Communication overhead in federated learning scales poorly with heterogeneous edge devices, leading to training bottlenecks and device dropout.",
                "objectives": ["Develop adaptive gradient compression that accounts for device heterogeneity", "Achieve 90% communication reduction while maintaining convergence guarantees", "Validate on real-world IoT datasets with 1000+ devices"],
                "methodology": "We propose HeteroCompress, an adaptive compression framework that dynamically selects compression rates based on device capabilities and network conditions. We will use a reinforcement learning agent to optimize compression policies per-device.",
                "expected_outcomes": "90% reduction in communication overhead with less than 2% accuracy degradation compared to uncompressed federated learning baselines."
            }
        },
        {
            "context": "Large language models have demonstrated remarkable capabilities in code generation. However, their application to domain-specific programming tasks in scientific computing remains underexplored.",
            "gap": "LLMs struggle with scientific computing code that requires domain expertise in numerical methods and mathematical formulations.",
            "proposal": {
                "problem_statement": "Current code-generating LLMs lack domain knowledge for scientific computing, producing code with numerical instabilities and incorrect mathematical implementations.",
                "objectives": ["Fine-tune LLMs on curated scientific computing codebases", "Develop a benchmark for scientific code generation quality", "Achieve 80% functional correctness on numerical method implementations"],
                "methodology": "We will curate a dataset of 50,000 scientific computing functions from established libraries (NumPy, SciPy, FEniCS) with documentation pairs. A domain-specific LoRA adapter will be trained on this dataset with custom loss weighting for numerical accuracy.",
                "expected_outcomes": "A specialized code generation model achieving 80% functional correctness on scientific computing benchmarks, compared to 45% for general-purpose code LLMs."
            }
        },
        {
            "context": "Graph neural networks have become the standard approach for molecular property prediction. Recent work has explored hierarchical representations that capture both local and global molecular features.",
            "gap": "Current GNN approaches for drug discovery do not effectively incorporate 3D spatial information and protein-ligand interaction dynamics.",
            "proposal": {
                "problem_statement": "Molecular property prediction GNNs operating on 2D graph representations miss critical 3D conformational and dynamic interaction information needed for accurate drug-target binding prediction.",
                "objectives": ["Develop a 3D-aware GNN architecture for protein-ligand binding prediction", "Incorporate molecular dynamics simulations as training signal", "Outperform 2D GNNs by 10% AUC on standard drug discovery benchmarks"],
                "methodology": "We propose DynaBind-GNN, which combines equivariant graph neural networks with molecular dynamics trajectory features. The model processes 3D conformer ensembles using SE(3)-equivariant message passing.",
                "expected_outcomes": "A 3D-aware binding prediction model achieving 0.95 AUC on DAVIS and 0.91 on KIBA benchmarks."
            }
        },
    ]
    return examples * 5


def train_proposal_generator(
    base_model: str = "mistralai/Mistral-7B-Instruct-v0.2",
    output_dir: str = "services/module1-integrity/models/proposal_lora",
    data_dir: str = "ml/data/processed/proposals",
    epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 2e-4,
    max_length: int = 2048,
    use_lora: bool = True,
    lora_r: int = 16,
    lora_alpha: int = 32,
    use_4bit: bool = True,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)

    if device.type != "cuda":
        logger.warning("Causal LM training strongly benefits from GPU. CPU training will be very slow.")
        use_4bit = False  # bitsandbytes requires CUDA

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model with optional 4-bit quantization
    model_kwargs = {}
    if use_4bit and device.type == "cuda":
        try:
            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
            logger.info("Using 4-bit quantization")
        except Exception:
            logger.warning("4-bit quantization failed, loading in full precision")

    try:
        model = AutoModelForCausalLM.from_pretrained(base_model, **model_kwargs)
    except Exception as e:
        logger.warning("Could not load %s: %s. Using smaller model for testing.", base_model, e)
        base_model = "gpt2"
        model = AutoModelForCausalLM.from_pretrained(base_model)
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

    # Apply LoRA
    if use_lora and HAS_PEFT:
        if use_4bit and device.type == "cuda":
            try:
                model = prepare_model_for_kbit_training(model)
            except Exception:
                pass
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=lora_r,
            lora_alpha=lora_alpha,
            lora_dropout=0.05,
            target_modules=["q_proj", "v_proj"],
        )
        try:
            model = get_peft_model(model, lora_config)
            model.print_trainable_parameters()
        except Exception as e:
            logger.warning("LoRA failed (%s), training full model", e)
    elif use_lora:
        logger.warning("peft not installed — pip install peft")

    model = model.to(device)

    examples = load_data(data_dir)
    logger.info("Loaded %d proposal examples", len(examples))

    random.shuffle(examples)
    split = int(len(examples) * 0.85)
    train_examples = examples[:split]
    val_examples = examples[split:]

    train_ds = ProposalDataset(train_examples, tokenizer, max_length)
    val_ds = ProposalDataset(val_examples, tokenizer, max_length)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    optimizer = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=learning_rate, weight_decay=0.01,
    )
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=total_steps // 10, num_training_steps=total_steps)

    best_val_loss = float("inf")

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

        avg_train_loss = total_loss / len(train_loader)

        # Validate
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels = batch["labels"].to(device)
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                val_loss += outputs.loss.item()

        avg_val_loss = val_loss / max(len(val_loader), 1)
        logger.info(
            "Epoch %d/%d — train loss: %.4f — val loss: %.4f",
            epoch + 1, epochs, avg_train_loss, avg_val_loss,
        )

        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            if HAS_PEFT and use_lora:
                model.save_pretrained(str(output_path))
            else:
                torch.save(model.state_dict(), output_path / "model.pt")
            tokenizer.save_pretrained(str(output_path))
            logger.info("New best model saved (val_loss=%.4f)", avg_val_loss)

    metadata = {
        "model": "proposal-generator",
        "base": base_model,
        "lora": use_lora and HAS_PEFT,
        "best_val_loss": best_val_loss,
        "epochs": epochs,
        "train_size": len(train_examples),
        "val_size": len(val_examples),
    }
    with open(output_path / "training_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Proposal generator training complete. Best val_loss=%.4f", best_val_loss)


def main():
    parser = argparse.ArgumentParser(description="Train proposal generator (RAG + LoRA LLM)")
    parser.add_argument("--base", default="mistralai/Mistral-7B-Instruct-v0.2")
    parser.add_argument("--output", default="services/module1-integrity/models/proposal_lora")
    parser.add_argument("--data", default="ml/data/processed/proposals")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--no-lora", action="store_true")
    args = parser.parse_args()
    train_proposal_generator(
        base_model=args.base, output_dir=args.output, data_dir=args.data,
        epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.lr,
        use_lora=not args.no_lora,
    )


if __name__ == "__main__":
    main()

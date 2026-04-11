"""Model 4: Aspect-Based Sentiment Analysis for academic feedback.

Architecture: BERT encoder → 4 aspect-specific classification heads (3 classes each)
Aspects: methodology, writing, originality, data_analysis
Classes per aspect: positive, neutral, negative
Loss: CrossEntropyLoss per head, summed
Target: Accuracy >= 0.93, per-aspect F1 >= 0.85

Usage:
    python ml/training/train_sentiment.py
    python ml/training/train_sentiment.py --epochs 15 --lr 2e-5
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_linear_schedule_with_warmup
from sklearn.metrics import f1_score, accuracy_score, classification_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ASPECTS = ["methodology", "writing", "originality", "data_analysis"]
LABELS = ["positive", "neutral", "negative"]


class AspectSentimentModel(nn.Module):
    """BERT with per-aspect classification heads."""

    def __init__(self, base_model: str, num_aspects: int = 4, num_classes: int = 3, dropout: float = 0.3):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model)
        hidden_size = self.encoder.config.hidden_size
        self.aspect_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, 256),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(256, num_classes),
            )
            for _ in range(num_aspects)
        ])

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls_output = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        return [head(cls_output) for head in self.aspect_heads]


class FeedbackDataset(Dataset):
    """Dataset for aspect-based sentiment analysis."""

    def __init__(self, texts: list[str], labels: np.ndarray, tokenizer, max_length: int = 512):
        self.texts = texts
        self.labels = labels  # shape: (N, num_aspects)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoding = self.tokenizer(
            self.texts[idx],
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long),
        }


def load_data(data_dir: str) -> tuple[list[str], np.ndarray]:
    """Load feedback data with aspect sentiments."""
    feedback_dir = Path(data_dir)
    feedback_file = feedback_dir / "feedback_labeled.json"
    if feedback_file.exists():
        with open(feedback_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        texts = []
        labels = []
        for item in data:
            texts.append(item["text"])
            labels.append([item["aspects"][a] for a in ASPECTS])
        return texts, np.array(labels)

    logger.warning("No feedback data found, generating synthetic examples")
    return _synthetic_data()


def _synthetic_data() -> tuple[list[str], np.ndarray]:
    """Bootstrap synthetic feedback data for pipeline testing."""
    samples = [
        ("The methodology is well-structured and follows established protocols. Writing is clear and concise. Novel approach to the problem. Data analysis could be more rigorous.", [0, 0, 0, 2]),
        ("Poor research design with no control group. Grammatical errors throughout. The idea is not original. Statistical analysis is incorrect.", [2, 2, 2, 2]),
        ("Adequate methodology but lacks detail. Writing quality is acceptable. Some novel contributions. Data analysis is thorough and well-presented.", [1, 1, 0, 0]),
        ("Excellent experimental design with proper validation. Writing needs significant improvement. Highly original contribution to the field. Solid statistical methods.", [0, 2, 0, 0]),
        ("The methods section is incomplete. Well-written and easy to follow. Incremental improvement over existing work. No data analysis provided.", [2, 0, 1, 2]),
        ("Sound methodology with clear justification. Average writing quality. Creative problem formulation. Basic but correct analysis.", [0, 1, 0, 1]),
        ("Flawed experimental setup. Excellent academic writing. Derivative work with no new insights. Comprehensive data analysis.", [2, 0, 2, 0]),
        ("Rigorous and reproducible methods. Several typos and unclear sections. Moderately original. Analysis lacks depth.", [0, 2, 1, 2]),
        ("Standard methodology, nothing exceptional. Clear and professional writing. Fresh perspective on an old problem. Appropriate statistical tests used.", [1, 0, 0, 0]),
        ("Innovative mixed-methods approach. Writing is too verbose. Truly groundbreaking research. Data visualization is misleading.", [0, 2, 0, 2]),
    ]
    texts = [s[0] for s in samples] * 10
    labels = np.array([s[1] for s in samples] * 10)
    return texts, labels


def train_sentiment(
    base_model: str = "bert-base-uncased",
    output_dir: str = "services/module2-collaboration/models/sentiment",
    data_dir: str = "ml/data/processed/feedback",
    epochs: int = 10,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
    max_length: int = 512,
    dropout: float = 0.3,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)

    texts, labels = load_data(data_dir)
    logger.info("Loaded %d samples", len(texts))

    # Split
    indices = list(range(len(texts)))
    random.shuffle(indices)
    train_end = int(len(indices) * 0.70)
    val_end = int(len(indices) * 0.85)
    train_idx = indices[:train_end]
    val_idx = indices[train_end:val_end]
    test_idx = indices[val_end:]

    tokenizer = AutoTokenizer.from_pretrained(base_model)

    train_ds = FeedbackDataset([texts[i] for i in train_idx], labels[train_idx], tokenizer, max_length)
    val_ds = FeedbackDataset([texts[i] for i in val_idx], labels[val_idx], tokenizer, max_length)
    test_ds = FeedbackDataset([texts[i] for i in test_idx], labels[test_idx], tokenizer, max_length)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)
    test_loader = DataLoader(test_ds, batch_size=batch_size)

    model = AspectSentimentModel(base_model, num_aspects=len(ASPECTS), dropout=dropout).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)

    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=total_steps // 10, num_training_steps=total_steps)

    best_f1 = 0.0

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch in train_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            batch_labels = batch["labels"].to(device)

            optimizer.zero_grad()
            logits_list = model(input_ids, attention_mask)

            loss = sum(
                criterion(logits_list[i], batch_labels[:, i])
                for i in range(len(ASPECTS))
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)

        # Validate
        model.eval()
        aspect_preds = {a: [] for a in ASPECTS}
        aspect_true = {a: [] for a in ASPECTS}

        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                logits_list = model(input_ids, attention_mask)
                batch_labels = batch["labels"]

                for i, aspect in enumerate(ASPECTS):
                    preds = logits_list[i].argmax(dim=-1).cpu().numpy()
                    aspect_preds[aspect].extend(preds)
                    aspect_true[aspect].extend(batch_labels[:, i].numpy())

        aspect_f1s = {}
        for aspect in ASPECTS:
            aspect_f1s[aspect] = f1_score(aspect_true[aspect], aspect_preds[aspect], average="macro", zero_division=0)

        avg_f1 = np.mean(list(aspect_f1s.values()))
        logger.info(
            "Epoch %d/%d — loss: %.4f — avg F1: %.4f — %s",
            epoch + 1, epochs, avg_loss, avg_f1,
            " | ".join(f"{a}: {f:.3f}" for a, f in aspect_f1s.items()),
        )

        if avg_f1 > best_f1:
            best_f1 = avg_f1
            torch.save(model.state_dict(), output_path / "model.pt")
            tokenizer.save_pretrained(str(output_path))
            logger.info("New best model saved (avg F1=%.4f)", avg_f1)

    # Test evaluation
    model.load_state_dict(torch.load(output_path / "model.pt", weights_only=True))
    model.eval()
    aspect_preds = {a: [] for a in ASPECTS}
    aspect_true = {a: [] for a in ASPECTS}

    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            logits_list = model(input_ids, attention_mask)
            batch_labels = batch["labels"]
            for i, aspect in enumerate(ASPECTS):
                preds = logits_list[i].argmax(dim=-1).cpu().numpy()
                aspect_preds[aspect].extend(preds)
                aspect_true[aspect].extend(batch_labels[:, i].numpy())

    logger.info("Test set results:")
    for aspect in ASPECTS:
        report = classification_report(
            aspect_true[aspect], aspect_preds[aspect],
            target_names=LABELS, zero_division=0,
        )
        logger.info("Aspect: %s\n%s", aspect, report)

    metadata = {
        "model": "aspect-sentiment",
        "base": base_model,
        "aspects": ASPECTS,
        "num_classes": len(LABELS),
        "best_val_f1": best_f1,
        "epochs": epochs,
        "train_size": len(train_idx),
        "val_size": len(val_idx),
        "test_size": len(test_idx),
    }
    with open(output_path / "training_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # Save aspect/label mappings
    with open(output_path / "label_config.json", "w") as f:
        json.dump({"aspects": ASPECTS, "labels": LABELS}, f, indent=2)

    logger.info("Sentiment training complete. Best avg F1=%.4f", best_f1)


def main():
    parser = argparse.ArgumentParser(description="Train aspect-based sentiment model")
    parser.add_argument("--base", default="bert-base-uncased")
    parser.add_argument("--output", default="services/module2-collaboration/models/sentiment")
    parser.add_argument("--data", default="ml/data/processed/feedback")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-5)
    args = parser.parse_args()
    train_sentiment(base_model=args.base, output_dir=args.output, data_dir=args.data, epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.lr)


if __name__ == "__main__":
    main()

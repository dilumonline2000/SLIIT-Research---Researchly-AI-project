"""Model 3: SciBERT Multi-label Topic Classifier.

Architecture: SciBERT encoder → Mean pooling → Dense(768,512) → ReLU → Dropout(0.3) → Dense(512,num_labels) → Sigmoid
Loss: BCEWithLogitsLoss
Target: Macro F1 >= 0.80, Precision >= 0.82

Usage:
    python ml/training/train_scibert.py
    python ml/training/train_scibert.py --epochs 20 --lr 3e-5
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
from sklearn.metrics import f1_score, precision_score, classification_report
from sklearn.preprocessing import MultiLabelBinarizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CATEGORIES = [
    "Artificial Intelligence", "Internet of Things", "Networking",
    "Cybersecurity", "Data Science", "Machine Learning",
    "Mobile Computing", "Cloud Computing", "Software Engineering",
    "Computer Vision", "Natural Language Processing",
    "Information Retrieval", "Databases",
    "Human-Computer Interaction", "Other",
]


class SciBERTClassifier(nn.Module):
    """SciBERT with a multi-label classification head."""

    def __init__(self, base_model: str, num_labels: int, dropout: float = 0.3):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model)
        hidden_size = self.encoder.config.hidden_size  # 768
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, num_labels),
        )

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        # Mean pooling over token embeddings
        token_embeddings = outputs.last_hidden_state
        mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        pooled = torch.sum(token_embeddings * mask_expanded, dim=1) / torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
        return self.classifier(pooled)


class PaperDataset(Dataset):
    """Dataset for multi-label paper classification."""

    def __init__(self, texts: list[str], labels: np.ndarray, tokenizer, max_length: int = 512):
        self.texts = texts
        self.labels = labels
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
            "labels": torch.tensor(self.labels[idx], dtype=torch.float32),
        }


def load_data(data_dir: str) -> tuple[list[str], list[list[str]]]:
    """Load papers and their topic labels."""
    papers_file = Path(data_dir) / "papers_processed.json"
    if papers_file.exists():
        with open(papers_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        texts = []
        labels = []
        for p in papers:
            abstract = p.get("abstract", "")
            kws = p.get("keywords", [])
            if abstract and len(abstract) > 50 and kws:
                texts.append(f"{p.get('title', '')}. {abstract}")
                labels.append(kws)
        return texts, labels

    logger.warning("No data found, generating synthetic examples")
    return _synthetic_data()


def _synthetic_data() -> tuple[list[str], list[list[str]]]:
    """Bootstrap synthetic data for pipeline testing."""
    data = [
        ("Deep reinforcement learning for autonomous navigation", ["Artificial Intelligence", "Machine Learning"]),
        ("BERT-based sentiment analysis of product reviews", ["Natural Language Processing", "Machine Learning"]),
        ("Secure IoT gateway design for smart homes", ["Internet of Things", "Cybersecurity"]),
        ("Cloud-native microservice architecture patterns", ["Cloud Computing", "Software Engineering"]),
        ("Mobile health monitoring using wearable sensors", ["Mobile Computing", "Internet of Things"]),
        ("Graph databases for social network analysis", ["Databases", "Data Science"]),
        ("Object detection in autonomous driving with YOLOv8", ["Computer Vision", "Artificial Intelligence"]),
        ("Privacy-preserving federated learning framework", ["Machine Learning", "Cybersecurity"]),
        ("Network intrusion detection using random forests", ["Cybersecurity", "Networking"]),
        ("Voice user interface design for elderly users", ["Human-Computer Interaction", "Mobile Computing"]),
    ]
    texts = [d[0] for d in data]
    labels = [d[1] for d in data]
    # Duplicate to have minimal training set
    texts = texts * 10
    labels = labels * 10
    return texts, labels


def train_scibert(
    base_model: str = "allenai/scibert_scivocab_uncased",
    output_dir: str = "services/module3-data/models/scibert_classifier",
    data_dir: str = "ml/data/processed",
    epochs: int = 15,
    batch_size: int = 16,
    learning_rate: float = 3e-5,
    max_length: int = 512,
    dropout: float = 0.3,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)

    # Load data
    texts, raw_labels = load_data(data_dir)
    logger.info("Loaded %d samples", len(texts))

    # Binarize labels
    mlb = MultiLabelBinarizer(classes=CATEGORIES)
    labels = mlb.fit_transform(raw_labels)

    # Save label mapping
    with open(output_path / "label_classes.json", "w") as f:
        json.dump(CATEGORIES, f)

    # Split
    indices = list(range(len(texts)))
    random.shuffle(indices)
    train_end = int(len(indices) * 0.70)
    val_end = int(len(indices) * 0.85)
    train_idx = indices[:train_end]
    val_idx = indices[train_end:val_end]
    test_idx = indices[val_end:]

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model)

    train_ds = PaperDataset([texts[i] for i in train_idx], labels[train_idx], tokenizer, max_length)
    val_ds = PaperDataset([texts[i] for i in val_idx], labels[val_idx], tokenizer, max_length)
    test_ds = PaperDataset([texts[i] for i in test_idx], labels[test_idx], tokenizer, max_length)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)
    test_loader = DataLoader(test_ds, batch_size=batch_size)

    # Model
    model = SciBERTClassifier(base_model, num_labels=len(CATEGORIES), dropout=dropout).to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)

    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=total_steps // 10, num_training_steps=total_steps)

    best_f1 = 0.0

    for epoch in range(epochs):
        # Train
        model.train()
        total_loss = 0
        for batch in train_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            batch_labels = batch["labels"].to(device)

            optimizer.zero_grad()
            logits = model(input_ids, attention_mask)
            loss = criterion(logits, batch_labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)

        # Validate
        model.eval()
        all_preds, all_true = [], []
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                logits = model(input_ids, attention_mask)
                preds = (torch.sigmoid(logits) > 0.5).cpu().numpy()
                all_preds.append(preds)
                all_true.append(batch["labels"].numpy())

        all_preds = np.vstack(all_preds)
        all_true = np.vstack(all_true)
        macro_f1 = f1_score(all_true, all_preds, average="macro", zero_division=0)
        precision = precision_score(all_true, all_preds, average="macro", zero_division=0)

        logger.info(
            "Epoch %d/%d — loss: %.4f — val Macro-F1: %.4f — Precision: %.4f",
            epoch + 1, epochs, avg_loss, macro_f1, precision,
        )

        if macro_f1 > best_f1:
            best_f1 = macro_f1
            torch.save(model.state_dict(), output_path / "model.pt")
            tokenizer.save_pretrained(str(output_path))
            logger.info("New best model saved (Macro-F1=%.4f)", macro_f1)

    # Test evaluation
    model.load_state_dict(torch.load(output_path / "model.pt", weights_only=True))
    model.eval()
    all_preds, all_true = [], []
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            logits = model(input_ids, attention_mask)
            preds = (torch.sigmoid(logits) > 0.5).cpu().numpy()
            all_preds.append(preds)
            all_true.append(batch["labels"].numpy())

    all_preds = np.vstack(all_preds)
    all_true = np.vstack(all_true)
    report = classification_report(all_true, all_preds, target_names=CATEGORIES, zero_division=0)
    logger.info("Test set classification report:\n%s", report)

    metadata = {
        "model": "scibert-topic-classifier",
        "base": base_model,
        "num_labels": len(CATEGORIES),
        "best_val_f1": best_f1,
        "epochs": epochs,
        "train_size": len(train_idx),
        "val_size": len(val_idx),
        "test_size": len(test_idx),
    }
    with open(output_path / "training_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("SciBERT training complete. Best Macro-F1=%.4f", best_f1)


def main():
    parser = argparse.ArgumentParser(description="Train SciBERT multi-label classifier")
    parser.add_argument("--base", default="allenai/scibert_scivocab_uncased")
    parser.add_argument("--output", default="services/module3-data/models/scibert_classifier")
    parser.add_argument("--data", default="ml/data/processed")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=3e-5)
    args = parser.parse_args()
    train_scibert(base_model=args.base, output_dir=args.output, data_dir=args.data, epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.lr)


if __name__ == "__main__":
    main()

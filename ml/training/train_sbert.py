"""Model 2: Fine-tune SBERT for academic text similarity.

Method: Contrastive learning with triplet loss
Base: sentence-transformers/all-MiniLM-L6-v2
Training data: Triplets (anchor, positive, negative) from scraped paper clusters.

Usage:
    python ml/training/train_sbert.py
    python ml/training/train_sbert.py --base allenai/scibert_scivocab_uncased --epochs 15
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from pathlib import Path

import numpy as np
from sentence_transformers import (
    SentenceTransformer,
    InputExample,
    losses,
    evaluation,
)
from torch.utils.data import DataLoader
from sklearn.cluster import KMeans

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_papers(data_dir: str = "ml/data/processed") -> list[dict]:
    """Load preprocessed papers for triplet generation."""
    papers_file = Path(data_dir) / "papers_processed.json"
    if papers_file.exists():
        with open(papers_file, "r", encoding="utf-8") as f:
            return json.load(f)
    logger.warning("No processed papers found at %s", papers_file)
    return []


def generate_triplets(
    papers: list[dict],
    model: SentenceTransformer,
    n_clusters: int = 20,
    max_triplets: int = 10000,
) -> list[InputExample]:
    """Generate (anchor, positive, negative) triplets by topic clustering.

    1. Encode all abstracts
    2. Cluster into n_clusters via KMeans
    3. For each paper, pick a positive from the same cluster and negative from another
    """
    if not papers:
        return _generate_synthetic_triplets()

    abstracts = [p.get("abstract", "") for p in papers]
    abstracts = [a for a in abstracts if len(a) > 50]

    if len(abstracts) < 100:
        logger.warning("Too few papers (%d) for clustering, using synthetic data", len(abstracts))
        return _generate_synthetic_triplets()

    logger.info("Encoding %d abstracts for clustering...", len(abstracts))
    embeddings = model.encode(abstracts, show_progress_bar=True, batch_size=64)

    actual_clusters = min(n_clusters, len(abstracts) // 5)
    logger.info("Running KMeans with %d clusters", actual_clusters)
    kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)

    # Group by cluster
    clusters: dict[int, list[int]] = {}
    for idx, label in enumerate(labels):
        clusters.setdefault(label, []).append(idx)

    # Generate triplets
    triplets: list[InputExample] = []
    all_indices = list(range(len(abstracts)))

    for _ in range(max_triplets):
        # Pick a random cluster with at least 2 members
        valid_clusters = [c for c, members in clusters.items() if len(members) >= 2]
        if not valid_clusters:
            break

        cluster_id = random.choice(valid_clusters)
        members = clusters[cluster_id]

        anchor_idx, pos_idx = random.sample(members, 2)

        # Negative from a different cluster
        other_indices = [i for i in all_indices if labels[i] != cluster_id]
        if not other_indices:
            continue
        neg_idx = random.choice(other_indices)

        triplets.append(InputExample(texts=[
            abstracts[anchor_idx],
            abstracts[pos_idx],
            abstracts[neg_idx],
        ]))

    logger.info("Generated %d triplets from %d clusters", len(triplets), actual_clusters)
    return triplets


def _generate_synthetic_triplets() -> list[InputExample]:
    """Bootstrap synthetic triplets for testing the pipeline."""
    pairs = [
        (
            "Deep learning approaches for natural language understanding",
            "Neural network methods for text comprehension and NLU",
            "Optimizing database query performance in distributed systems",
        ),
        (
            "Convolutional neural networks for image classification",
            "CNN architectures for visual recognition tasks",
            "Sentiment analysis of customer reviews using BERT",
        ),
        (
            "Reinforcement learning for robotic manipulation",
            "RL-based control policies for robot arm grasping",
            "Statistical methods for time series forecasting",
        ),
        (
            "Federated learning for privacy-preserving machine learning",
            "Distributed model training with differential privacy guarantees",
            "Web scraping techniques for data collection from social media",
        ),
        (
            "Graph neural networks for molecular property prediction",
            "GNN-based approaches to drug discovery and molecular modeling",
            "Mobile app development frameworks comparison study",
        ),
    ]
    triplets = []
    for anchor, pos, neg in pairs:
        triplets.append(InputExample(texts=[anchor, pos, neg]))
        # Augment by swapping anchor/positive
        triplets.append(InputExample(texts=[pos, anchor, neg]))
    return triplets


def train_sbert(
    base_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    output_dir: str = "services/shared/models/sbert_academic",
    data_dir: str = "ml/data/processed",
    epochs: int = 10,
    batch_size: int = 32,
    learning_rate: float = 2e-5,
    warmup_steps: int = 100,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Loading base model: %s", base_model)
    model = SentenceTransformer(base_model)

    # Load data and generate triplets
    papers = load_papers(data_dir)
    triplets = generate_triplets(papers, model)

    if not triplets:
        logger.error("No triplets generated — cannot train")
        return

    # Split into train/val
    random.shuffle(triplets)
    split = int(len(triplets) * 0.9)
    train_examples = triplets[:split]
    val_examples = triplets[split:]

    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
    train_loss = losses.TripletLoss(model=model, distance_metric=losses.TripletDistanceMetric.COSINE, triplet_margin=0.5)

    # Evaluator (using triplet evaluation)
    val_sentences_a = [e.texts[0] for e in val_examples]
    val_sentences_b = [e.texts[1] for e in val_examples]
    val_sentences_c = [e.texts[2] for e in val_examples]

    evaluator = evaluation.TripletEvaluator(
        anchors=val_sentences_a,
        positives=val_sentences_b,
        negatives=val_sentences_c,
        name="val-triplet",
    )

    logger.info(
        "Training: %d triplets, %d val, %d epochs, batch=%d, lr=%s",
        len(train_examples), len(val_examples), epochs, batch_size, learning_rate,
    )

    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        evaluator=evaluator,
        epochs=epochs,
        warmup_steps=warmup_steps,
        optimizer_params={"lr": learning_rate},
        output_path=str(output_path),
        evaluation_steps=max(len(train_dataloader) // 2, 1),
        save_best_model=True,
        show_progress_bar=True,
    )

    # Save metadata
    metadata = {
        "model": "sbert-academic",
        "base": base_model,
        "epochs": epochs,
        "train_triplets": len(train_examples),
        "val_triplets": len(val_examples),
    }
    with open(output_path / "training_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("SBERT training complete. Model saved to %s", output_path)


def main():
    parser = argparse.ArgumentParser(description="Fine-tune SBERT for academic similarity")
    parser.add_argument("--base", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--output", default="services/shared/models/sbert_academic")
    parser.add_argument("--data", default="ml/data/processed")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=2e-5)
    args = parser.parse_args()

    train_sbert(
        base_model=args.base,
        output_dir=args.output,
        data_dir=args.data,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
    )


if __name__ == "__main__":
    main()

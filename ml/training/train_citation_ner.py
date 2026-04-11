"""Model 1: Train spaCy NER for citation entity extraction.

Entities: AUTHOR, TITLE, JOURNAL, YEAR, VOLUME, PAGES, DOI
Base model: en_core_web_trf (transformer-based)
Target: F1 >= 0.85, format accuracy >= 90%

Usage:
    python ml/training/train_citation_ner.py
    python ml/training/train_citation_ner.py --epochs 50 --output models/ner
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from pathlib import Path

import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ENTITIES = ["AUTHOR", "TITLE", "JOURNAL", "YEAR", "VOLUME", "PAGES", "DOI"]


def load_config(config_path: str = "ml/configs/citation_ner.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def create_training_data() -> list[tuple[str, dict]]:
    """Generate synthetic citation training data with entity spans.

    In production, this should load from ml/data/processed/citations/.
    This provides bootstrap data so the training pipeline can run immediately.
    """
    examples = [
        (
            "Smith, J. and Doe, A. (2023). Deep learning for NLP tasks. Journal of AI Research, 45(2), 123-145. doi:10.1234/jair.2023.001",
            {"entities": [
                (0, 24, "AUTHOR"),
                (33, 60, "TITLE"),
                (62, 84, "JOURNAL"),
                (27, 31, "YEAR"),
                (86, 91, "VOLUME"),
                (94, 101, "PAGES"),
                (103, 128, "DOI"),
            ]}
        ),
        (
            "Brown, T., et al. (2020). Language models are few-shot learners. Advances in Neural Information Processing Systems, 33, 1877-1901.",
            {"entities": [
                (0, 16, "AUTHOR"),
                (25, 63, "TITLE"),
                (65, 110, "JOURNAL"),
                (19, 23, "YEAR"),
                (112, 114, "VOLUME"),
                (116, 125, "PAGES"),
            ]}
        ),
        (
            "Vaswani, A., Shazeer, N., Parmar, N., et al. (2017). Attention is all you need. In NeurIPS 2017.",
            {"entities": [
                (0, 44, "AUTHOR"),
                (53, 79, "TITLE"),
                (84, 96, "JOURNAL"),
                (47, 51, "YEAR"),
            ]}
        ),
        (
            "Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers. In NAACL-HLT, pp. 4171-4186.",
            {"entities": [
                (0, 50, "AUTHOR"),
                (59, 112, "TITLE"),
                (117, 125, "JOURNAL"),
                (53, 57, "YEAR"),
                (131, 140, "PAGES"),
            ]}
        ),
        (
            "LeCun, Y., Bengio, Y., & Hinton, G. (2015). Deep learning. Nature, 521(7553), 436-444. doi:10.1038/nature14539",
            {"entities": [
                (0, 35, "AUTHOR"),
                (44, 57, "TITLE"),
                (59, 65, "JOURNAL"),
                (38, 42, "YEAR"),
                (67, 76, "VOLUME"),
                (79, 86, "PAGES"),
                (88, 112, "DOI"),
            ]}
        ),
    ]
    return examples


def train_ner(
    output_dir: str = "services/module1-integrity/models/citation_ner",
    epochs: int = 30,
    batch_size: int = 16,
    dropout: float = 0.3,
    learning_rate: float = 5e-5,
) -> None:
    """Train the spaCy NER model for citation extraction."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load or create a blank model
    try:
        nlp = spacy.load("en_core_web_trf")
        logger.info("Loaded en_core_web_trf as base model")
    except OSError:
        logger.warning("en_core_web_trf not found, falling back to en_core_web_sm")
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("No spaCy model found, creating blank 'en' model")
            nlp = spacy.blank("en")

    # Add NER pipe if not present
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")

    # Add entity labels
    for entity in ENTITIES:
        ner.add_label(entity)

    # Prepare training data
    raw_data = create_training_data()
    logger.info("Training data: %d examples", len(raw_data))

    # Load additional data if available
    data_dir = Path("ml/data/processed/citations")
    if data_dir.exists():
        for json_file in data_dir.glob("*.json"):
            with open(json_file, "r") as f:
                extra = json.load(f)
            if isinstance(extra, list):
                raw_data.extend([(e["text"], {"entities": e["entities"]}) for e in extra])
        logger.info("Total training data after loading files: %d", len(raw_data))

    # Split data
    random.shuffle(raw_data)
    split_idx = int(len(raw_data) * 0.85)
    train_data = raw_data[:split_idx]
    val_data = raw_data[split_idx:]

    # Convert to spaCy Examples
    train_examples = []
    for text, annotations in train_data:
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, annotations)
        train_examples.append(example)

    # Disable other pipes during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]

    best_f1 = 0.0
    patience_counter = 0
    patience = 5

    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.begin_training()
        optimizer.learn_rate = learning_rate

        for epoch in range(epochs):
            random.shuffle(train_examples)
            losses = {}

            batches = minibatch(train_examples, size=compounding(4, batch_size, 1.001))
            for batch in batches:
                nlp.update(batch, sgd=optimizer, drop=dropout, losses=losses)

            # Evaluate on validation set
            if val_data:
                val_examples = []
                for text, annotations in val_data:
                    doc = nlp.make_doc(text)
                    val_examples.append(Example.from_dict(doc, annotations))

                scores = nlp.evaluate(val_examples)
                f1 = scores.get("ents_f", 0.0)

                logger.info(
                    "Epoch %d/%d — loss: %.4f — val F1: %.4f — P: %.4f — R: %.4f",
                    epoch + 1, epochs,
                    losses.get("ner", 0),
                    f1,
                    scores.get("ents_p", 0),
                    scores.get("ents_r", 0),
                )

                # Save best model
                if f1 > best_f1:
                    best_f1 = f1
                    patience_counter = 0
                    nlp.to_disk(output_path)
                    logger.info("New best model saved (F1=%.4f)", f1)
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        logger.info("Early stopping at epoch %d", epoch + 1)
                        break
            else:
                logger.info("Epoch %d/%d — loss: %.4f", epoch + 1, epochs, losses.get("ner", 0))
                nlp.to_disk(output_path)

    # Save metadata
    metadata = {
        "model": "citation-ner",
        "base": "en_core_web_trf",
        "entities": ENTITIES,
        "best_f1": best_f1,
        "epochs_trained": epoch + 1,
        "train_size": len(train_data),
        "val_size": len(val_data),
    }
    with open(output_path / "training_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Training complete. Best F1=%.4f. Model saved to %s", best_f1, output_path)


def main():
    parser = argparse.ArgumentParser(description="Train Citation NER model")
    parser.add_argument("--output", default="services/module1-integrity/models/citation_ner")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--lr", type=float, default=5e-5)
    args = parser.parse_args()

    train_ner(
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        dropout=args.dropout,
        learning_rate=args.lr,
    )


if __name__ == "__main__":
    main()

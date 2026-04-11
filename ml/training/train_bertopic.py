"""Model 10: BERTopic — Dynamic Topic Discovery.

Architecture: SBERT embeddings → UMAP → HDBSCAN → c-TF-IDF → topic representation
Discovers latent research topics from paper abstracts without predefined categories.

Usage:
    python ml/training/train_bertopic.py
    python ml/training/train_bertopic.py --min-topic-size 10 --nr-topics 30
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np

try:
    from bertopic import BERTopic
    HAS_BERTOPIC = True
except ImportError:
    HAS_BERTOPIC = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_SBERT = True
except ImportError:
    HAS_SBERT = False

try:
    from umap import UMAP
    HAS_UMAP = True
except ImportError:
    HAS_UMAP = False

try:
    from hdbscan import HDBSCAN
    HAS_HDBSCAN = True
except ImportError:
    HAS_HDBSCAN = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_abstracts(data_dir: str) -> list[str]:
    """Load paper abstracts for topic modeling."""
    papers_file = Path(data_dir) / "papers_processed.json"
    if papers_file.exists():
        with open(papers_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        abstracts = [
            p.get("abstract", "")
            for p in papers
            if len(p.get("abstract", "")) > 50
        ]
        if abstracts:
            return abstracts

    logger.warning("No paper data found, using synthetic abstracts")
    return _synthetic_abstracts()


def _synthetic_abstracts() -> list[str]:
    """Generate synthetic abstracts for pipeline testing."""
    topics = {
        "deep_learning": [
            "We propose a novel deep neural network architecture for image recognition that leverages residual connections and attention mechanisms to achieve state-of-the-art accuracy on ImageNet.",
            "This paper presents an efficient training strategy for deep learning models that reduces computational costs by 50% while maintaining comparable performance on standard benchmarks.",
            "A comprehensive survey of deep learning techniques for medical image analysis, covering convolutional networks, U-Net variants, and vision transformers for diagnostic applications.",
            "We introduce a self-supervised pretraining approach for deep neural networks that learns robust visual representations from unlabeled medical imaging data.",
            "Transfer learning with deep convolutional networks for fine-grained visual classification achieves remarkable results on domain-specific datasets with limited labeled samples.",
        ],
        "nlp": [
            "Large language models demonstrate emergent reasoning capabilities when scaled beyond 100 billion parameters, with implications for question answering and mathematical problem solving.",
            "We propose a lightweight transformer architecture for real-time machine translation that reduces latency by 70% compared to standard encoder-decoder models.",
            "Sentiment analysis of social media posts using BERT-based models with domain-specific fine-tuning achieves 95% accuracy on Twitter sentiment benchmarks.",
            "A novel approach to named entity recognition in scientific text combining contextual embeddings with graph neural networks for improved entity boundary detection.",
            "Cross-lingual transfer learning with multilingual BERT enables zero-shot text classification across 50 languages with minimal performance degradation.",
        ],
        "iot_security": [
            "An intrusion detection framework for smart home IoT networks using federated learning to preserve device privacy while maintaining high detection accuracy.",
            "Lightweight cryptographic protocols for resource-constrained IoT devices that provide end-to-end encryption with minimal energy overhead.",
            "Vulnerability assessment of industrial IoT systems reveals critical weaknesses in MQTT and CoAP protocol implementations across major vendors.",
            "Edge computing-based anomaly detection for IoT sensor networks using compressed machine learning models deployed on microcontrollers.",
            "Blockchain-based authentication for IoT device identity management provides tamper-resistant credential verification in decentralized networks.",
        ],
        "cloud_computing": [
            "Microservice orchestration patterns for cloud-native applications comparing Kubernetes, Docker Swarm, and AWS ECS across scalability and fault tolerance metrics.",
            "Serverless computing cost optimization through intelligent function placement and cold start mitigation reduces cloud spending by 40%.",
            "Multi-cloud deployment strategies for disaster recovery and high availability in enterprise applications using infrastructure-as-code automation.",
            "Container security scanning and runtime protection for Kubernetes clusters identifies and remediates vulnerabilities in production environments.",
            "Performance modeling of serverless functions under variable workloads using queuing theory and machine learning-based prediction.",
        ],
        "data_science": [
            "Automated feature engineering using meta-learning for tabular datasets significantly reduces the expertise required for competitive machine learning performance.",
            "A comparative study of explainable AI methods for random forest and gradient boosting models in healthcare prediction tasks.",
            "Time series anomaly detection using variational autoencoders with attention mechanisms for industrial predictive maintenance applications.",
            "Data augmentation strategies for imbalanced classification datasets using SMOTE variants and generative adversarial approaches.",
            "Causal inference methods for observational studies in social science research using propensity score matching and instrumental variables.",
        ],
    }
    abstracts = []
    for topic_abstracts in topics.values():
        abstracts.extend(topic_abstracts * 4)  # Replicate for volume
    return abstracts


def train_bertopic(
    output_dir: str = "services/module3-data/models/bertopic",
    data_dir: str = "ml/data/processed",
    embedding_model: str = "all-MiniLM-L6-v2",
    min_topic_size: int = 5,
    nr_topics: int | None = None,
    n_neighbors: int = 15,
    n_components: int = 5,
    min_cluster_size: int = 5,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if not HAS_BERTOPIC:
        logger.error("bertopic not installed. pip install bertopic")
        metadata = {"model": "bertopic", "status": "skipped", "reason": "bertopic not installed"}
        with open(output_path / "training_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        return

    abstracts = load_abstracts(data_dir)
    logger.info("Loaded %d abstracts for topic modeling", len(abstracts))

    # Configure sub-models
    umap_model = None
    if HAS_UMAP:
        umap_model = UMAP(
            n_neighbors=n_neighbors,
            n_components=n_components,
            min_dist=0.0,
            metric="cosine",
            random_state=42,
        )

    hdbscan_model = None
    if HAS_HDBSCAN:
        hdbscan_model = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=3,
            metric="euclidean",
            prediction_data=True,
        )

    # Build BERTopic model
    kwargs = {
        "language": "english",
        "min_topic_size": min_topic_size,
        "verbose": True,
    }
    if nr_topics is not None:
        kwargs["nr_topics"] = nr_topics
    if umap_model is not None:
        kwargs["umap_model"] = umap_model
    if hdbscan_model is not None:
        kwargs["hdbscan_model"] = hdbscan_model

    if HAS_SBERT:
        kwargs["embedding_model"] = embedding_model

    topic_model = BERTopic(**kwargs)

    logger.info("Fitting BERTopic model...")
    topics, probs = topic_model.fit_transform(abstracts)

    # Get topic info
    topic_info = topic_model.get_topic_info()
    logger.info("Discovered %d topics (including outlier topic -1)", len(topic_info))

    for _, row in topic_info.iterrows():
        if row["Topic"] == -1:
            continue
        topic_words = topic_model.get_topic(row["Topic"])
        words_str = ", ".join([w for w, _ in topic_words[:5]])
        logger.info("  Topic %d (%d docs): %s", row["Topic"], row["Count"], words_str)

    # Save model
    topic_model.save(str(output_path / "bertopic_model"), serialization="safetensors", save_ctfidf=True, save_embedding_model=embedding_model)
    logger.info("Model saved to %s", output_path)

    # Save topic info
    topic_info_dict = topic_info.to_dict(orient="records")
    with open(output_path / "topic_info.json", "w") as f:
        json.dump(topic_info_dict, f, indent=2)

    # Save topic-word distributions
    all_topics = {}
    for topic_id in topic_info["Topic"]:
        if topic_id == -1:
            continue
        words = topic_model.get_topic(topic_id)
        all_topics[str(topic_id)] = [{"word": w, "score": float(s)} for w, s in words]
    with open(output_path / "topic_words.json", "w") as f:
        json.dump(all_topics, f, indent=2)

    # Metadata
    n_outliers = sum(1 for t in topics if t == -1)
    metadata = {
        "model": "bertopic-discovery",
        "embedding_model": embedding_model,
        "num_documents": len(abstracts),
        "num_topics": len(topic_info) - 1,  # exclude outlier
        "num_outliers": n_outliers,
        "outlier_ratio": n_outliers / len(abstracts) if abstracts else 0,
        "min_topic_size": min_topic_size,
    }
    with open(output_path / "training_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("BERTopic training complete. %d topics discovered.", metadata["num_topics"])


def main():
    parser = argparse.ArgumentParser(description="Train BERTopic topic discovery model")
    parser.add_argument("--output", default="services/module3-data/models/bertopic")
    parser.add_argument("--data", default="ml/data/processed")
    parser.add_argument("--embedding-model", default="all-MiniLM-L6-v2")
    parser.add_argument("--min-topic-size", type=int, default=5)
    parser.add_argument("--nr-topics", type=int, default=None)
    args = parser.parse_args()
    train_bertopic(
        output_dir=args.output, data_dir=args.data,
        embedding_model=args.embedding_model,
        min_topic_size=args.min_topic_size,
        nr_topics=args.nr_topics,
    )


if __name__ == "__main__":
    main()

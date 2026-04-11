"""Model 9: GNN Mind Map Generator — GCN for concept relationships.

Architecture: GCN (2-layer) for link prediction between research concepts
Input: Concept graph built from paper co-occurrence and citation networks
Target: Generates structured mind maps from research topic clusters

Usage:
    python ml/training/train_gnn_mindmap.py
    python ml/training/train_gnn_mindmap.py --hidden-dim 128 --epochs 200
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
import torch.nn.functional as F

try:
    import torch_geometric
    from torch_geometric.data import Data
    from torch_geometric.nn import GCNConv
    from torch_geometric.utils import negative_sampling, train_test_split_edges
    HAS_PYG = True
except ImportError:
    HAS_PYG = False

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class GCNLinkPredictor(nn.Module):
    """2-layer GCN for link prediction on concept graphs."""

    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int, dropout: float = 0.3):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)
        self.dropout = dropout

    def encode(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        return x

    def decode(self, z, edge_index):
        """Predict edge probability via dot product."""
        return (z[edge_index[0]] * z[edge_index[1]]).sum(dim=-1)

    def forward(self, x, edge_index, pos_edge_index, neg_edge_index):
        z = self.encode(x, edge_index)
        pos_score = self.decode(z, pos_edge_index)
        neg_score = self.decode(z, neg_edge_index)
        return pos_score, neg_score


def load_concept_graph(data_dir: str) -> tuple[list[str], np.ndarray, list[tuple[int, int]]]:
    """Load concept graph: nodes (concepts), features, edges (relationships).

    Returns: (concept_names, node_features, edge_list)
    """
    graph_file = Path(data_dir) / "concept_graph.json"
    if graph_file.exists():
        with open(graph_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        concepts = data["concepts"]
        features = np.array(data["features"])
        edges = [(e[0], e[1]) for e in data["edges"]]
        return concepts, features, edges

    logger.warning("No concept graph found, generating synthetic graph")
    return _synthetic_graph()


def _synthetic_graph() -> tuple[list[str], np.ndarray, list[tuple[int, int]]]:
    """Generate a synthetic concept graph for pipeline testing."""
    concepts = [
        "Deep Learning", "Neural Networks", "Backpropagation", "Gradient Descent",
        "Convolutional Networks", "Image Classification", "Object Detection", "Segmentation",
        "Transformers", "Attention Mechanism", "BERT", "GPT",
        "Natural Language Processing", "Text Classification", "Machine Translation",
        "Reinforcement Learning", "Q-Learning", "Policy Gradient",
        "Generative Models", "GANs", "VAE", "Diffusion Models",
        "Graph Neural Networks", "Node Classification", "Link Prediction",
        "Federated Learning", "Privacy", "Differential Privacy",
        "Computer Vision", "Feature Extraction",
    ]
    n = len(concepts)

    # Generate feature vectors (simulated embeddings)
    np.random.seed(42)
    features = np.random.randn(n, 64).astype(np.float32)
    # Make related concepts have similar features
    clusters = [
        [0, 1, 2, 3],       # DL fundamentals
        [4, 5, 6, 7, 28, 29],  # vision
        [8, 9, 10, 11],     # transformers
        [12, 13, 14],       # NLP
        [15, 16, 17],       # RL
        [18, 19, 20, 21],   # generative
        [22, 23, 24],       # GNNs
        [25, 26, 27],       # federated/privacy
    ]
    for cluster in clusters:
        center = np.random.randn(64)
        for idx in cluster:
            features[idx] = center + np.random.randn(64) * 0.3

    # Edges: intra-cluster (strong) + some inter-cluster
    edges = []
    for cluster in clusters:
        for i in range(len(cluster)):
            for j in range(i + 1, len(cluster)):
                edges.append((cluster[i], cluster[j]))

    # Inter-cluster edges
    inter_edges = [
        (0, 8), (0, 15), (0, 18), (0, 22),  # DL connects to many
        (8, 12), (10, 13),  # transformers <-> NLP
        (4, 28), (5, 28),   # CNN <-> CV
        (18, 21), (19, 21), # generative connections
        (25, 0), (26, 27),  # federated <-> DL, privacy
    ]
    edges.extend(inter_edges)

    return concepts, features, edges


def train_gnn_mindmap(
    output_dir: str = "services/module4-analytics/models/mindmap",
    data_dir: str = "ml/data/processed",
    hidden_dim: int = 128,
    out_dim: int = 64,
    epochs: int = 200,
    learning_rate: float = 0.01,
    dropout: float = 0.3,
) -> None:
    if not HAS_PYG:
        logger.error("torch-geometric not installed. pip install torch-geometric")
        logger.info("Saving placeholder metadata only.")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        metadata = {"model": "gnn-mindmap", "status": "skipped", "reason": "torch-geometric not installed"}
        with open(output_path / "training_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        return

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)

    concepts, features, edge_list = load_concept_graph(data_dir)
    logger.info("Graph: %d concepts, %d edges", len(concepts), len(edge_list))

    # Build PyG Data object
    x = torch.tensor(features, dtype=torch.float32)
    edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
    # Make undirected
    edge_index = torch.cat([edge_index, edge_index.flip(0)], dim=1)

    data = Data(x=x, edge_index=edge_index)
    data = train_test_split_edges(data, val_ratio=0.1, test_ratio=0.15)
    data = data.to(device)

    model = GCNLinkPredictor(
        in_channels=features.shape[1],
        hidden_channels=hidden_dim,
        out_channels=out_dim,
        dropout=dropout,
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    best_auc = 0.0

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()

        # Negative sampling
        neg_edge_index = negative_sampling(
            edge_index=data.train_pos_edge_index,
            num_nodes=data.num_nodes,
            num_neg_samples=data.train_pos_edge_index.size(1),
        )

        pos_score, neg_score = model(
            data.x, data.train_pos_edge_index,
            data.train_pos_edge_index, neg_edge_index,
        )

        pos_loss = F.binary_cross_entropy_with_logits(pos_score, torch.ones_like(pos_score))
        neg_loss = F.binary_cross_entropy_with_logits(neg_score, torch.zeros_like(neg_score))
        loss = pos_loss + neg_loss
        loss.backward()
        optimizer.step()

        # Validate every 20 epochs
        if (epoch + 1) % 20 == 0:
            model.eval()
            with torch.no_grad():
                z = model.encode(data.x, data.train_pos_edge_index)
                val_pos_score = model.decode(z, data.val_pos_edge_index)
                val_neg_edge = negative_sampling(
                    edge_index=data.train_pos_edge_index,
                    num_nodes=data.num_nodes,
                    num_neg_samples=data.val_pos_edge_index.size(1),
                )
                val_neg_score = model.decode(z, val_neg_edge)

                scores = torch.cat([val_pos_score, val_neg_score]).sigmoid().cpu().numpy()
                labels = np.concatenate([
                    np.ones(val_pos_score.size(0)),
                    np.zeros(val_neg_score.size(0)),
                ])
                from sklearn.metrics import roc_auc_score
                auc = roc_auc_score(labels, scores)

            logger.info("Epoch %d/%d — loss: %.4f — val AUC: %.4f", epoch + 1, epochs, loss.item(), auc)

            if auc > best_auc:
                best_auc = auc
                torch.save(model.state_dict(), output_path / "model.pt")

    # Save concept mapping
    with open(output_path / "concepts.json", "w") as f:
        json.dump(concepts, f, indent=2)

    metadata = {
        "model": "gnn-mindmap",
        "type": "gcn-link-prediction",
        "num_concepts": len(concepts),
        "num_edges": len(edge_list),
        "hidden_dim": hidden_dim,
        "out_dim": out_dim,
        "best_val_auc": best_auc,
        "epochs": epochs,
    }
    with open(output_path / "training_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("GNN mind map training complete. Best AUC=%.4f", best_auc)


def main():
    parser = argparse.ArgumentParser(description="Train GNN mind map generator")
    parser.add_argument("--output", default="services/module4-analytics/models/mindmap")
    parser.add_argument("--data", default="ml/data/processed")
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--out-dim", type=int, default=64)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--lr", type=float, default=0.01)
    args = parser.parse_args()
    train_gnn_mindmap(
        output_dir=args.output, data_dir=args.data,
        hidden_dim=args.hidden_dim, out_dim=args.out_dim,
        epochs=args.epochs, learning_rate=args.lr,
    )


if __name__ == "__main__":
    main()

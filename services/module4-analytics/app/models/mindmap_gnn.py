"""Model wrapper for GNN Mind Map Generator — inference time."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "mindmap"

try:
    from torch_geometric.nn import GCNConv
    HAS_PYG = True
except ImportError:
    HAS_PYG = False


class _GCNEncoder(nn.Module):
    """GCN encoder for concept embeddings."""

    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int, dropout: float = 0.3):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)
        self.dropout = dropout

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        return x


class MindMapGNNModel:
    """Wrapper for the trained GCN mind map model."""

    def __init__(self, model_dir: str | Path | None = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._model = None
        self.concepts: list[str] = []
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load(self) -> None:
        if not HAS_PYG:
            logger.error("torch-geometric not installed")
            return

        concepts_path = self.model_dir / "concepts.json"
        if concepts_path.exists():
            with open(concepts_path) as f:
                self.concepts = json.load(f)

        weights_path = self.model_dir / "model.pt"
        if weights_path.exists():
            # Infer dimensions from metadata
            metadata_path = self.model_dir / "training_metadata.json"
            hidden_dim, out_dim, in_dim = 128, 64, 64
            if metadata_path.exists():
                with open(metadata_path) as f:
                    meta = json.load(f)
                hidden_dim = meta.get("hidden_dim", 128)
                out_dim = meta.get("out_dim", 64)

            self._model = _GCNEncoder(in_dim, hidden_dim, out_dim)
            self._model.load_state_dict(torch.load(weights_path, map_location=self.device, weights_only=True))
            self._model = self._model.to(self.device).eval()
            logger.info("Loaded GNN mind map model from %s", self.model_dir)
        else:
            logger.warning("No GNN model weights at %s", weights_path)

    def generate_mindmap(self, seed_concepts: list[str], max_nodes: int = 20, threshold: float = 0.5) -> dict:
        """Generate a mind map structure from seed concepts.

        Returns: {nodes: [{id, label}], edges: [{source, target, weight}]}
        """
        if not self.concepts:
            self.load()

        # Find matching concept indices
        seed_indices = []
        for concept in seed_concepts:
            concept_lower = concept.lower()
            for i, c in enumerate(self.concepts):
                if concept_lower in c.lower() or c.lower() in concept_lower:
                    seed_indices.append(i)
                    break

        if not seed_indices:
            # Return a basic structure from seed concepts
            nodes = [{"id": i, "label": c} for i, c in enumerate(seed_concepts)]
            edges = [{"source": 0, "target": i, "weight": 0.5} for i in range(1, len(nodes))]
            return {"nodes": nodes, "edges": edges}

        # Build mind map from related concepts
        related = set(seed_indices)
        nodes = []
        edges = []

        # Add seed nodes
        for idx in seed_indices:
            nodes.append({"id": idx, "label": self.concepts[idx], "is_seed": True})

        # Add related concepts (nearest neighbors by index proximity as fallback)
        for idx in seed_indices:
            for offset in range(-3, 4):
                neighbor = idx + offset
                if 0 <= neighbor < len(self.concepts) and neighbor not in related:
                    related.add(neighbor)
                    nodes.append({"id": neighbor, "label": self.concepts[neighbor], "is_seed": False})
                    edges.append({
                        "source": idx,
                        "target": neighbor,
                        "weight": round(0.8 - abs(offset) * 0.1, 2),
                    })
                if len(nodes) >= max_nodes:
                    break
            if len(nodes) >= max_nodes:
                break

        # Add edges between seed nodes
        for i in range(len(seed_indices)):
            for j in range(i + 1, len(seed_indices)):
                edges.append({
                    "source": seed_indices[i],
                    "target": seed_indices[j],
                    "weight": 0.9,
                })

        return {"nodes": nodes, "edges": edges}

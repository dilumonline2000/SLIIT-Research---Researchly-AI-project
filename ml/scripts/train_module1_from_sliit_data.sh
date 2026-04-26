#!/bin/bash
# Complete Module 1 training pipeline using SLIIT repository data

set -e

echo ""
echo "======================================================================"
echo "  MODULE 1 TRAINING PIPELINE (SLIIT Data)"
echo "======================================================================"
echo ""

# Step 1: Install dependencies
echo "[1/5] Installing dependencies..."
pip install beautifulsoup4 httpx pyyaml -q

# Step 2: Scrape SLIIT repository
echo "[2/5] Scraping SLIIT repository (this may take a few minutes)..."
python ml/scripts/scrape_sliit_repository.py --pages 50 --output ml/data/raw/sliit_papers

echo ""
echo "[3/5] Training Citation NER model..."
python ml/training/train_citation_ner.py --epochs 30

echo ""
echo "[4/5] Training SBERT model (for plagiarism/gap detection)..."
python ml/training/train_sbert.py --task plagiarism --epochs 15

echo ""
echo "[5/5] Training Proposal Generator (LoRA fine-tune)..."
python ml/training/train_proposal_generator.py --epochs 3 --batch-size 1

echo ""
echo "======================================================================"
echo "  TRAINING COMPLETE!"
echo "======================================================================"
echo ""
echo "Models saved to:"
echo "  - services/module1-integrity/models/citation_ner/"
echo "  - services/module1-integrity/models/sbert_plagiarism/"
echo "  - services/module1-integrity/models/proposal_generator/"
echo ""

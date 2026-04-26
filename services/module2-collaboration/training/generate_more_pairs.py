"""
Generate additional training pairs to improve model accuracy.
Adds 50+ more student query examples covering all research domains from the PDF supervisor dataset.

Run:
    python training/generate_more_pairs.py

Output:
    Appends new pairs to data/training_pairs.json
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PAIRS_F = DATA_DIR / "training_pairs.json"

# Additional training pairs – domain-specific student queries
# Format: (student_query, supervisor_id, label)
# Covers supervisors from the full 74-supervisor list that weren't in original 65 pairs

NEW_PAIRS = [
    # --- NLP / Language AI (Supervisor IDs: 1, 2, 4, 26, 33, 39, 56, 65, 68) ---
    ("I am building a Sinhala language NLP system for sentiment analysis", 1, 1),
    ("My project involves fine-tuning BERT for named entity recognition", 56, 1),
    ("I want to create a multilingual text classification system using transformers", 2, 1),
    ("My research is about question answering systems using large language models", 4, 1),
    ("I am developing a research paper summarization tool using T5", 33, 1),
    ("My project uses GPT models for automatic essay grading", 26, 1),
    ("I want to study topic modeling using LDA and BERTopic", 39, 1),
    ("My research involves information extraction from legal documents", 2, 1),
    ("I am working on computational linguistics and parsing", 26, 1),

    # --- Machine Learning / Deep Learning (IDs: 6, 12, 13, 18, 20, 42, 50, 24) ---
    ("I am implementing a random forest model for student performance prediction", 6, 1),
    ("My project is about federated learning for privacy-preserving ML", 13, 1),
    ("I want to research explainable AI for medical diagnosis", 18, 1),
    ("My research involves transfer learning for low-resource classification", 42, 1),
    ("I am building a GAN for data augmentation in medical imaging", 20, 1),
    ("My project is about multi-objective optimization in neural architecture search", 42, 1),
    ("I want to study spiking neural networks for energy-efficient AI", 24, 1),
    ("My research involves ensemble methods for fraud detection", 50, 1),
    ("I am researching graph neural networks for knowledge representation", 13, 1),

    # --- Computer Vision (IDs: 20, 37, 41, 62, 65, 21) ---
    ("I am developing a real-time object detection system using YOLO", 41, 1),
    ("My project is about image segmentation for autonomous vehicles", 20, 1),
    ("I want to research facial recognition with privacy preservation", 65, 1),
    ("My research involves 3D reconstruction from 2D images", 37, 1),
    ("I am building a plant disease detection system from leaf images", 41, 1),
    ("My project involves semantic segmentation for medical imaging", 20, 1),
    ("I want to study audio restoration and speech processing", 21, 1),

    # --- IoT / Smart Systems (IDs: 3, 16, 35, 36, 54, 67, 57) ---
    ("My project uses Raspberry Pi and sensors for smart energy monitoring", 16, 1),
    ("I am researching LoRaWAN networks for long-range IoT communication", 67, 1),
    ("My research involves digital twin systems for industrial IoT", 54, 1),
    ("I want to study SDN for managing IoT network traffic", 35, 1),
    ("My project is about predictive maintenance using IoT sensor data", 54, 1),
    ("I am building a smart water management system using IoT", 3, 1),
    ("My research involves 6G wireless communication systems", 67, 1),

    # --- Cyber Security (IDs: 15, 30, 38, 53, 69, 71, 22) ---
    ("My research involves adversarial attacks on deep learning models", 15, 1),
    ("I am developing a blockchain-based identity management system", 22, 1),
    ("My project is about zero-trust architecture for enterprise networks", 53, 1),
    ("I want to study malware detection using machine learning", 15, 1),
    ("My research involves privacy-preserving data sharing techniques", 38, 1),
    ("I am researching threat modeling in critical infrastructure", 53, 1),
    ("My project involves digital forensics and incident response", 69, 1),

    # --- Education Technology (IDs: 5, 6, 14, 29, 32, 45, 51) ---
    ("I am building a gamified learning platform for programming education", 14, 1),
    ("My project is about automatic quiz generation from lecture notes", 6, 1),
    ("I want to study student engagement prediction in online courses", 5, 1),
    ("My research involves AR for interactive science education", 52, 1),
    ("I am developing a peer review system for university assignments", 29, 1),
    ("My project is about learning analytics for education technology", 14, 1),
    ("I want to create an assistive technology system for accessibility", 51, 1),

    # --- Data Science / Analytics (IDs: 12, 13, 17, 18, 49, 56, 17, 48, 59) ---
    ("My project is about real-time dashboard for hospital patient monitoring", 48, 1),
    ("I am researching time series forecasting for stock market prediction", 18, 1),
    ("My research involves data lineage tracking in ETL pipelines", 49, 1),
    ("I want to build a recommendation engine for e-commerce", 14, 1),
    ("My project is about clustering algorithms for customer segmentation", 17, 1),
    ("I am researching big data management for business intelligence", 49, 1),
    ("My project involves data visualization and interactive dashboards", 28, 1),

    # --- Networking / Systems / Communications (IDs: 57, 63, 67, 71, 36, 34) ---
    ("I am researching software-defined networking for cloud data centres", 57, 1),
    ("My project involves QoS optimization in 5G/6G networks", 67, 1),
    ("I want to study network topology discovery using graph algorithms", 71, 1),
    ("My research is about intelligent systems for network automation", 63, 1),
    ("I am building a cloud communication platform with security", 36, 1),
    ("My project involves social network analysis for collaboration", 34, 1),

    # --- Software Engineering (IDs: 9, 25, 50, 59, 61) ---
    ("My research is about software complexity metrics and refactoring", 9, 1),
    ("I am developing AR/VR applications for immersive experiences", 9, 1),
    ("My project is about mobile development for cross-platform apps", 9, 1),
    ("I want to study HCI design principles for better user interfaces", 25, 1),
    ("My research involves code quality and automated testing", 50, 1),

    # --- Specialized Domains (IDs: 27, 28, 31, 40, 43, 44, 46, 47) ---
    ("I am researching network protocols and assistive technologies", 27, 1),
    ("My project involves geospatial information systems and mapping", 37, 1),
    ("I want to study keystroke dynamics for biometric authentication", 31, 1),
    ("My research is about software engineering complexity metrics", 40, 1),
    ("I am building an educational software with gamification", 45, 1),
    ("My project involves image processing for healthcare applications", 44, 1),
    ("I want to research cloud computing and distributed systems", 46, 1),
    ("My research involves security and privacy in ML systems", 47, 1),

    # --- Hard Negatives (label=0 - wrong domain/mismatch) ---
    ("I want to build a deep learning image classifier", 69, 0),  # Cyber security domain
    ("My research is about network security firewalls", 20, 0),   # Computer vision domain
    ("I am studying e-learning engagement analytics", 67, 0),    # Wireless communications
    ("My project is about speech synthesis using AI", 53, 0),    # Security domain
    ("I want to research blockchain for supply chain", 41, 0),   # Computer vision
    ("My research is about data visualization dashboards", 3, 0),  # Smart agriculture
    ("I am building an NLP chatbot for customer service", 57, 0), # Networking
    ("My project involves deep learning for cancer detection", 25, 0),  # HCI
    ("I want to study cybersecurity threat modeling", 1, 0),     # NLP domain
    ("My research is about AR/VR museum applications", 69, 0),   # Cyber security
]


def append_pairs():
    """Load existing pairs, append new ones, deduplicate, and save."""
    with open(PAIRS_F, encoding="utf-8") as f:
        existing = json.load(f)

    before = len(existing)
    combined = existing + NEW_PAIRS

    # Deduplicate by (query, sup_id)
    seen = set()
    deduped = []
    for pair in combined:
        key = (pair[0], pair[1])
        if key not in seen:
            seen.add(key)
            deduped.append(pair)

    with open(PAIRS_F, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)

    positive = sum(1 for p in deduped if p[2] == 1)
    negative = sum(1 for p in deduped if p[2] == 0)

    print(f"\n[+] Training pairs augmented:")
    print(f"  Before: {before} pairs")
    print(f"  After:  {len(deduped)} pairs (+{len(deduped) - before} new)")
    print(f"  Positive (label=1): {positive}")
    print(f"  Negative (label=0): {negative}")
    print(f"\n  File: {PAIRS_F}\n")


if __name__ == "__main__":
    append_pairs()

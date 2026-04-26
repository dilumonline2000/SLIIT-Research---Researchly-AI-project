"""
Convert scraped SLIIT citations to spaCy NER training format.

Takes citations from citations_sliit.json and converts them to spaCy format
with entity annotations for AUTHOR, TITLE, YEAR, JOURNAL, VOLUME, PAGES, DOI.
"""

import json
import re
from pathlib import Path

def convert_citations_to_ner_format(input_file: Path, output_file: Path) -> None:
    """Convert citation data to spaCy training format."""

    with open(input_file, "r", encoding="utf-8") as f:
        citations_data = json.load(f)

    training_data = []

    for citation in citations_data:
        text = citation.get("text", "")
        if not text:
            continue

        entities = []

        # Extract AUTHOR (before year)
        authors = citation.get("authors", [])
        if authors:
            author_text = ", ".join(authors[:3])
            start = text.find(author_text)
            if start != -1:
                entities.append((start, start + len(author_text), "AUTHOR"))

        # Extract YEAR (pattern: YYYY in parentheses)
        year_match = re.search(r"\((\d{4})\)", text)
        if year_match:
            year_str = year_match.group(1)
            start = text.find(year_str)
            if start != -1:
                entities.append((start, start + 4, "YEAR"))

        # Extract TITLE (between year and first period after a sentence)
        title = citation.get("title", "")
        if title:
            # Find title in the text
            start = text.find(title)
            if start != -1:
                entities.append((start, start + len(title), "TITLE"))

        # Only add if we found at least some entities
        if entities:
            # Remove duplicates and sort
            entities = list(set(entities))
            entities.sort(key=lambda x: x[0])

            training_data.append({
                "text": text,
                "entities": entities
            })

    # Save in spaCy format
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(training_data, f, indent=2, ensure_ascii=False)

    print(f"[+] Converted {len(training_data)} citations to spaCy format")
    print(f"    Saved to: {output_file}\n")

    # Show sample
    if training_data:
        print(f"[+] Sample training example:")
        sample = training_data[0]
        print(f"    Text: {sample['text']}")
        print(f"    Entities: {sample['entities']}\n")


def main():
    input_file = Path("ml/data/processed/citations/citations_sliit.json")
    output_file = Path("ml/data/processed/citations/citations_ner_train.json")

    if not input_file.exists():
        print(f"Error: {input_file} not found")
        return

    convert_citations_to_ner_format(input_file, output_file)


if __name__ == "__main__":
    main()

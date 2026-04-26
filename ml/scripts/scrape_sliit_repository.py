"""
Scrape SLIIT Research Repository (rda.sliit.lk) using DSpace REST API.

Usage:
    python ml/scripts/scrape_sliit_repository.py --pages 20 --output ml/data/raw/sliit_papers
    python ml/scripts/scrape_sliit_repository.py --pages 50

Downloads:
    - Paper metadata via DSpace API (title, authors, abstract, date)
    - Creates datasets for Module 1 models:
      * Citations (for Citation NER training)
      * Proposals (for Proposal Generator training)
      * Documents (for SBERT plagiarism/gap detection)
"""

import argparse
import json
import logging
import re
import time
from pathlib import Path
from typing import Optional

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://rda.sliit.lk/server/api/discover/search/objects"
TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 0.5  # Be respectful to the server


def scrape_page(session: httpx.Client, page_num: int, page_size: int = 20) -> list[dict]:
    """Scrape a single page using DSpace REST API."""
    params = {
        "size": page_size,
        "page": page_num - 1,  # DSpace uses 0-based indexing
        "sort": "dc.date.accessioned,desc"
    }

    logger.info(f"Scraping page {page_num} (items {(page_num-1)*page_size}-{page_num*page_size})")

    try:
        response = session.get(BASE_URL, params=params, timeout=TIMEOUT)
        response.raise_for_status()
    except httpx.RequestError as e:
        logger.error(f"Request failed for page {page_num}: {e}")
        return []

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON for page {page_num}: {e}")
        return []

    papers = []

    # Navigate the nested structure: _embedded -> searchResult -> _embedded -> objects
    try:
        objects = data.get('_embedded', {}).get('searchResult', {}).get('_embedded', {}).get('objects', [])
    except (AttributeError, TypeError):
        logger.warning(f"Unexpected API response structure on page {page_num}")
        return papers

    for obj in objects:
        try:
            paper = parse_paper_object(obj)
            if paper:
                papers.append(paper)
        except Exception as e:
            logger.debug(f"Error parsing item: {e}")
            continue

    logger.info(f"Extracted {len(papers)} papers from page {page_num}")
    time.sleep(DELAY_BETWEEN_REQUESTS)  # Be respectful
    return papers


def parse_paper_object(obj) -> Optional[dict]:
    """Extract paper metadata from DSpace API object."""
    try:
        # Get the indexableObject which contains actual metadata
        indexable = obj.get('_embedded', {}).get('indexableObject', {})

        if not indexable:
            return None

        paper = {
            "id": indexable.get("uuid"),
            "title": indexable.get("name", ""),
            "handle": indexable.get("handle", ""),
            "url": f"https://rda.sliit.lk/handle/{indexable.get('handle', '')}",
        }

        metadata = indexable.get("metadata", {})

        # Authors
        authors = []
        author_meta = metadata.get("dc.contributor.author", [])
        if author_meta:
            authors = [a.get("value", "").strip() for a in author_meta if a.get("value")]

        paper["authors"] = authors

        # Abstract
        abstract_meta = metadata.get("dc.description.abstract", [])
        abstract = ""
        if abstract_meta:
            abstract = abstract_meta[0].get("value", "").strip()

        paper["abstract"] = abstract

        # Date
        date_issued_meta = metadata.get("dc.date.issued", [])
        year = None
        date_str = ""

        if date_issued_meta:
            date_str = date_issued_meta[0].get("value", "").strip()
            # Extract year from date string (format: YYYY-MM-DD or YYYY)
            year_match = re.search(r"(\d{4})", date_str)
            if year_match:
                year = int(year_match.group(1))

        paper["year"] = year
        paper["date"] = date_str

        # Publication type
        publication_type_meta = metadata.get("dc.type", [])
        publication_type = "Publication"
        if publication_type_meta:
            publication_type = publication_type_meta[0].get("value", "Publication").strip()

        paper["publication_type"] = publication_type

        # Other useful metadata
        paper["language"] = metadata.get("dc.language", [{}])[0].get("value") if metadata.get("dc.language") else None
        paper["subject"] = [s.get("value", "") for s in metadata.get("dc.subject", [])]

        return paper

    except Exception as e:
        logger.debug(f"Error parsing object: {e}")
        return None


def scrape_repository(num_pages: int = 10) -> list[dict]:
    """Scrape multiple pages from SLIIT repository."""
    all_papers = []

    with httpx.Client() as session:
        # Set a realistic user agent
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        for page in range(1, num_pages + 1):
            papers = scrape_page(session, page)
            all_papers.extend(papers)

            if not papers:
                logger.warning(f"No papers on page {page}, stopping")
                break

    return all_papers


def create_citation_dataset(papers: list[dict], output_path: Path) -> None:
    """Format papers for Citation NER training (extract citations)."""
    citations = []

    for paper in papers:
        # Create formatted citations from paper metadata
        authors_list = paper.get("authors", [])[:3]  # First 3 authors
        if not authors_list:
            continue

        authors = ", ".join(authors_list)
        title = paper.get("title", "").strip()
        year = paper.get("year")

        if authors and title and year:
            # Create citation in various formats for diversity
            citation = f"{authors} ({year}). {title}."
            citations.append({
                "text": citation,
                "source_url": paper.get("url", ""),
                "title": title,
                "authors": authors_list,
                "year": year
            })

    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "citations_sliit.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(citations, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(citations)} citations to {output_file}")


def create_proposal_dataset(papers: list[dict], output_path: Path) -> None:
    """Format papers for Proposal Generator training."""
    proposals = []

    for paper in papers:
        abstract = (paper.get("abstract") or "").strip()
        title = (paper.get("title") or "").strip()

        # Abstract can serve as context, generate proposal-like structure
        if abstract and len(abstract) > 50:  # Only if substantial abstract
            proposal = {
                "abstract": abstract,
                "title": title,
                "authors": paper.get("authors", []),
                "year": paper.get("year"),
                "source_url": paper.get("url", ""),
                # Template proposal structure (can be filled by user later)
                "proposal": {
                    "problem_statement": abstract[:150],  # First 150 chars as problem
                    "objectives": "",  # User to fill
                    "methodology": "",  # User to fill
                    "expected_outcomes": ""  # User to fill
                }
            }
            proposals.append(proposal)

    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "proposals_sliit.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(proposals, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(proposals)} proposals to {output_file}")


def create_document_pairs_dataset(papers: list[dict], output_path: Path) -> None:
    """Create document pairs for SBERT similarity/plagiarism training."""
    pairs = []

    # Create pairs with similar papers (by keyword matching)
    for i, paper1 in enumerate(papers):
        abstract1 = ((paper1.get("abstract") or "") or "").lower()
        title1 = ((paper1.get("title") or "") or "").lower()
        subject1 = set(paper1.get("subject", []))

        if not abstract1 or not title1:
            continue

        # Find papers with similar topics
        for j, paper2 in enumerate(papers[i+1:], start=i+1):
            abstract2 = ((paper2.get("abstract") or "") or "").lower()
            title2 = ((paper2.get("title") or "") or "").lower()
            subject2 = set(paper2.get("subject", []))

            if not abstract2 or not title2:
                continue

            # Simple similarity: word overlap + subject match
            words1 = set(re.findall(r"\b\w{4,}\b", abstract1 + title1))
            words2 = set(re.findall(r"\b\w{4,}\b", abstract2 + title2))

            if words1 and words2:
                word_overlap = len(words1 & words2) / max(len(words1 | words2), 1)
                subject_overlap = len(subject1 & subject2) / max(len(subject1 | subject2), 1) if (subject1 or subject2) else 0

                # Combine scores
                similarity = (word_overlap * 0.7 + subject_overlap * 0.3)

                # Only keep high-overlap pairs (similar) or no-overlap (dissimilar)
                if similarity > 0.25 or similarity < 0.05:
                    pair = {
                        "text1": abstract1[:250],
                        "text2": abstract2[:250],
                        "similarity": round(min(similarity, 1.0), 2),
                        "label": "similar" if similarity > 0.25 else "dissimilar",
                        "paper1": paper1.get("title"),
                        "paper2": paper2.get("title")
                    }
                    pairs.append(pair)

            # Limit pairs to avoid explosion
            if len(pairs) >= 500:
                break

        if len(pairs) >= 500:
            break

    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "document_pairs_sliit.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(pairs, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(pairs)} document pairs to {output_file}")


def save_raw_papers(papers: list[dict], output_path: Path) -> None:
    """Save raw paper metadata."""
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "papers_raw_sliit.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(papers)} raw papers to {output_file}")

    # Print summary
    total_with_abstract = sum(1 for p in papers if p.get("abstract", "").strip())
    total_with_authors = sum(1 for p in papers if p.get("authors"))
    avg_abstract_len = sum(len(p.get("abstract", "")) for p in papers) / max(len(papers), 1)

    print(f"\n{'='*70}")
    print(f"  REPOSITORY DATA SUMMARY")
    print(f"{'='*70}")
    print(f"Total papers:             {len(papers)}")
    print(f"With abstracts:           {total_with_abstract}")
    print(f"With authors:             {total_with_authors}")
    print(f"Avg abstract length:      {avg_abstract_len:.0f} chars")
    print(f"Saved to:                 {output_file}")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Scrape SLIIT Research Repository")
    parser.add_argument("--pages", type=int, default=10, help="Number of pages to scrape (default: 10)")
    parser.add_argument("--output", default="ml/data/raw/sliit_papers", help="Output directory")
    args = parser.parse_args()

    output_path = Path(args.output)

    print(f"\n{'='*70}")
    print(f"  SCRAPING SLIIT RESEARCH REPOSITORY")
    print(f"  Using DSpace REST API")
    print(f"{'='*70}\n")

    # Scrape papers
    papers = scrape_repository(num_pages=args.pages)

    if not papers:
        logger.error("No papers scraped. Check your internet connection.")
        return

    # Save raw data
    save_raw_papers(papers, output_path)

    # Create training datasets
    print("[+] Creating training datasets...\n")
    create_citation_dataset(papers, Path("ml/data/processed/citations"))
    create_proposal_dataset(papers, Path("ml/data/processed/proposals"))
    create_document_pairs_dataset(papers, Path("ml/data/processed/documents"))

    print(f"[+] Training datasets created in:")
    print(f"    - ml/data/processed/citations/citations_sliit.json")
    print(f"    - ml/data/processed/proposals/proposals_sliit.json")
    print(f"    - ml/data/processed/documents/document_pairs_sliit.json\n")


if __name__ == "__main__":
    main()

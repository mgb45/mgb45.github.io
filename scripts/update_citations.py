#!/usr/bin/env python3
"""Sync ``_data/citations.csv`` with a Google Scholar profile.

This script fetches the publication list for a Google Scholar author profile
(using the free ``scholarly`` package) and merges it into the existing
``_data/citations.csv`` file that powers the Publications page.

Merging (rather than overwriting) means:
  * Publications already in the CSV are matched to Scholar entries by a
    normalized title, and fields that Scholar can supply (Authors,
    Publication, Year, Volume, Number, Pages, Publisher) are refreshed.
  * Fields Scholar does not provide (DOI, PDF, Code, BibTeX, ...) are left
    untouched, so manually curated links are never lost.
  * New publications found on Scholar are appended.
  * Existing rows that are no longer on Scholar are kept as-is (Scholar is
    not treated as the source of truth for removals).

Usage:
    python scripts/update_citations.py --scholar-id SCHOLAR_USER_ID \
        --csv-path _data/citations.csv

The script exits with a non-zero status if it cannot fetch data from
Google Scholar, so a failed run is never mistaken for "no changes".
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any

FIELDNAMES = [
    "Authors",
    "Title",
    "Publication",
    "Volume",
    "Number",
    "Pages",
    "Year",
    "Publisher",
    "DOI",
    "PDF",
    "Code",
]

# Fields that Google Scholar can supply and that are safe to auto-refresh.
AUTO_FIELDS = ["Authors", "Publication", "Volume", "Number", "Pages", "Year", "Publisher"]


def normalize_title(title: str) -> str:
    """Normalize a title for fuzzy-free exact matching between sources."""
    title = title.lower().strip()
    title = re.sub(r"[^a-z0-9]+", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def read_existing_csv(csv_path: Path) -> tuple[list[dict[str, str]], bool]:
    """Read the existing CSV, returning rows and whether a BOM was present."""
    if not csv_path.exists():
        return [], True

    raw = csv_path.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(text.splitlines())
    rows = [dict(row) for row in reader]
    return rows, has_bom


def fetch_scholar_publications(scholar_id: str) -> list[dict[str, str]]:
    """Fetch publications for a Google Scholar profile using ``scholarly``."""
    try:
        from scholarly import scholarly
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise SystemExit(
            "The 'scholarly' package is required. Install it with "
            "'pip install -r scripts/requirements.txt'."
        ) from exc

    try:
        author = scholarly.search_author_id(scholar_id)
        author = scholarly.fill(author, sections=["publications"])
    except Exception as exc:  # noqa: BLE001 - surface any scraping failure
        raise SystemExit(f"Failed to fetch Google Scholar profile '{scholar_id}': {exc}") from exc

    publications: list[dict[str, str]] = []
    for pub in author.get("publications", []):
        try:
            pub = scholarly.fill(pub)
        except Exception as exc:  # noqa: BLE001
            print(f"Warning: failed to expand a publication entry: {exc}", file=sys.stderr)
            continue

        bib: dict[str, Any] = pub.get("bib", {})
        title = str(bib.get("title", "")).strip()
        if not title:
            continue

        authors_raw = bib.get("author", "")
        authors = "; ".join(a.strip() for a in authors_raw.split(" and ") if a.strip())
        if authors:
            authors += "; "

        publications.append(
            {
                "Authors": authors,
                "Title": title,
                "Publication": str(bib.get("citation", bib.get("venue", ""))).strip(),
                "Volume": str(bib.get("volume", "")).strip(),
                "Number": str(bib.get("number", "")).strip(),
                "Pages": str(bib.get("pages", "")).strip(),
                "Year": str(bib.get("pub_year", "")).strip(),
                "Publisher": str(bib.get("publisher", "")).strip(),
            }
        )

    if not publications:
        raise SystemExit(
            f"No publications were returned for Google Scholar profile '{scholar_id}'; "
            "aborting without writing changes."
        )

    return publications


def merge_publications(
    existing_rows: list[dict[str, str]], scholar_pubs: list[dict[str, str]]
) -> tuple[list[dict[str, str]], int, int]:
    """Merge Scholar publications into the existing rows.

    Returns the merged rows plus counts of (updated, added) entries.
    """
    by_title = {normalize_title(row.get("Title", "")): row for row in existing_rows}
    updated = 0
    added = 0

    for pub in scholar_pubs:
        key = normalize_title(pub["Title"])
        if not key:
            continue

        if key in by_title:
            row = by_title[key]
            changed = False
            for field in AUTO_FIELDS:
                new_value = pub.get(field, "")
                if new_value and row.get(field, "") != new_value:
                    row[field] = new_value
                    changed = True
            if changed:
                updated += 1
        else:
            new_row = {field: "" for field in FIELDNAMES}
            new_row.update({k: v for k, v in pub.items() if k in FIELDNAMES})
            existing_rows.append(new_row)
            by_title[key] = new_row
            added += 1

    return existing_rows, updated, added


def write_csv(csv_path: Path, rows: list[dict[str, str]], has_bom: bool) -> None:
    encoding = "utf-8-sig" if has_bom else "utf-8"
    with csv_path.open("w", encoding=encoding, newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDNAMES})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scholar-id",
        required=True,
        help="Google Scholar author profile ID (the 'user=' value from the profile URL).",
    )
    parser.add_argument(
        "--csv-path",
        default="_data/citations.csv",
        help="Path to the citations CSV file to update (default: _data/citations.csv).",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    existing_rows, has_bom = read_existing_csv(csv_path)
    scholar_pubs = fetch_scholar_publications(args.scholar_id)
    merged_rows, updated, added = merge_publications(existing_rows, scholar_pubs)
    write_csv(csv_path, merged_rows, has_bom)

    print(f"Merged Google Scholar data: {added} new publication(s), {updated} updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

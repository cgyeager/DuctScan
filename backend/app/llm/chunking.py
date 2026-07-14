"""
Chunking strategy — split parsed pages into retrievable text chunks.
"""

import glob
import os
import re
from collections import Counter
from pathlib import Path

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter

HEADER_PATTERNS = [
    # 210.4, 220.12  — decimal section number, then a title.
    # ^        anchor to start of line
    # \d+      one or more digits   (210)
    # \.       a literal dot
    # \d+      one or more digits   (4)
    # \s+      whitespace before the title
    # \S       at least one non-space char (a real title follows)
    re.compile(r'^\d+\.\d+\s+\S'),

    # "Section 210 — Branch Circuits"
    # \bSection\b  the word Section (word-boundaries so "Sectional" won't match)
    # \s+\d+       space then a number
    re.compile(r'^Section\s+\d+\b'),

    # "Step 1.", "Step 2."
    # Step \d+   keyword then number
    # \.?        optional trailing dot
    re.compile(r'^Step\s+\d+\.?$'),

    # "DEFINITIONS", "LEAK TESTING", "TROUBLESHOOTING"
    # Whole line is uppercase letters/spaces, and short.
    # [A-Z]      uppercase only
    # [A-Z\s]*   more uppercase or spaces
    # $          to end of line  — nothing lowercase allowed
    re.compile(r'^[A-Z][A-Z\s]+$'),
]

SECTION_HEADERS = [
    re.compile(r'^\d+\.\d+\s+\S'),
    re.compile(r'^Section\s+\d+\b'),
    re.compile(r'^[A-Z][A-Z\s]{2,}$')
]

def find_sections(text: str) -> list[dict]:
    """
    Scan text line by line, find major-section headers and their character
    offsets. Return a list of {"label": str, "start": int, "end": int} spans
    covering the whole document.
    """

    offset = 0
    headers = []
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        for pattern in SECTION_HEADERS:
            if pattern.match(stripped):
                headers.append((offset, stripped))
                break

        offset += len(line)

    spans = []
    # Preamble: text before first header
    if not headers:
        return [{"label": "PREAMBLE", "start": 0, "end": len(text)}]
    if headers[0][0] > 0:
        spans.append({"label": "PREAMBLE", "start": 0, "end": headers[0][0]})

    # One span per header
    for i, (start, label) in enumerate(headers):
        end = headers[i+1][0] if i + 1 < len(headers) else len(text)
        spans.append({"label": label, "start": start, "end": end})

    return spans


def detect_section(text: str) -> str | None:
    """Return the section label for a chunk: the FIRST header line found, else None."""
    MIN = 6
    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        for pattern in HEADER_PATTERNS:
            if pattern.match(line):
                if line.isupper() and len(line.split()) > MIN:
                    continue
                return line

    return None


# ---------------------------------------------------------------------------
# Section detection (Option C: typography) — see scripts/section_detection_examples.py
# ---------------------------------------------------------------------------

# Page furniture like "2 Rec. ITU-R P.453-14" repeats atop every page and must
# never be promoted to a section heading.
RUNNING_HEADER = re.compile(r"Rec\.\s*ITU-R", re.IGNORECASE)

# "1 Title" / "2.1 Title" — number(s), whitespace, then a capitalized word.
NUMBERED_HEADING = re.compile(r"^(\d+(?:\.\d+)*)\s+[A-Z]")

# Exactly "Annex 1" — anchored with $ so a sentence starting with
# "Annex 1, ..." doesn't match (the false positive the regex approach showed).
ANNEX_HEADING = re.compile(r"^Annex\s+\d+$")


def _looks_like_heading_text(text: str) -> bool:
    """Content sanity checks: does this line READ like a section title?

    Typography (bold/size) says a line is styled like a heading; this guards
    against bold-but-irrelevant lines and equation debris ("6 7", "0 . 3 M e d").
    """
    text = text.strip()
    if RUNNING_HEADER.search(text):
        return False
    if not (NUMBERED_HEADING.match(text) or ANNEX_HEADING.match(text)):
        return False
    if not 8 <= len(text) <= 100:
        return False
    return sum(c.isalpha() for c in text) >= 8


def _headings_from_fonts(source_path: str) -> list[dict]:
    """Detect headings by how they are typeset (Option C).

    A heading line is (a) >=90% bold characters, (b) at body-or-larger font
    size (body size = the most common character size on the page), and
    (c) passes the text sanity checks. Returns [{"page_num", "title"}];
    offsets are resolved later against the parsed page text.
    """
    found = []
    with pdfplumber.open(source_path) as pdf:
        for page in pdf.pages:
            lines = page.extract_text_lines()
            if not lines:
                continue  # image-only page (OCR text has no font info)

            all_sizes = Counter(
                round(c["size"], 1) for ln in lines for c in ln["chars"]
            )
            body_size = all_sizes.most_common(1)[0][0]

            for ln in lines:
                chars = [c for c in ln["chars"] if not c["text"].isspace()]
                if not chars:
                    continue
                bold_ratio = sum(
                    "bold" in c["fontname"].lower() for c in chars
                ) / len(chars)
                line_size = max(round(c["size"], 1) for c in chars)
                text = " ".join(ln["text"].split())

                if (
                    bold_ratio >= 0.9
                    and line_size >= body_size
                    and _looks_like_heading_text(text)
                ):
                    found.append({"page_num": page.page_number, "title": text})
    return found


def _locate_headings(pages: list[dict], headings: list[dict]) -> list[dict]:
    """Resolve each detected heading to a character offset in its page's text.

    extract_text_lines() (font pass) and extract_text() (parse pass) are two
    different renderings, so headings are matched by whitespace-normalized
    line comparison. Headings that can't be located are dropped.
    """
    located = []
    for h in headings:
        page = next((p for p in pages if p["page_num"] == h["page_num"]), None)
        if page is None:
            continue
        for line in page["text"].splitlines():
            if " ".join(line.split()) == h["title"]:
                located.append({**h, "offset": page["text"].find(line)})
                break
    return located


def _headings_from_text(pages: list[dict]) -> list[dict]:
    """Fallback for .txt files and OCR'd pages: guarded line-scan of the text."""
    found = []
    for page in pages:
        offset = 0
        for line in page["text"].splitlines(keepends=True):
            stripped = line.strip()
            if stripped and _looks_like_heading_text(stripped):
                found.append(
                    {"page_num": page["page_num"], "title": stripped, "offset": offset}
                )
            offset += len(line)
    return found


def _assign_sections_with_carry(pages: list[dict], headings: list[dict]) -> list[dict]:
    """Build {"page_num", "label", "start", "end"} spans, carrying the current
    section across page boundaries: a page with no heading belongs to the last
    section seen, not PREAMBLE. Only text before the document's first heading
    is PREAMBLE."""
    by_page: dict[int, list[dict]] = {}
    for h in headings:
        by_page.setdefault(h["page_num"], []).append(h)

    spans = []
    current = "PREAMBLE"
    for page in pages:
        page_headings = sorted(
            by_page.get(page["page_num"], []), key=lambda h: h["offset"]
        )
        cursor = 0
        for h in page_headings:
            if h["offset"] > cursor:
                spans.append(
                    {
                        "page_num": page["page_num"],
                        "label": current,
                        "start": cursor,
                        "end": h["offset"],
                    }
                )
            current = h["title"]
            cursor = h["offset"]
        spans.append(
            {
                "page_num": page["page_num"],
                "label": current,
                "start": cursor,
                "end": len(page["text"]),
            }
        )
    return spans


def chunk_document(
    pages: list[dict],
    document_id: str,
    source_path: str,
) -> list[dict]:
    """
    Split parsed document pages into chunks suitable for embedding + retrieval.

    Section labels come from typography-based heading detection (Option C)
    when the source is a PDF, with a text-heuristic fallback otherwise.
    """
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 50

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )

    # Detect headings document-wide (not per page) so sections can carry over.
    path = Path(source_path)
    headings: list[dict] = []
    if path.suffix.lower() == ".pdf" and path.exists():
        try:
            headings = _locate_headings(pages, _headings_from_fonts(source_path))
        except Exception:
            headings = []  # fall through to the text scan
    if not headings:
        headings = _headings_from_text(pages)

    chunks = []
    for span in _assign_sections_with_carry(pages, headings):
        page = next(p for p in pages if p["page_num"] == span["page_num"])
        section_text = page["text"][span["start"]:span["end"]]

        for piece in splitter.split_text(section_text):
            chunks.append({
                "document_id": document_id,
                "content": piece,
                "source_path": source_path,
                "page": span["page_num"],
                "section": span["label"],
            })

    return chunks

# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------
REQUIRED_KEYS = {"document_id", "content", "source_path", "page", "section"}
 
 
def load_corpus(folder: str) -> dict:
    """
    Load each .txt file as a list of page dicts: [{"page_num": int, "text": str}].
 
    Plain .txt has no real pages, so by default each file is one page. If a file
    contains form-feed characters ("\\f"), we treat those as page breaks so you
    can exercise multi-page handling.
    """
    corpus = {}
    for path in sorted(glob.glob(os.path.join(folder, "*.txt"))):
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        parts = raw.split("\f")
        pages = [
            {"page_num": i + 1, "text": part}
            for i, part in enumerate(parts)
            if part.strip()
        ]
        if not pages:
            pages = [{"page_num": 1, "text": raw}]
        corpus[os.path.basename(path)] = pages
    return corpus
 
 
def validate_chunk(chunk) -> list:
    """Catch shape mistakes early — missing keys, wrong types."""
    problems = []
    if not isinstance(chunk, dict):
        return [f"chunk is {type(chunk).__name__}, expected dict"]
    missing = REQUIRED_KEYS - set(chunk.keys())
    if missing:
        problems.append(f"missing keys: {sorted(missing)}")
    extra = set(chunk.keys()) - REQUIRED_KEYS
    if extra:
        problems.append(f"unexpected keys: {sorted(extra)}")
    if "content" in chunk and not isinstance(chunk["content"], str):
        problems.append("content is not a str")
    if "page" in chunk and not (chunk["page"] is None or isinstance(chunk["page"], int)):
        problems.append("page is not int|None")
    if "section" in chunk and not (chunk["section"] is None or isinstance(chunk["section"], str)):
        problems.append("section is not str|None")
    return problems
 
 
def show_chunk(i: int, chunk) -> None:
    shape_problems = validate_chunk(chunk)
    if shape_problems:
        print(f"  -- chunk {i:>2} | X SHAPE: {' ; '.join(shape_problems)}")
        return
 
    content = chunk["content"]
    n = len(content)
    page = chunk["page"]
    section = chunk["section"]
    head = content[:90].replace("\n", "\\n")
    tail = content[-90:].replace("\n", "\\n")
    sect = f" | section={section!r}" if section else " | section=None"
    print(f"  -- chunk {i:>2} | {n:>4} chars | page={page}{sect}")
    print(f"     starts: {head!r}")
    print(f"     ends:   {tail!r}")
 
    # Heuristic smells — flags that hint a boundary cut through meaning.
    smells = []
    stripped = content.strip()
    if stripped and stripped[-1] not in ".:)0123456789":
        smells.append("ends mid-sentence?")
    if "Step" in content and content.count("Step") == 1 and "Step 1" not in content:
        smells.append("orphaned procedure step?")
    if content.count("  ") > 8 and ("Value" not in content and "Parameter" not in content):
        smells.append("possible table fragment (no header)?")
    if stripped.endswith(("the", "a", "of", "to", "and", "for", "is", "than")):
        smells.append("ends on a dangling word")
    if section is None:
        smells.append("section unlabeled (citation will be weak)")
    if smells:
        print(f"     !  {' | '.join(smells)}")


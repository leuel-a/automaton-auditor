import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

from langchain_core.tools import tool

# In-memory cache for RAG-lite PDF indexing
_PDF_CACHE: Dict[str, Dict[str, Any]] = {}
_WORD_RE = re.compile(r"[A-Za-z0-9_/\-\.]+")


def _extract_pdf_pages(pdf_path: str) -> List[str]:
    """Best-effort per-page text extraction."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Prefer pypdf; fall back to PyPDF2
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(pdf_path)
        return [(p.extract_text() or "") for p in reader.pages]
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore

            reader = PdfReader(pdf_path)
            return [(p.extract_text() or "") for p in reader.pages]
        except Exception as e:
            raise RuntimeError(
                "Failed to extract text from PDF. Install 'pypdf' (recommended) or ensure PDF text is extractable."
            ) from e


def _chunk_pages(
    pages: List[str], max_chars: int = 2200, overlap_chars: int = 250
) -> List[Dict[str, Any]]:
    """
    Chunk by page, then within page by character length.
    Preserves page numbers for citations.
    """
    chunks: List[Dict[str, Any]] = []
    chunk_id = 0

    for page_no, raw in enumerate(pages, start=1):
        text = re.sub(r"\s+", " ", (raw or "")).strip()
        if not text:
            continue

        start = 0
        while start < len(text):
            end = min(len(text), start + max_chars)
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    {
                        "chunk_id": f"c{chunk_id}",
                        "pages": [page_no],
                        "text": chunk_text,
                    }
                )
                chunk_id += 1

            if end >= len(text):
                break
            start = max(0, end - overlap_chars)

    return chunks


def _score(question: str, chunk_text: str) -> float:
    """
    Simple lexical overlap scoring + boosts for quoted phrases.
    This is intentionally lightweight ("RAG-lite"), not embedding-based.
    """
    q = (question or "").lower()
    c = (chunk_text or "").lower()

    q_terms = set(_WORD_RE.findall(q))
    if not q_terms:
        return 0.0

    c_terms = set(_WORD_RE.findall(c))
    overlap = len(q_terms & c_terms)
    base = overlap / max(1, len(q_terms))

    # Boost quoted phrases: "Dialectical Synthesis"
    boost = 0.0
    for phrase in re.findall(r"\"([^\"]+)\"", question):
        if phrase.lower() in c:
            boost += 0.35

    return base + boost


@tool
def pdf_parse_ingest_pdf(path: str) -> str:
    """
    Ingest a PDF and build a chunk index (RAG-lite).
    Returns JSON: {doc_id, num_chunks, pages}
    """
    pages = _extract_pdf_pages(path)
    chunks = _chunk_pages(pages)

    doc_id = f"pdf_{uuid.uuid4().hex[:10]}"
    _PDF_CACHE[doc_id] = {
        "path": path,
        "pages": len(pages),
        "chunks": chunks,
    }

    return (
        "{"
        f'"doc_id": "{doc_id}", '
        f'"num_chunks": {len(chunks)}, '
        f'"pages": {len(pages)}'
        "}"
    )


@tool
def pdf_parse_query_pdf(doc_id: str, question: str, top_k: int = 6) -> str:
    """
    Query an ingested PDF index for relevant chunks.
    Returns JSON: {matches:[{chunk_id,pages,score,text}]}
    """
    if doc_id not in _PDF_CACHE:
        raise ValueError(f"Unknown doc_id: {doc_id}. Call pdf_parse_ingest_pdf first.")

    chunks = _PDF_CACHE[doc_id]["chunks"]
    scored: List[Tuple[float, Dict[str, Any]]] = []
    for ch in chunks:
        s = _score(question, ch["text"])
        if s > 0:
            scored.append((s, ch))

    scored.sort(key=lambda x: x[0], reverse=True)

    matches: List[Dict[str, Any]] = []
    for s, ch in scored[: max(1, top_k)]:
        matches.append(
            {
                "chunk_id": ch["chunk_id"],
                "pages": ch["pages"],
                "score": round(float(s), 4),
                "text": ch["text"],
            }
        )

    # JSON without importing json (keeps symmetry with your tool style)
    # If you prefer json.dumps, swap it in.
    import json

    return json.dumps({"matches": matches}, ensure_ascii=False)


@tool
def markdown_read(path: str) -> str:
    """
    Read a UTF-8 markdown file from local disk.
    Returns raw text.
    """
    p = Path(path).resolve()
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"Markdown not found: {path}")
    return p.read_text(encoding="utf-8", errors="replace")


@tool
def cross_reference(repo_path: str, paths: List[str]) -> str:
    """
    Cross-reference report-cited file paths against the cloned repository.
    Returns JSON: {verified:[...], missing:[...], details:{path:true/false}}
    """
    root = Path(repo_path).resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError("repo_path missing or does not exist on disk.")

    verified: List[str] = []
    missing: List[str] = []
    details: Dict[str, bool] = {}

    for p in paths:
        rel = (p or "").strip().lstrip("./")
        if not rel:
            continue

        full = (root / rel).resolve()

        # Prevent traversal outside repo root
        if root not in full.parents and full != root:
            details[p] = False
            missing.append(p)
            continue

        ok = full.exists()
        details[p] = ok
        (verified if ok else missing).append(p)

    import json

    return json.dumps(
        {"verified": verified, "missing": missing, "details": details},
        ensure_ascii=False,
    )

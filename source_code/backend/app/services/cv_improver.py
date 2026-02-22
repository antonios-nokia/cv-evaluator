"""
DOCX in-place CV improver.

Instead of rewriting the entire CV as text, this module:
  1. Asks the LLM for targeted bullet-point insertions (JSON array).
  2. Locates each anchor keyword in the DOCX XML.
  3. Inserts new <w:p> elements after the matching paragraph.
  4. Returns the modified DOCX as bytes, plus plain text for re-evaluation.
"""

import copy
import io
import json
import logging
from typing import Optional

from docx import Document
from docx.oxml.ns import qn
from lxml import etree

from app.services import ollama_client
from app.services.cv_parser import extract_text_from_docx
from app.services.evaluator import (
    _repair_json,
    _sanitize_control_chars,
    _strip_markdown_fences,
)

logger = logging.getLogger(__name__)

IMPROVE_SYSTEM = (
    "You are an expert CV editor. You improve CVs by inserting targeted bullet points "
    "at the right location — never removing or rewriting existing content. "
    "You always respond with valid JSON only — no markdown, no extra commentary."
)

IMPROVE_PROMPT_TEMPLATE = """You are editing a CV to better match a job description.

Your task: identify 3-6 places in the CV where NEW bullet points should be inserted.
For each insertion output:
- "after_keyword": a short verbatim phrase (5-20 words) that appears in the CV text, indicating where to insert AFTER.
- "new_bullets": list of 1-3 new bullet strings to add there (do NOT start with "•" — that is added automatically).

Only use information the candidate has explicitly confirmed in the chat. Do not invent anything.

CV text:
{cv_text}

---

Job Description:
{job_description}

---

Candidate's additional confirmed context from chat:
{chat_context}

---

Return ONLY a valid JSON array, no markdown, no commentary:
[
  {{"after_keyword": "exact phrase from CV", "new_bullets": ["bullet 1", "bullet 2"]}},
  ...
]"""


# ---------------------------------------------------------------------------
# JSON parsing helpers
# ---------------------------------------------------------------------------

def _try_parse_list(s: str) -> Optional[list]:
    """Try json.loads then raw_decode; return list or None."""
    s = s.strip()
    if not s:
        return None
    try:
        obj = json.loads(s)
        if isinstance(obj, list):
            return obj
    except json.JSONDecodeError:
        pass
    try:
        obj, _ = json.JSONDecoder().raw_decode(s)
        if isinstance(obj, list):
            return obj
    except json.JSONDecodeError:
        pass
    return None


def _parse_additions_json(raw: str) -> list:
    """Multi-strategy parser for the LLM additions array."""
    candidates = [
        raw,
        _strip_markdown_fences(raw),
        _sanitize_control_chars(raw),
        _sanitize_control_chars(_strip_markdown_fences(raw)),
    ]
    for candidate in candidates:
        result = _try_parse_list(candidate)
        if result is not None:
            return result

    for candidate in [raw, _strip_markdown_fences(raw)]:
        repaired = _repair_json(candidate.strip())
        result = _try_parse_list(repaired) or _try_parse_list(
            _sanitize_control_chars(repaired)
        )
        if result is not None:
            logger.warning("Parsed additions JSON after repair (LLM response was likely truncated).")
            return result

    logger.error("All additions-JSON parse strategies failed. Raw starts: %s", raw[:300])
    return []


# ---------------------------------------------------------------------------
# OOXML helpers
# ---------------------------------------------------------------------------

def _find_paragraph_containing(body_elem, keyword: str):
    """
    Walk all <w:p> elements in document order (body paragraphs + table cells).
    Return (para_elem, parent_elem) for the first match, or (None, None).
    """
    keyword_lower = keyword.lower()
    for para in body_elem.iter(qn("w:p")):
        text = "".join(t.text or "" for t in para.iter(qn("w:t")))
        if keyword_lower in text.lower():
            return para, para.getparent()
    return None, None


def _build_bullet_paragraph(text: str, ref_para) -> etree._Element:
    """
    Create a new <w:p> with the bullet text, copying paragraph/run formatting
    from ref_para but stripping <w:numPr> to avoid inheriting list numbering.
    """
    new_para = etree.Element(qn("w:p"))

    # Copy pPr from reference paragraph
    ref_pPr = ref_para.find(qn("w:pPr"))
    if ref_pPr is not None:
        pPr = copy.deepcopy(ref_pPr)
        # Remove numPr so we don't inherit automatic list numbering
        numPr = pPr.find(qn("w:numPr"))
        if numPr is not None:
            pPr.remove(numPr)
        new_para.append(pPr)

    # Find rPr from the first run in the reference paragraph
    ref_rPr = None
    for r in ref_para.iter(qn("w:r")):
        rPr = r.find(qn("w:rPr"))
        if rPr is not None:
            ref_rPr = copy.deepcopy(rPr)
        break  # only need the first run's formatting

    # Build the run
    r_elem = etree.SubElement(new_para, qn("w:r"))
    if ref_rPr is not None:
        r_elem.append(ref_rPr)
    t_elem = etree.SubElement(r_elem, qn("w:t"))
    t_elem.text = f"\u2022 {text}"  # literal bullet
    t_elem.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    return new_para


def _insert_paragraphs_after(target, parent, new_paras: list):
    """
    Insert new_paras after target inside parent.

    OOXML table-cell invariant: the last <w:p> in a <w:tc> must stay last.
    If target IS the last <w:p> in a cell we insert the new paragraphs BEFORE it.
    """
    is_cell = etree.QName(parent.tag).localname == "tc"
    if is_cell:
        cell_paras = parent.findall(qn("w:p"))
        if cell_paras and cell_paras[-1] is target:
            # Insert before the required terminal paragraph
            idx = list(parent).index(target)
            for i, new_p in enumerate(new_paras):
                parent.insert(idx + i, new_p)
            return

    # Normal case: insert after target
    idx = list(parent).index(target)
    for i, new_p in enumerate(new_paras):
        parent.insert(idx + 1 + i, new_p)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def improve_docx(
    cv_bytes: bytes,
    cv_text: str,
    job_description: str,
    chat_history: list,
) -> tuple[bytes, str]:
    """
    Ask the LLM for bullet-point additions, apply them in-place to the DOCX,
    and return (improved_bytes, improved_text).

    Always works from the original cv_bytes — not from previously improved bytes —
    so multiple clicks do not compound edits.
    """
    user_messages = [
        msg["content"] for msg in chat_history if msg.get("role") == "user"
    ]
    chat_context = (
        "\n".join(f"- {m}" for m in user_messages) if user_messages else "None provided."
    )

    prompt = IMPROVE_PROMPT_TEMPLATE.format(
        cv_text=cv_text[:8000],
        job_description=job_description[:4000],
        chat_context=chat_context[:3000],
    )

    raw = await ollama_client.complete(prompt, system=IMPROVE_SYSTEM)
    additions = _parse_additions_json(raw)

    if not additions:
        logger.warning("No additions produced by LLM; returning original DOCX bytes.")
        return cv_bytes, cv_text

    doc = Document(io.BytesIO(cv_bytes))
    body = doc.element.body

    applied = 0
    for addition in additions:
        keyword = (addition.get("after_keyword") or "").strip()
        bullets = addition.get("new_bullets") or []
        if not keyword or not bullets:
            continue

        target, parent = _find_paragraph_containing(body, keyword)
        if target is None:
            logger.warning("Keyword not found in DOCX: %r — skipping", keyword)
            continue

        new_paras = [_build_bullet_paragraph(b, target) for b in bullets if b]
        if new_paras:
            _insert_paragraphs_after(target, parent, new_paras)
            applied += 1

    logger.info("Applied %d/%d additions to DOCX.", applied, len(additions))

    out = io.BytesIO()
    doc.save(out)
    improved_bytes = out.getvalue()
    improved_text = extract_text_from_docx(improved_bytes)

    return improved_bytes, improved_text

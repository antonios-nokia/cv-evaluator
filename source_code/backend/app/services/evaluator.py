import json
import logging
import re

from app.services import ollama_client

logger = logging.getLogger(__name__)

EVAL_SYSTEM = (
    "You are an expert recruitment specialist and CV evaluator. "
    "You always respond with valid JSON only — no markdown, no extra commentary."
)

EVAL_PROMPT_TEMPLATE = """Evaluate the candidate CV against the job description below.

<cv>
{cv_text}
</cv>

<job_description>
{job_description}
</job_description>

TASK — two steps:

Step 1: Read ONLY <job_description>. Write down every skill, technology, tool, and certification it requires or prefers. Call this list REQUIRED (aim for 8-15 items, each 1-4 words).

Step 2: For each item in REQUIRED, check whether it is explicitly named in <cv>.
  - If yes → put it in "strengths"
  - If no  → put it in "gaps"

IMPORTANT RULES:
- strengths and gaps must contain only items from REQUIRED (Step 1). Never put CV-only skills in either list.
- A skill goes in strengths only if that exact term (or a clear synonym) appears in the <cv> text.
- Do not infer. "OpenShift" does not prove "GCP". "Network automation" does not prove "Python".
- Return concise skill names (1-4 words), not full sentences.

Return ONLY this JSON object — no other text:
{{
  "strengths": [<items from REQUIRED that appear in cv>],
  "gaps": [<items from REQUIRED that do NOT appear in cv>],
  "summary": "<2-3 sentence overall assessment, single line, no newlines>"
}}

- strengths = [] when the CV contains none of the job requirements.
- strengths + gaps must together contain all REQUIRED items."""


def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers if present."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _sanitize_control_chars(s: str) -> str:
    """Escape literal control characters (newlines, tabs, etc.) inside JSON string values."""
    result = []
    in_string = False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and in_string:
            # Already-escaped sequence — pass both chars through unchanged
            result.append(ch)
            i += 1
            if i < len(s):
                result.append(s[i])
            i += 1
            continue
        if ch == '"':
            in_string = not in_string
            result.append(ch)
            i += 1
            continue
        if in_string:
            if ch == "\n":
                result.append("\\n")
            elif ch == "\r":
                result.append("\\r")
            elif ch == "\t":
                result.append("\\t")
            else:
                result.append(ch)
            i += 1
            continue
        result.append(ch)
        i += 1
    return "".join(result)


def _repair_json(raw: str) -> str:
    """Close any unclosed strings, arrays, and objects at the end of a truncated JSON response."""
    stack = []
    in_string = False
    escape_next = False

    for ch in raw:
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            stack.append("}")
        elif ch == "[":
            stack.append("]")
        elif ch in ("}", "]"):
            if stack and stack[-1] == ch:
                stack.pop()

    suffix = ""
    if in_string:
        suffix += '"'       # close the open string first
    suffix += "".join(reversed(stack))   # close open arrays / objects
    return raw + suffix


def _try_parse(s: str) -> dict | None:
    """Try json.loads, then raw_decode (which ignores trailing text)."""
    s = s.strip()
    if not s:
        return None
    # Direct parse
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # raw_decode handles valid JSON followed by trailing text
    try:
        obj, _ = json.JSONDecoder().raw_decode(s)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    return None


def _parse_eval_json(raw: str) -> dict:
    """Try multiple strategies to extract a valid JSON object from the model output."""
    candidates = [
        raw,
        _strip_markdown_fences(raw),
        _sanitize_control_chars(raw),
        _sanitize_control_chars(_strip_markdown_fences(raw)),
    ]

    for candidate in candidates:
        result = _try_parse(candidate)
        if result is not None:
            return result

    # Attempt to repair truncated JSON (e.g. model stopped before the final `}`)
    for candidate in [raw, _strip_markdown_fences(raw)]:
        repaired = _repair_json(candidate.strip())
        result = _try_parse(repaired) or _try_parse(_sanitize_control_chars(repaired))
        if result is not None:
            logger.warning("Parsed JSON after repair (model response was likely truncated).")
            return result

    logger.error("All JSON parse strategies failed. Full raw response:\n%s", raw)
    raise ValueError(
        f"The model did not return parseable JSON. Raw response starts with: {raw[:300]}"
    )


async def evaluate_cv(cv_text: str, job_description: str) -> dict:
    prompt = EVAL_PROMPT_TEMPLATE.format(
        cv_text=cv_text[:8000],
        job_description=job_description[:4000],
    )
    raw = await ollama_client.complete(prompt, system=EVAL_SYSTEM)
    result = _parse_eval_json(raw)

    # Normalize to expected output shape
    raw_strengths = list(result.get("strengths", []))
    gaps = list(result.get("gaps", []))

    # Verify each claimed strength actually appears in the CV text.
    # This catches hallucinations where the model claims a skill is present but it isn't.
    cv_lower = cv_text.lower()
    verified_strengths = []
    for skill in raw_strengths:
        # Extract meaningful tokens (3+ chars, skip common words)
        tokens = [t.lower() for t in re.split(r"[\s/,\-]+", skill) if len(t) >= 3]
        # A strength is valid if at least one of its key tokens appears literally in the CV
        if any(token in cv_lower for token in tokens):
            verified_strengths.append(skill)
        else:
            logger.info("Demoting hallucinated strength '%s' to gaps (not found in CV text).", skill)
            gaps.append(skill)

    strengths = verified_strengths

    # Compute score in Python — never trust the model's arithmetic.
    total = len(strengths) + len(gaps)
    found_count = len(strengths)
    if total > 0:
        score = round(found_count / total * 100)
    else:
        score = 0

    return {
        "score": max(0, min(100, score)),
        "strengths": strengths,
        "gaps": gaps,
        "summary": str(result.get("summary", "")),
    }

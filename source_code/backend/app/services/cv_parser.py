import io
from pypdf import PdfReader
from docx import Document
from docx.oxml.ns import qn


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def _iter_block_items(doc):
    """
    Yield paragraphs and table cells in document order.
    Handles top-level paragraphs, table cells (including nested tables),
    and text boxes embedded in drawing elements.
    """
    seen = set()

    # Top-level paragraphs and tables in body order
    body = doc.element.body
    for child in body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

        if tag == "p":
            text = "".join(r.text or "" for r in child.iter(qn("w:t")))
            if text.strip() and text not in seen:
                seen.add(text)
                yield text

        elif tag == "tbl":
            # Walk every cell in the table (handles nested tables too)
            for cell in child.iter(qn("w:tc")):
                cell_text = "".join(r.text or "" for r in cell.iter(qn("w:t")))
                if cell_text.strip() and cell_text not in seen:
                    seen.add(cell_text)
                    yield cell_text

    # Text boxes (w:txbxContent) anywhere in the document
    for txbx in body.iter(qn("w:txbxContent")):
        text = "".join(r.text or "" for r in txbx.iter(qn("w:t")))
        if text.strip() and text not in seen:
            seen.add(text)
            yield text


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    blocks = list(_iter_block_items(doc))
    return "\n".join(blocks).strip()


def extract_cv_text(filename: str, file_bytes: bytes) -> str:
    name_lower = filename.lower()
    if name_lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif name_lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}")

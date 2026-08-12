import re
from functools import lru_cache

import pypdfium2 as pdfium
from rapidocr_onnxruntime import RapidOCR

from intellipay.parsing.text_parser import parse_text_invoice
from intellipay.reasoning.models import InvoiceCandidate


def parse_pdf_invoice(content: bytes) -> InvoiceCandidate:
    document = pdfium.PdfDocument(content)
    lines: list[str] = []
    try:
        for page in document:
            image = page.render(scale=3).to_pil()
            result, _ = _ocr_engine()(image)
            lines.extend(_group_rows(result or []))
    finally:
        document.close()

    text = "\n".join(lines).replace("\uff08", "(").replace("\uff09", ")")
    text = re.sub(r"\s+(?=(?:Date|Vendor|Due|Terms):)", "\n", text)
    return parse_text_invoice(text.encode())


@lru_cache(maxsize=1)
def _ocr_engine() -> RapidOCR:
    return RapidOCR()


def _group_rows(result: list) -> list[str]:
    fragments = sorted(
        (
            sum(point[1] for point in entry[0]) / len(entry[0]),
            min(point[0] for point in entry[0]),
            entry[1],
        )
        for entry in result
    )
    rows: list[tuple[float, list[tuple[float, str]]]] = []
    for vertical_center, left, text in fragments:
        if not rows or abs(vertical_center - rows[-1][0]) > 12:
            rows.append((vertical_center, [(left, text)]))
        else:
            rows[-1][1].append((left, text))
    return [" ".join(text for _, text in sorted(cells)) for _, cells in rows]

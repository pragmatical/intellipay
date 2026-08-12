from collections.abc import Callable
from pathlib import Path

from intellipay.parsing.csv_parser import parse_csv_invoice
from intellipay.parsing.json_parser import parse_json_invoice
from intellipay.parsing.pdf_parser import parse_pdf_invoice
from intellipay.parsing.text_parser import parse_text_invoice
from intellipay.parsing.xml_parser import parse_xml_invoice
from intellipay.reasoning.models import InvoiceCandidate

Parser = Callable[[bytes], InvoiceCandidate]


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[str, Parser] = {
            ".csv": parse_csv_invoice,
            ".json": parse_json_invoice,
            ".pdf": parse_pdf_invoice,
            ".txt": parse_text_invoice,
            ".xml": parse_xml_invoice,
        }

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self._parsers

    def parse(self, path: Path, content: bytes) -> InvoiceCandidate:
        try:
            parser = self._parsers[path.suffix.lower()]
        except KeyError as error:
            raise ValueError(f"No deterministic parser for {path.suffix.lower()}") from error
        return parser(content)

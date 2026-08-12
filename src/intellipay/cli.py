import argparse
from pathlib import Path

from intellipay.config import ReasoningMode, Settings
from intellipay.workflow import InvoiceWorkflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process an invoice through IntelliPay")
    parser.add_argument("invoice_path", type=Path)
    parser.add_argument("--reasoning-mode", choices=ReasoningMode, default=None)
    parser.add_argument("--database-path", type=Path, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    overrides = {}
    if args.reasoning_mode:
        overrides["reasoning_mode"] = args.reasoning_mode
    if args.database_path:
        overrides["database_path"] = args.database_path
    settings = Settings(**overrides)
    result = InvoiceWorkflow(settings).process(args.invoice_path)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

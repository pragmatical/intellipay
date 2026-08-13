import argparse
import os
import socket
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import uvicorn

from intellipay.config import Settings
from intellipay.event_export import export_events_markdown
from intellipay.model_pricing import ReasoningCostReport, build_reasoning_cost_report
from intellipay.review_app import create_app
from intellipay.workflow import InvoiceWorkflow
from intellipay.workflow.models import ReviewTask, WorkflowResult
from intellipay.workflow.storage import SQLiteStore

DEFAULT_DATABASE = Path(".intellipay/demo.db")
DEFAULT_INVOICE_ROOT = Path("data/invoices")
DEFAULT_OBSERVABILITY_REPORT = Path(".intellipay/observability-report.md")


@dataclass(frozen=True)
class DemoScenario:
    title: str
    business_impact: str
    result: WorkflowResult


@dataclass(frozen=True)
class DemoSummary:
    database_path: Path
    scenarios: tuple[DemoScenario, ...]
    open_reviews: tuple[ReviewTask, ...]
    payment_count: int
    reasoning_cost: ReasoningCostReport


def reset_demo_state(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("", "-shm", "-wal"):
        Path(f"{database_path}{suffix}").unlink(missing_ok=True)


def ensure_demo_port_available(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        try:
            listener.bind((host, port))
        except OSError as error:
            raise RuntimeError(
                f"Port {host}:{port} is already in use. Stop the existing demo before rerunning."
            ) from error


@contextmanager
def demo_state_lock(database_path: Path) -> Iterator[None]:
    lock_path = Path(f"{database_path}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError as error:
            try:
                owner_pid = int(lock_path.read_text())
                os.kill(owner_pid, 0)
            except (ProcessLookupError, ValueError):
                lock_path.unlink(missing_ok=True)
                continue
            except PermissionError:
                pass
            raise RuntimeError(
                f"Demo state is already in use by process {owner_pid}. "
                "Stop the existing demo before rerunning."
            ) from error
    else:
        raise RuntimeError("Could not acquire the demo state lock")

    try:
        os.write(descriptor, str(os.getpid()).encode())
        yield
    finally:
        os.close(descriptor)
        lock_path.unlink(missing_ok=True)


def prepare_demo_inputs(database_path: Path, invoice_root: Path) -> dict[str, Path]:
    output = database_path.parent / "demo-inputs"
    output.mkdir(parents=True, exist_ok=True)
    source = (invoice_root / "invoice_1001.txt").read_text()

    repair = output / "invoice_demo_repair.txt"
    repair.write_text(source.replace("INV-1001", "INV-9002").replace("$5,000.00", "$5,OOO.OO", 1))

    review = output / "invoice_demo_review.txt"
    review.write_text(
        source.replace("INV-1001", "INV-9001")
        .replace("$250.00", "$1,000.00")
        .replace("$5,000.00", "$12,500.00")
    )
    return {"repair": repair, "review": review}


def run_demo(settings: Settings, invoice_root: Path = DEFAULT_INVOICE_ROOT) -> DemoSummary:
    inputs = prepare_demo_inputs(settings.database_path, invoice_root)
    workflow = InvoiceWorkflow(settings)
    scenarios: list[DemoScenario] = []
    scenario_count = 8

    print(f"Running IntelliPay demo with reasoning mode: {settings.reasoning_mode}", flush=True)

    def process(title: str, business_impact: str, path: Path) -> WorkflowResult:
        scenario_number = len(scenarios) + 1
        print(f"[{scenario_number}/{scenario_count}] Running {title}...", flush=True)
        result = workflow.process(path)
        scenarios.append(DemoScenario(title, business_impact, result))
        print(
            f"[{scenario_number}/{scenario_count}] Completed {title}: {result.outcome}",
            flush=True,
        )
        return result

    process(
        "Routine automation",
        "A valid invoice reaches one authorized mock payment.",
        invoice_root / "invoice_1001.txt",
    )
    process(
        "Replay protection",
        "A duplicate submission reuses the payment instead of moving money twice.",
        invoice_root / "invoice_1001.txt",
    )
    process(
        "Bounded agentic correction",
        "A typed critic repairs one ambiguous amount without bypassing controls.",
        inputs["repair"],
    )
    process(
        "Approvable human review",
        "A valid high-value invoice pauses for delegated human approval.",
        inputs["review"],
    )
    process(
        "Policy-blocked human review",
        "Insufficient stock keeps approval unavailable even during review.",
        invoice_root / "invoice_1002.txt",
    )
    process(
        "Hard rejection",
        "Invalid financial data is rejected before payment.",
        invoice_root / "invoice_1009.json",
    )
    process(
        "Original invoice payment",
        "The first accepted business version creates one payment.",
        invoice_root / "invoice_1004.json",
    )
    process(
        "Revision safety",
        "A conflicting revision escalates and cannot create another payment.",
        invoice_root / "invoice_1004_revised.json",
    )

    store = SQLiteStore(settings.database_path)
    return DemoSummary(
        database_path=settings.database_path,
        scenarios=tuple(scenarios),
        open_reviews=tuple(store.list_review_tasks("OPEN")),
        payment_count=store.payment_count(),
        reasoning_cost=build_reasoning_cost_report([scenario.result for scenario in scenarios]),
    )


def print_presentation(summary: DemoSummary) -> None:
    print("\nINTELLIPAY EXECUTABLE PRESENTATION")
    print("$2M annual loss | 30% error rate | 5-day manual cycle")
    print("=" * 72)
    for index, scenario in enumerate(summary.scenarios, start=1):
        result = scenario.result
        findings = ", ".join(finding.code for finding in result.findings) or "none"
        print(f"\n{index}. {scenario.title}")
        print(f"   {scenario.business_impact}")
        print(
            f"   {result.invoice.invoice_number}: outcome={result.outcome} "
            f"payment={result.payment_status} replayed={result.payment_replayed}"
        )
        print(
            f"   findings={findings} repairs={result.repair_attempts} "
            f"reasoning_calls={len(result.reasoning_trace)}"
        )

    print("\nCONTROL SUMMARY")
    print(f"   Persisted payments: {summary.payment_count}")
    print(f"   Open review tasks: {len(summary.open_reviews)}")
    for task in summary.open_reviews:
        actions = ", ".join(action.value for action in task.allowed_actions)
        print(f"   - {task.invoice_number}: {', '.join(task.reason_codes)} | actions: {actions}")

    cost = summary.reasoning_cost
    usage_basis = (
        "estimated local usage"
        if cost.estimated_usage_calls and not cost.exact_usage_calls
        else "provider-reported usage"
        if cost.exact_usage_calls and not cost.estimated_usage_calls
        else "mixed exact and estimated usage"
    )
    print("\nREASONING COST REPORT")
    print(f"   Calls: {cost.calls} ({usage_basis})")
    print(
        f"   Tokens: input={cost.input_tokens} cached_input={cost.cached_input_tokens} "
        f"output={cost.output_tokens}"
    )
    print(f"   Estimated API cost: ${cost.estimated_cost_usd:.6f} {cost.currency}")
    print(f"   Pricing: effective {cost.pricing_effective_date} | {cost.pricing_source_url}")
    if cost.unpriced_calls:
        print(f"   Unpriced metered calls: {cost.unpriced_calls}")


def write_observability_report(summary: DemoSummary) -> tuple[Path, int]:
    store = SQLiteStore(summary.database_path)
    events = store.events_after(0)
    report_path = summary.database_path.parent / DEFAULT_OBSERVABILITY_REPORT.name
    report_path.write_text(export_events_markdown(store, reasoning_cost=summary.reasoning_cost))
    return report_path, len(events)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the IntelliPay executable presentation and reviewer UI"
    )
    parser.add_argument("--invoice-root", type=Path, default=DEFAULT_INVOICE_ROOT)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--reviewer-username", default="reviewer")
    parser.add_argument("--reviewer-password", default="intellipay-demo")
    parser.add_argument("--no-server", action="store_true")
    return parser


def build_settings(args: argparse.Namespace) -> Settings:
    return Settings(
        database_path=DEFAULT_DATABASE,
        reviewer_username=args.reviewer_username,
        reviewer_password=args.reviewer_password,
    )


def main() -> None:
    args = build_parser().parse_args()
    try:
        ensure_demo_port_available(args.host, args.port)
        with demo_state_lock(DEFAULT_DATABASE):
            reset_demo_state(DEFAULT_DATABASE)
            settings = build_settings(args)
            summary = run_demo(settings, args.invoice_root)
            print_presentation(summary)
            report_path, event_count = write_observability_report(summary)
            print("\nOBSERVABILITY REPORT")
            print(f"   Captured events: {event_count}")
            print(f"   Markdown: {report_path}")
            if args.no_server:
                return

            print("\nREVIEWER UI")
            print(f"   URL: http://{args.host}:{args.port}/reviews")
            print(f"   Username: {args.reviewer_username}")
            print(f"   Password: {args.reviewer_password}")
            print("   Open INV-9001 to demonstrate approval.")
            print("   Open INV-1002 to demonstrate a policy-disabled approval.\n")
            uvicorn.run(create_app(settings), host=args.host, port=args.port)
    except RuntimeError as error:
        raise SystemExit(f"Demo could not start: {error}") from error


if __name__ == "__main__":
    main()

import socket
from pathlib import Path

import pytest

from intellipay.config import ReasoningMode, Settings
from intellipay.demo import (
    build_parser,
    build_settings,
    demo_state_lock,
    ensure_demo_port_available,
    reset_demo_state,
    run_demo,
    write_observability_report,
)
from intellipay.workflow.models import Outcome, PaymentStatus, ReviewAction


def test_demo_seeds_pipeline_and_approval_ui_state(tmp_path: Path, capsys) -> None:
    database = tmp_path / "demo.db"
    reset_demo_state(database)

    summary = run_demo(Settings(database_path=database, _env_file=None))
    output = capsys.readouterr().out
    results = {scenario.title: scenario.result for scenario in summary.scenarios}
    reviews = {task.invoice_number: task for task in summary.open_reviews}

    routine = results["Routine automation"]
    replay = results["Replay protection"]
    assert routine.outcome is Outcome.APPROVE
    assert routine.payment_status is PaymentStatus.SUCCESS
    assert replay.payment_id == routine.payment_id
    assert replay.payment_replayed is True

    repair = results["Bounded agentic correction"]
    assert repair.outcome is Outcome.APPROVE
    assert repair.repair_attempts == 1

    assert ReviewAction.APPROVE in reviews["INV-9001"].allowed_actions
    assert ReviewAction.APPROVE not in reviews["INV-1002"].allowed_actions
    assert results["Hard rejection"].outcome is Outcome.REJECT
    assert results["Revision safety"].outcome is Outcome.ESCALATE
    assert "INVOICE_VERSION_CONFLICT" in {
        finding.code for finding in results["Revision safety"].findings
    }
    assert summary.payment_count == 3
    assert summary.reasoning_cost.calls == 5
    assert summary.reasoning_cost.estimated_usage_calls == 5
    assert summary.reasoning_cost.exact_usage_calls == 0
    assert summary.reasoning_cost.estimated_cost_usd > 0
    assert "Running IntelliPay demo with reasoning mode: local" in output
    assert "[1/8] Running Routine automation..." in output
    assert "[8/8] Completed Revision safety: ESCALATE" in output

    report_path, event_count = write_observability_report(summary)
    report = report_path.read_text()
    assert event_count > 0
    assert "# IntelliPay Observability Report" in report
    assert f"- Total events: {event_count}" in report
    assert "## Reasoning Usage and Estimated Cost" in report
    assert "- Usage basis: Estimated local usage" in report
    assert f"- Reasoning calls: {summary.reasoning_cost.calls}" in report
    assert f"- Estimated API cost: ${summary.reasoning_cost.estimated_cost_usd:.6f} USD" in report
    assert f"| `{summary.reasoning_cost.by_operation[0].operation}` |" in report
    assert "## Captured Events" in report
    assert "[REDACTED]" in report
    assert routine.payment_id not in report


def test_demo_cli_always_uses_a_fresh_fixed_database(tmp_path: Path, monkeypatch) -> None:
    parser = build_parser()
    option_strings = {option for action in parser._actions for option in action.option_strings}

    assert "--database-path" not in option_strings
    assert "--no-reset" not in option_strings
    assert "--reasoning-mode" not in option_strings

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("INTELLIPAY_REASONING_MODE", raising=False)
    (tmp_path / ".env").write_text("INTELLIPAY_REASONING_MODE=live\n")
    assert build_settings(parser.parse_args([])).reasoning_mode is ReasoningMode.LIVE


def test_demo_refuses_to_replace_state_while_port_or_database_is_in_use(
    tmp_path: Path,
) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        with pytest.raises(RuntimeError, match="already in use"):
            ensure_demo_port_available("127.0.0.1", port)

    database = tmp_path / "demo.db"
    with (
        demo_state_lock(database),
        pytest.raises(RuntimeError, match="Demo state is already in use"),
        demo_state_lock(database),
    ):
        pass

    assert not Path(f"{database}.lock").exists()

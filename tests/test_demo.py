from pathlib import Path

from intellipay.config import Settings
from intellipay.demo import reset_demo_state, run_demo
from intellipay.workflow.models import Outcome, PaymentStatus, ReviewAction


def test_demo_seeds_pipeline_and_approval_ui_state(tmp_path: Path) -> None:
    database = tmp_path / "demo.db"
    reset_demo_state(database)

    summary = run_demo(Settings(database_path=database, _env_file=None))
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

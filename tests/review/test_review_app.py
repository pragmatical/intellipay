import re
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import SecretStr

from intellipay.config import Settings
from intellipay.review_app import create_app
from intellipay.workflow import InvoiceWorkflow
from intellipay.workflow.storage import SQLiteStore


def test_review_interface_requires_auth_and_completes_once(tmp_path: Path) -> None:
    database = tmp_path / "intellipay.db"
    settings = Settings(
        database_path=database,
        reviewer_username="morgan",
        reviewer_password=SecretStr("test-password"),
        _env_file=None,
    )
    result = InvoiceWorkflow(settings).process(Path("data/invoices/invoice_1002.txt"))
    task = SQLiteStore(database).list_review_tasks()[0]
    client = TestClient(create_app(settings))

    assert client.get("/reviews").status_code == 401
    queue = client.get("/reviews", auth=("morgan", "test-password"))
    detail = client.get(f"/reviews/{task.review_task_id}", auth=("morgan", "test-password"))

    assert queue.status_code == 200
    assert "INV-1002" in queue.text
    assert detail.status_code == 200
    assert "Which source evidence" not in detail.text
    assert "INSUFFICIENT STOCK" in detail.text
    assert "PAYMENT FACTS" in detail.text.upper()
    csrf = re.search(r'name="csrf" value="([a-f0-9]+)"', detail.text).group(1)
    decision = {
        "csrf": csrf,
        "action": "REJECT",
        "rationale": "Inventory evidence does not support payment.",
    }

    first = client.post(
        f"/reviews/{task.review_task_id}/decision",
        data=decision,
        auth=("morgan", "test-password"),
        follow_redirects=False,
    )
    replay = client.post(
        f"/reviews/{task.review_task_id}/decision",
        data=decision,
        auth=("morgan", "test-password"),
        follow_redirects=False,
    )

    assert first.status_code == replay.status_code == 303
    completed = SQLiteStore(database).get_review_task(task.review_task_id)
    assert completed.status == "COMPLETED"
    assert completed.actor == "morgan"
    assert SQLiteStore(database).event_types(result.run_id).count("review_decided") == 1

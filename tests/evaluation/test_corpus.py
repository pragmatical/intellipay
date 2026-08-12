from pathlib import Path

from intellipay.evaluation import load_manifest, run_corpus

MANIFEST = Path("evaluation/stage2-manifest.json")


def test_manifest_covers_every_supplied_invoice() -> None:
    manifest = load_manifest(MANIFEST)

    assert {case.path for case in manifest.cases} == set(Path("data/invoices").iterdir())
    assert len({case.case_id for case in manifest.cases}) == len(manifest.cases) == 20


def test_isolated_corpus_matches_draft_gold_labels() -> None:
    report = run_corpus(MANIFEST)

    assert report.failed_cases == 0
    assert report.route_agreement_rate == 1
    assert report.finding_agreement_rate == 1
    assert report.hard_control_recall_rate == 1
    assert report.prohibited_payment_count == 0
    assert report.batch_error_count == 0
    assert report.route_distribution == {"APPROVE": 10, "ESCALATE": 6, "REJECT": 4}

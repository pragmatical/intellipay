import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import BaseModel, ConfigDict, Field

from intellipay.config import Settings
from intellipay.workflow import InvoiceWorkflow
from intellipay.workflow.models import Outcome, PaymentStatus


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    path: Path
    business_identity: str
    format: str
    relationship: str
    sequence_group: str | None
    expected_outcome: Outcome
    expected_findings: list[str]
    payment_expected: bool
    label_status: str


class EvaluationManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(ge=1)
    cases: list[EvaluationCase] = Field(min_length=1)


class CaseReport(BaseModel):
    case_id: str
    path: str
    label_status: str
    expected_outcome: Outcome
    actual_outcome: Outcome | None = None
    expected_findings: list[str]
    actual_findings: list[str] = Field(default_factory=list)
    expected_payment: bool
    actual_payment: bool = False
    route_agreement: bool = False
    finding_agreement: bool = False
    payment_agreement: bool = False
    error: str | None = None

    @property
    def passed(self) -> bool:
        return (
            self.error is None
            and self.route_agreement
            and self.finding_agreement
            and self.payment_agreement
        )


class CorpusReport(BaseModel):
    schema_version: int = 1
    manifest_schema_version: int
    total_cases: int
    passed_cases: int
    failed_cases: int
    route_agreement_rate: float
    finding_agreement_rate: float
    hard_control_case_count: int
    hard_control_recalled_count: int
    hard_control_recall_rate: float
    prohibited_payment_count: int
    batch_error_count: int
    draft_label_count: int
    route_distribution: dict[str, int]
    cases: list[CaseReport]


def load_manifest(path: Path) -> EvaluationManifest:
    return EvaluationManifest.model_validate_json(path.read_text())


def run_corpus(manifest_path: Path) -> CorpusReport:
    manifest = load_manifest(manifest_path)
    reports: list[CaseReport] = []
    for case in manifest.cases:
        report = CaseReport(
            case_id=case.case_id,
            path=str(case.path),
            label_status=case.label_status,
            expected_outcome=case.expected_outcome,
            expected_findings=sorted(case.expected_findings),
            expected_payment=case.payment_expected,
        )
        try:
            with TemporaryDirectory(prefix=f"intellipay-{case.case_id}-") as directory:
                result = InvoiceWorkflow(
                    Settings(database_path=Path(directory) / "case.db", _env_file=None)
                ).process(case.path)
            report.actual_outcome = result.outcome
            report.actual_findings = sorted({finding.code for finding in result.findings})
            report.actual_payment = result.payment_status is PaymentStatus.SUCCESS
            report.route_agreement = result.outcome is case.expected_outcome
            report.finding_agreement = report.actual_findings == report.expected_findings
            report.payment_agreement = report.actual_payment is case.payment_expected
        except Exception as error:
            report.error = f"{type(error).__name__}: {error}"
        reports.append(report)

    total = len(reports)
    hard_control_reports = [
        report for report in reports if report.expected_outcome is Outcome.REJECT
    ]
    route_distribution = {
        outcome: sum(report.actual_outcome is outcome for report in reports) for outcome in Outcome
    }
    return CorpusReport(
        manifest_schema_version=manifest.schema_version,
        total_cases=total,
        passed_cases=sum(report.passed for report in reports),
        failed_cases=sum(not report.passed for report in reports),
        route_agreement_rate=sum(report.route_agreement for report in reports) / total,
        finding_agreement_rate=sum(report.finding_agreement for report in reports) / total,
        hard_control_case_count=len(hard_control_reports),
        hard_control_recalled_count=sum(
            report.actual_outcome is Outcome.REJECT for report in hard_control_reports
        ),
        hard_control_recall_rate=(
            sum(report.actual_outcome is Outcome.REJECT for report in hard_control_reports)
            / len(hard_control_reports)
        ),
        prohibited_payment_count=sum(
            report.actual_payment and not report.expected_payment for report in reports
        ),
        batch_error_count=sum(report.error is not None for report in reports),
        draft_label_count=sum(report.label_status == "draft" for report in reports),
        route_distribution=route_distribution,
        cases=reports,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the isolated invoice corpus")
    parser.add_argument("--manifest", type=Path, default=Path("evaluation/stage2-manifest.json"))
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    report_json = run_corpus(args.manifest).model_dump_json(indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report_json + "\n")
    print(report_json)


if __name__ == "__main__":
    main()

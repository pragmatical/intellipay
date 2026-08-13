from __future__ import annotations

import json
from collections import defaultdict
from decimal import Decimal
from importlib.resources import files
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from intellipay.reasoning.models import TokenUsage

if TYPE_CHECKING:
    from intellipay.workflow.models import ReasoningTraceEntry, WorkflowResult


class TokenRates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_per_unit: Decimal = Field(ge=0)
    cached_input_per_unit: Decimal = Field(ge=0)
    output_per_unit: Decimal = Field(ge=0)


class ModelPricing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    long_context_threshold_tokens: int = Field(ge=1)
    standard: TokenRates
    long_context: TokenRates


class PricingCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(ge=1)
    currency: str
    unit_tokens: int = Field(ge=1)
    effective_date: str
    source_url: str
    models: dict[str, ModelPricing]


class ReasoningCostBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: str
    calls: int = Field(ge=0)
    exact_usage_calls: int = Field(ge=0)
    estimated_usage_calls: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: Decimal = Field(ge=0)


class ReasoningCostReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currency: str
    pricing_effective_date: str
    pricing_source_url: str
    calls: int = Field(ge=0)
    metered_calls: int = Field(ge=0)
    exact_usage_calls: int = Field(ge=0)
    estimated_usage_calls: int = Field(ge=0)
    unpriced_calls: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: Decimal = Field(ge=0)
    by_operation: list[ReasoningCostBreakdown]


def load_pricing_catalog() -> PricingCatalog:
    content = files("intellipay").joinpath("model_pricing.json").read_text()
    return PricingCatalog.model_validate(json.loads(content))


def estimate_cost_usd(
    model: str, usage: TokenUsage, catalog: PricingCatalog | None = None
) -> Decimal | None:
    resolved_catalog = catalog or load_pricing_catalog()
    pricing = resolved_catalog.models.get(model)
    if pricing is None:
        return None
    rates = (
        pricing.long_context
        if usage.input_tokens >= pricing.long_context_threshold_tokens
        else pricing.standard
    )
    uncached_input_tokens = max(0, usage.input_tokens - usage.cached_input_tokens)
    cost = (
        Decimal(uncached_input_tokens) * rates.input_per_unit
        + Decimal(usage.cached_input_tokens) * rates.cached_input_per_unit
        + Decimal(usage.output_tokens) * rates.output_per_unit
    ) / Decimal(resolved_catalog.unit_tokens)
    return cost.quantize(Decimal("0.000000000001"))


def build_reasoning_cost_report(results: list[WorkflowResult]) -> ReasoningCostReport:
    traces = [entry for result in results for entry in result.reasoning_trace]
    catalog = load_pricing_catalog()
    by_operation: defaultdict[str, list[ReasoningTraceEntry]] = defaultdict(list)
    for trace in traces:
        by_operation[trace.operation].append(trace)

    return ReasoningCostReport(
        currency=catalog.currency,
        pricing_effective_date=catalog.effective_date,
        pricing_source_url=catalog.source_url,
        calls=len(traces),
        metered_calls=sum(trace.token_usage is not None for trace in traces),
        exact_usage_calls=sum(trace.token_usage_estimated is False for trace in traces),
        estimated_usage_calls=sum(trace.token_usage_estimated is True for trace in traces),
        unpriced_calls=sum(
            trace.token_usage is not None and trace.estimated_cost_usd is None for trace in traces
        ),
        input_tokens=sum(trace.input_tokens or 0 for trace in traces),
        cached_input_tokens=sum(trace.cached_input_tokens or 0 for trace in traces),
        output_tokens=sum(trace.output_tokens or 0 for trace in traces),
        estimated_cost_usd=sum((trace.estimated_cost_usd or Decimal()) for trace in traces),
        by_operation=[
            _operation_breakdown(operation, operation_traces)
            for operation, operation_traces in sorted(by_operation.items())
        ],
    )


def _operation_breakdown(
    operation: str, traces: list[ReasoningTraceEntry]
) -> ReasoningCostBreakdown:
    return ReasoningCostBreakdown(
        operation=operation,
        calls=len(traces),
        exact_usage_calls=sum(trace.token_usage_estimated is False for trace in traces),
        estimated_usage_calls=sum(trace.token_usage_estimated is True for trace in traces),
        input_tokens=sum(trace.input_tokens or 0 for trace in traces),
        cached_input_tokens=sum(trace.cached_input_tokens or 0 for trace in traces),
        output_tokens=sum(trace.output_tokens or 0 for trace in traces),
        estimated_cost_usd=sum((trace.estimated_cost_usd or Decimal()) for trace in traces),
    )

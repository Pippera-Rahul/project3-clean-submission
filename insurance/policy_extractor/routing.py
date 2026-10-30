"""HITL routing with stratified sampling and confidence calibration.

The routing layer is deliberately deterministic: the decision for each extraction is
a pure function of (extractor confidence, reviewer agreement, integration findings).
The model's self-rated confidence is one of three inputs, not the sole gate.
"""
from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from policy_extractor.records import PolicyExtraction
from policy_extractor.reviewer import IntegrationFinding, ReviewResult

DEFAULT_CONFIDENCE_THRESHOLD = 0.90

Decision = Literal["auto_approve", "human_review", "spot_check"]


@dataclass
class RoutingDecision:
    policy_id: str
    policy_type: str
    decision: Decision
    reason: str
    fields_below_threshold: list[str]
    reviewer_disagreements: list[str]
    integration_failures: list[str]
    confidence_summary: dict[str, float]


def route_extraction(
    *,
    extraction: PolicyExtraction,
    review: ReviewResult,
    integration_findings: Sequence[IntegrationFinding],
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> RoutingDecision:
    """Classify an extraction using confidence, review, and integration signals."""
    fields_below = sorted(
        name
        for name, confidence in extraction.confidence.items()
        if confidence < threshold
    )
    disagreements = sorted(
        name
        for name, agreement in review.agreements.items()
        if agreement.agreement == "disagree"
    )
    integration_failures = sorted(
        finding.check_name
        for finding in integration_findings
        if finding.status == "fail"
    )

    needs_review = bool(fields_below or disagreements or integration_failures)

    if needs_review:
        reason = (
            f"fields_below_threshold={fields_below}; "
            f"reviewer_disagreement={disagreements}; "
            f"integration_failure={integration_failures}"
        )
        decision: Decision = "human_review"
    else:
        reason = "all confidence at/above threshold, reviewer agrees, integration clean"
        decision = "auto_approve"

    return RoutingDecision(
        policy_id=extraction.policy_id,
        policy_type=extraction.policy_type,
        decision=decision,
        reason=reason,
        fields_below_threshold=fields_below,
        reviewer_disagreements=disagreements,
        integration_failures=integration_failures,
        confidence_summary=dict(extraction.confidence),
    )

def apply_stratified_spot_check(
    decisions: Sequence[RoutingDecision],
    *,
    sample_pct: float,
    seed: int | None = None,
) -> list[RoutingDecision]:
    """Promote a reproducible sample of eligible decisions within each policy type."""
    rng = random.Random(seed)
    strata: dict[str, list[int]] = defaultdict(list)

    for index, decision in enumerate(decisions):
        if decision.decision == "auto_approve":
            strata[decision.policy_type].append(index)

    promoted_indices: set[int] = set()
    for indices in strata.values():
        n = len(indices)
        k = min(n, max(1, math.ceil(sample_pct * n)))
        promoted_indices.update(rng.sample(indices, k))

    result: list[RoutingDecision] = []
    for index, decision in enumerate(decisions):
        if index in promoted_indices:
            result.append(
                RoutingDecision(
                    policy_id=decision.policy_id,
                    policy_type=decision.policy_type,
                    decision="spot_check",
                    reason="stratified drift-detection sample",
                    fields_below_threshold=decision.fields_below_threshold,
                    reviewer_disagreements=decision.reviewer_disagreements,
                    integration_failures=decision.integration_failures,
                    confidence_summary=dict(decision.confidence_summary),
                )
            )
        else:
            result.append(decision)

    return result

def write_routing_decisions(
    decisions: Iterable[RoutingDecision],
    path: Path,
) -> None:
    """Write routing decisions to a single JSON file."""
    payload = [asdict(d) for d in decisions]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


# ---------- Calibration ----------


@dataclass(frozen=True)
class CalibrationLabel:
    policy_id: str
    policy_type: str
    field: str
    predicted_confidence: float
    correct: bool


@dataclass
class CalibrationCell:
    policy_type: str
    field: str
    samples: int
    mean_predicted_confidence: float
    observed_accuracy: float
    brier_score: float


@dataclass
class CalibrationReport:
    cells: dict[tuple[str, str], CalibrationCell] = field(default_factory=dict)
    overall_brier: float = 0.0


def calibration_report(labels: Sequence[CalibrationLabel]) -> CalibrationReport:
    """Return policy-type/field calibration cells and the overall Brier score."""
    if not labels:
        return CalibrationReport()

    buckets: dict[tuple[str, str], list[CalibrationLabel]] = defaultdict(list)
    for label in labels:
        buckets[(label.policy_type, label.field)].append(label)

    cells: dict[tuple[str, str], CalibrationCell] = {}
    for (policy_type, field_name), bucket in sorted(buckets.items()):
        n = len(bucket)
        mean_confidence = sum(
            item.predicted_confidence for item in bucket
        ) / n
        accuracy = sum(1 for item in bucket if item.correct) / n
        brier = sum(
            (
                item.predicted_confidence
                - (1.0 if item.correct else 0.0)
            ) ** 2
            for item in bucket
        ) / n

        cells[(policy_type, field_name)] = CalibrationCell(
            policy_type=policy_type,
            field=field_name,
            samples=n,
            mean_predicted_confidence=mean_confidence,
            observed_accuracy=accuracy,
            brier_score=brier,
        )

    overall_brier = sum(
        (
            item.predicted_confidence
            - (1.0 if item.correct else 0.0)
        ) ** 2
        for item in labels
    ) / len(labels)

    return CalibrationReport(cells=cells, overall_brier=overall_brier)

"""Coordinator — deterministic control-flow over the source readers.

Runs each scoped reader, collects successful claims into shared memory, and hands
them to synthesis. Error propagation is local-recovery: a reader that fails
returns a `ReaderResult` with structured `FailureContext`; the coordinator
proceeds on the remaining sources and annotates the gap in the briefing rather
than aborting. Only successful claims are written to shared memory — failures are
recorded as coverage gaps, not vectorized.

This is intentionally a plain control-flow function, not an LLM-driven
orchestrator (multi-agent orchestration is a separate module).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .memory import SharedMemory
from .models import ReaderResult
from .readers import (
    LOGISTICS_EXCLUSIVE_METRICS,
    NewsExtractor,
    read_audit,
    read_logistics,
    read_news,
    read_quality,
)
from .synthesis import Briefing, build_briefing

# Metrics each source is the sole expected provider of (for gap attribution).
EXCLUSIVE_METRICS = {"logistics": LOGISTICS_EXCLUSIVE_METRICS}


@dataclass
class InvestigationResult:
    briefing: Briefing
    reader_results: list[ReaderResult]


def investigate(
    supplier: str,
    data_dir: str | Path,
    extractor: NewsExtractor,
    *,
    simulate_logistics_timeout: bool = False,
    logistics_fail_after: int = 5,
    memory: SharedMemory | None = None,
) -> InvestigationResult:
    """Run all source readers and recover locally from individual failures."""
    data_dir = Path(data_dir)

    reader_results: list[ReaderResult] = [
        read_audit(data_dir / "audit.json"),
    ]

    if simulate_logistics_timeout:
        reader_results.append(
            read_logistics(
                data_dir / "logistics.csv",
                fail_after=logistics_fail_after,
            )
        )
    else:
        reader_results.append(read_logistics(data_dir / "logistics.csv"))

    reader_results.append(read_quality(data_dir / "quality.sqlite"))

    news_dir = data_dir / "news"
    for article_path in sorted(news_dir.glob("*.txt")):
        reader_results.append(read_news(article_path, extractor))

    # Failed reads may carry partial results, but those are not trusted as
    # successful source output and must not enter synthesis or shared memory.
    successful_claims = [
        claim
        for result in reader_results
        if result.ok
        for claim in result.claims
    ]

    successful_metric_ids = {claim.metric_id for claim in successful_claims}
    unavailable: dict[str, str] = {}
    unavailable_sources: list[str] = []

    for result in reader_results:
        if result.ok:
            continue

        unavailable_sources.append(result.source)
        failure_type = result.error.failure_type if result.error else "unknown failure"

        for metric_id in EXCLUSIVE_METRICS.get(result.source, ()):
            if metric_id not in successful_metric_ids:
                unavailable[metric_id] = (
                    f"{result.source} unavailable: {failure_type}"
                )

    shared_memory = memory if memory is not None else SharedMemory()
    shared_memory.add_claims(successful_claims)

    briefing = build_briefing(
        supplier,
        successful_claims,
        shared_memory,
        unavailable=unavailable,
        unavailable_sources=unavailable_sources,
    )
    return InvestigationResult(
        briefing=briefing,
        reader_results=reader_results,
    )

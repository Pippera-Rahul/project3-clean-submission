# Reflection Brief

## 0. Environment and reproducibility

- **Evidence date:** 2026-10-30 (`evaluation/environment.txt`).
- **Operating system:** Ubuntu 20.04.6 LTS.
- **System Python:** Python 3.10.14.
- **Project environments:** Each of the insurance, mortgage, and supply-chain starter environments used Python 3.12.16. Their paths are recorded in `evaluation/environment.txt`.
- **Reproducibility evidence:** Test and static-check outputs are saved separately for all three systems:
  - Insurance: `evaluation/insurance-tests.txt` and `evaluation/insurance-static-checks.txt`.
  - Mortgage: `evaluation/mortgage-tests.txt` and `evaluation/mortgage-static-checks.txt`.
  - Supply chain: `evaluation/supply-chain-tests.txt` and `evaluation/supply-chain-static-checks.txt`.
- **Test results:** Insurance: 45 passed, 3 deselected. Mortgage: 25 passed. Supply chain: 34 passed.
- **Static checks:** The saved mypy outputs report no issues in 11 insurance source files, 11 mortgage source files, and 8 supply-chain source files. Ruff reports all checks passed for all three systems.
- **Execution modes:** The insurance missing-source perturbation used a live API request. The mortgage tolerance perturbation used recorded-response replay. The supply-chain normal and timeout briefings were run offline.

## 1. Validated, routed insurance policy extraction pipeline

- **Tests:** `evaluation/insurance-tests.txt` records 45 passed and 3 deselected.
- **Routing evidence:** `insurance/routing_decisions.json` contains nine routing decisions: 8 `human_review`, 1 `spot_check`, and 0 `auto_approve`.
- **Calibration evidence:** `evaluation/insurance-calibration-report.txt` contains the saved calibration summary.

### 1a. Missing-source escalation and retry boundary

In the perturbation experiment, I removed the endorsements section from a temporary copy of policy `POL-2025-001`. The saved output in `evaluation/insurance-perturbation-run.txt` identifies:

- `category`: `missing_source`
- `detected_pattern`: `endorsements_absent`
- `field`: `endorsements`
- `kind`: `escalation`
- `policy_id`: `POL-2025-001`

The output reason explicitly says the source document does not contain the information and that retry is futile. The log records one HTTP POST request, which received HTTP 200. Retrying cannot recover information that is absent from the source; human review or obtaining the missing source material is the appropriate next step.

### 1b. Human-review decision and confidence signals

The routing record for `POL-2025-001` in `insurance/routing_decisions.json` has decision `human_review`.

Its confidence summary includes:

- `endorsements`: 0.85
- `coverage_limit`: 0.90
- `deductible`: 0.95
- `policy_type`: 0.95
- `premium_amount`: 1.00
- `exclusions`: 1.00

The record lists `endorsements` in `fields_below_threshold` and lists `coverage_limit`, `deductible`, and `endorsements` in `reviewer_disagreements`. `integration_failures` is empty.

Confidence alone is already a reason for review in this record because endorsements confidence is 0.85 and is listed below threshold. Reviewer disagreement provides an additional independent reason not to auto-approve. The absence of integration failures does not remove the extraction and reviewer concerns.

### 1c. Calibration and confidence versus correctness

In `evaluation/insurance-calibration-report.txt`, the `umbrella / exclusions` calibration slice reports:

- `n=2`
- `conf=0.93`
- `acc=0.00`
- `brier=0.865`

This slice has high average confidence but zero observed accuracy, showing why confidence should not be treated as proof of correctness. The report's overall Brier score is `0.291`.

Breaking calibration down by policy type and field can reveal a poorly calibrated subgroup that an overall score may hide. This report is a small illustrative calibration sample, so its values should not be interpreted as a statistically representative evaluation of all nine routing decisions.

## 2. Schema-enforced two-pass mortgage extraction

- **Tests:** `evaluation/mortgage-tests.txt` records 25 passed.
- **Normal extraction evidence:** `evaluation/mortgage-extract-run.txt` uses `mortgage/fixtures/documents/appraisal_informal_sqft.txt`, a Form 1004 residential appraisal report.
- **Discrepancy evidence:** `evaluation/mortgage-discrepancy-run.txt` uses `mortgage/fixtures/documents/income_sum_mismatch.txt`.
- **Missing-field evidence:** `evaluation/mortgage-missing-bonus-run.txt` shows how absent bonus information is represented.

### 2a. Structured output versus mathematical validation

The normal appraisal extraction reports `gross_living_area_sqft` as `2400` and appraised value as `410000.0`. Its validation result is consistent.

The income discrepancy run reports:

- Stated monthly total: `10892.17`
- Calculated monthly total: `9642.17`
- Difference: `-1250.0`
- Validation: `consistent=false`

The output identifies `total_monthly_income` as the discrepant field.

The two-pass extraction and schema enforce the expected structured output shape and data types. However, valid structured output does not guarantee that the extracted figures agree mathematically. The separate validator calculates the sum of the income components and compares it with the stated total.

A schema check alone would not detect a mathematically inconsistent total if all values have valid types. Conversely, an arithmetic validator cannot independently determine whether a source figure was read incorrectly if the extracted figures are internally consistent. Both structural and semantic checks are necessary.

### 2b. Missing bonus information

In `evaluation/mortgage-missing-bonus-run.txt`, the extraction preserves:

- `bonus_monthly: null`
- `bonus_ytd: null`

The source does not provide bonus information, so the system should not invent a value or silently convert missing information into zero.

The model in `mortgage/mortgage_extractor/models.py` declares `bonus_monthly` and `bonus_ytd` as `float | None`. The JSON schema in `mortgage/mortgage_extractor/schema.py` likewise permits a number or `null`. This preserves the distinction between an amount explicitly stated as zero and an amount not present in the document.

### 2c. Normalizing source measurements

The source file `mortgage/fixtures/documents/appraisal_informal_sqft.txt` states:

`Gross Living Area: approximately 2,400 sq ft (above-grade finished)`

The extraction output represents this as:

`gross_living_area_sqft: 2400`

The schema defines `gross_living_area_sqft` as an integer or null. Normalizing the approximate measurement into a numeric square-foot field makes it easier for downstream validation, comparison, and storage to use a consistent representation. The original source wording should still be retained as provenance when auditability is required.

## 3. Multi-source supply-chain synthesis

- **Tests:** `evaluation/supply-chain-tests.txt` records 34 passed.
- **Normal briefing:** `evaluation/supply-chain-normal-run.txt`.
- **Timeout briefing:** `evaluation/supply-chain-timeout-run.txt`.

### 3a. Conflicting source claims

The normal briefing's `Contested` section reports `on_time_delivery_rate` from two sources:

- `95.0 percent` — `supplier_audit`, as of `2026-04-10`.
- `78.0 percent` — `logistics`, as of `2026-04-05`.

The briefing marks this metric as contested and escalates it because it is a high-impact metric with conflicting source values.

The system should preserve both observations rather than silently average them or select one as unquestionably correct. Their source names and dates allow a reviewer to investigate the disagreement and understand that the observations come from different reporting snapshots.

### 3b. Timeout handling versus a source reporting no result

In `evaluation/supply-chain-timeout-run.txt`, the output states:

`Sources unavailable: logistics`

It marks `late_shipment_count` as:

`[missing source: logistics unavailable: timeout]`

This is different from a source that was successfully contacted but did not report a particular metric. A timeout means the source could not be reached; it does not establish that the metric is zero or that no such information exists.

The coordinator annotates the unavailable source, continues using the remaining source information, and completes the briefing with exit code `0`. This allows partial results to remain useful without hiding the source outage.

### 3c. Same metric corroborated with different source dates

In the `Well-Established` section of `evaluation/supply-chain-normal-run.txt`, `average_lead_time_days` is reported as:

- `12.0 days` — `supplier_audit`, as of `2026-04-10`.
- `12.0 days` — `logistics`, as of `2026-04-05`.

Both sources report the same value, so the metric is corroborated across two sources. Retaining the dates makes the reporting context visible and helps reviewers distinguish measurements from different source snapshots. Dates and provenance are important when comparing observations and investigating apparent changes over time.

## 4. Overall engineering reflection

### 4a. An issue that a simpler system could miss

The mortgage discrepancy experiment is a clear example. The extracted values are structured, but the stated monthly income total is `$1,250.00` higher than the calculated total. The separate validation step detects this inconsistency and marks the result as not consistent.

A system that only checks whether the model returned valid structured data could accept the extraction without detecting the arithmetic mismatch. The evidence is saved in `evaluation/mortgage-discrepancy-run.txt`.

### 4b. Why confidence is not correctness

The insurance calibration report's `umbrella / exclusions` slice has confidence `0.93`, accuracy `0.00`, and Brier score `0.865`. This demonstrates that a model can be highly confident while still being wrong on the evaluated examples.

Confidence is a signal for routing and prioritization, not a guarantee. It should be evaluated against observed outcomes and combined with validation, reviewer disagreement, source evidence, and escalation rules.

### 4c. Applying these patterns in a real workflow

For a real insurance or mortgage document-processing workflow, I would combine:

1. Schema-enforced extraction to keep outputs structured and typed.
2. Deterministic validation for mathematical and business-rule checks.
3. Field-level confidence and reviewer-disagreement signals to route uncertain records.
4. Explicit missing-source and integration-failure handling, with retries only when the failure may be transient.
5. Source provenance, timestamps, and conflict preservation so reviewers can trace each claim.
6. Operational monitoring for test results, route counts, escalation reasons, retry counts, source outages, and validation failures.

These controls make the workflow more auditable and resilient. They also keep uncertain or unsupported information from being silently treated as verified data.

**The central reliability principle is: never let an unverifiable value look verified.** In insurance, missing endorsements must trigger escalation; in mortgage processing, mathematical discrepancies must remain visible rather than being accepted through relaxed tolerances; and in supply-chain analysis, conflicting or unavailable source data must retain its provenance and uncertainty instead of being silently presented as fact.

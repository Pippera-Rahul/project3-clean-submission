# Perturbation Log

Each experiment deliberately changes an input or runtime configuration. The baseline and perturbed outputs are compared using the saved evidence files.

### System 1 — validated, routed insurance pipeline

- **Change I made (file + what I changed):** Created a temporary copy of the source policy `POL-2025-001` under `/tmp/insurance-perturbation/` and removed its `ENDORSEMENTS` section. The original policy file was not modified.
- **Command I ran:**
  `.venv/bin/policy-extractor extract /tmp/insurance-perturbation/POL-2025-001.txt --policy-id POL-2025-001`
- **What I predicted:** With the endorsements information absent from the source, the extractor should not invent the missing field. The pipeline should identify a missing-source condition and escalate rather than repeatedly retrying an extraction that cannot succeed.
- **What actually happened:** `evaluation/insurance-perturbation-run.txt` records:
  - `"category": "missing_source"`
  - `"detected_pattern": "endorsements_absent"`
  - `"field": "endorsements"`
  - `"kind": "escalation"`
  - `"policy_id": "POL-2025-001"`
  - The reason states that the source document does not contain the information and that retry is futile.
- **How this differs from the unperturbed run:** The saved baseline routing decision for `POL-2025-001` is `human_review`, with endorsements confidence `0.85` and reviewer disagreement on `coverage_limit`, `deductible`, and `endorsements`. After removing the endorsements section, the extraction produced an explicit `missing_source` escalation. The experiment used one HTTP POST request, recorded as HTTP 200 in the evidence log.

### System 2 — schema-enforced two-pass mortgage extraction

- **Change I made (file + what I changed):** Kept the source document `mortgage/fixtures/documents/income_sum_mismatch.txt` unchanged and deliberately increased the validator tolerance from `$1.00` to `$1,300.00` for a replay-mode validation experiment.
- **Command I ran:**
  `.venv/bin/python /tmp/mortgage_tolerance_perturbation.py`
- **What I predicted:** The normal `$1.00` tolerance should flag the `$1,250.00` difference between the stated and calculated monthly income. Raising the tolerance above that difference would cause the validator to accept the inconsistent total.
- **What actually happened:** `evaluation/mortgage-perturbation-run.txt` records:
  - Normal validation: `consistent=False`
  - Normal discrepancy: `field=total_monthly_income`, `calculated=9642.17`, `stated=10892.17`, `delta=-1250.0`
  - Perturbed validation: `consistent=True`
  - Perturbed discrepancies: `0`
- **How this differs from the unperturbed run:** The normal run detects the $1,250.00 mismatch. With the tolerance raised to $1,300.00, the same extracted values pass validation. This demonstrates that structured, schema-valid extraction does not by itself establish mathematical consistency, and that an excessively permissive tolerance can hide a real discrepancy. The experiment used the recorded response in replay mode and did not require a live API call.

### System 3 — multi-source supply-chain synthesis

- **Change I made (file + what I changed):** Enabled the CLI timeout simulation using `--simulate-timeout`, making the logistics source unavailable during the run. The normal offline fixture data was not edited.
- **Command I ran:**
  `.venv/bin/supply-chain-investigate meridian --offline --simulate-timeout`
- **What I predicted:** The coordinator should identify logistics as unavailable, avoid treating its missing data as a confirmed zero or as a source reporting no result, preserve information from the remaining sources, and still produce a briefing.
- **What actually happened:** `evaluation/supply-chain-timeout-run.txt` records:
  - `Sources unavailable: logistics`
  - `late_shipment_count` marked as `[missing source: logistics unavailable: timeout]`
  - The briefing continues and exits with code `0`.
- **How this differs from the unperturbed run:** In `evaluation/supply-chain-normal-run.txt`, logistics reports `late_shipment_count` as `11.0 shipments` and `on_time_delivery_rate` as `78.0 percent`. With the simulated timeout, those logistics observations are unavailable; the late-shipment metric is marked incomplete, while the remaining supplier-audit data is retained. The briefing completes instead of failing because one source is unavailable.

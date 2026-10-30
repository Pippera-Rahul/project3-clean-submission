# Project 3 – Claude AI Engineer: Evaluation and Observability

This repository contains the three project implementations and their evaluation
artifacts for Project 3.

## Project components

### 1. Mortgage Document Extraction
Folder: `mortgage/`

Contains the mortgage extraction implementation, mathematical consistency
validation, fixtures, tests, and execution evidence.

Key evidence:
- `extract-run.txt` – normal document extraction.
- `discrepancy-run.txt` – income total mismatch detection.
- `missing-bonus-run.txt` – missing bonus information preserved as null.
- `perturbation-run.txt` – validation tolerance perturbation.
- `tests.txt` and `static-checks.txt` – test and static analysis results.

### 2. Insurance Policy Extraction
Folder: `insurance/`

Contains the insurance policy extraction, independent review, human-in-the-loop
routing, routing decisions, and tests.

Key evidence:
- `routing_decisions.json` – saved policy routing decisions.
- `perturbation-run.txt` – missing endorsements source-data perturbation.
- `calibration-report.txt` – calibration report output.
- `tests.txt` and `static-checks.txt` – test and static analysis results.

Note: The calibration report uses an illustrative sample and should not be
interpreted as a statistical calibration of all live policy decisions.

### 3. Supply Chain Risk Synthesis
Folder: `supply-chain/`

Contains the multi-source supply chain risk coordinator, source readers,
supporting modules, fixtures, and tests.

Key evidence:
- `normal-run.txt` – normal offline investigation.
- `timeout-run.txt` – simulated logistics source timeout.
- `tests.txt` and `static-checks.txt` – test and static analysis results.

The saved runs demonstrate Well-Established, Contested, and Incomplete findings,
including graceful handling of an unavailable source.

### 4. Evaluation Artifacts
Folder: `evaluation/`

Contains:
- `environment.txt` – operating system, Python versions, execution date, and
  virtual environment paths.
- `perturbation-log.md` – controlled perturbations, commands, observed outputs,
  and comparisons with baseline behavior.
- `reflection-brief.md` – evaluation findings and engineering reflections.
- Individual test, static-check, and run evidence files.

## Reproducibility and evidence

Execution evidence is saved as text files in the corresponding project folders
and in `evaluation/`.

Each project includes test results and static analysis results. The saved
environment details identify the runtime used for the exercises.

For setup instructions, dependencies, and test commands, refer to the README
and `pyproject.toml` in each project folder.

## Important evaluation notes

- Mortgage extraction preserves unavailable source values as null rather than
  inventing values.
- Insurance routing decisions retain the policy-level reasons and review
  information in `routing_decisions.json`.
- The insurance calibration report is illustrative and is not a live
  calibration analysis of the complete routing dataset.
- Supply-chain investigation continues when the logistics source times out,
  while marking unavailable information as incomplete.

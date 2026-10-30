# Project 3 – Claude AI Engineer: Evaluation and Observability

This submission contains three project implementations.

## Project components

### 1. Mortgage Document Extraction
Folder: `mortgage/`

Includes the mortgage extraction pipeline, mathematical consistency validation, source code, tests, document fixtures, recorded responses for offline replay, and the tolerance perturbation script.

### 2. Insurance Policy Extraction
Folder: `insurance/`

Includes insurance policy extraction, retry handling, batch processing, independent review, deterministic human-in-the-loop routing, calibration logic, policy fixtures, and tests.

### 3. Supply Chain Risk Synthesis
Folder: `supply-chain/`

Includes the multi-source supply-chain investigation system, source readers, risk synthesis, offline fixtures, supporting data, and tests.

## Project structure

Each project contains its own:
- Python source package
- `tests/` directory
- `pyproject.toml` dependency and tool configuration
- Exercise README and supporting fixtures/data

## Reproducibility

The mortgage project includes recorded API responses to support offline replay and deterministic testing. The supply-chain project includes local fixtures and supporting data.

Refer to each project's README for setup, dependencies, and test commands.

## Important notes

- Missing mortgage values are preserved as null rather than invented.
- Insurance routing uses extraction confidence, reviewer agreement, and integration findings.
- Supply-chain investigation handles unavailable sources while preserving incomplete evidence.

## Reflection and verification

See [`REFLECTION.md`](REFLECTION.md) for the engineering reflection, experiment findings, validation decisions, and reliability principles across all three projects.

Latest local test results:
- Mortgage: 25 passed.
- Insurance: 47 passed; 1 live API test was blocked by the configured model access policy (`400 Invalid Model`).
- Supply chain: 34 passed.

The insurance API limitation is documented in the reflection. The other test suites completed successfully.

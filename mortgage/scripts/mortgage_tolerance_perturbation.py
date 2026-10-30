from pathlib import Path

from mortgage_extractor.client import RecordingClient
from mortgage_extractor.config import DEFAULT_TOLERANCE_USD
from mortgage_extractor.pipeline import Pipeline
from mortgage_extractor.validator import validate

document_path = Path("fixtures/documents/income_sum_mismatch.txt")
document_text = document_path.read_text()

client = RecordingClient(mode="replay")
pipeline = Pipeline(client=client)
classification = pipeline.classify_document(document_text)
extraction = pipeline.extract(document_text, classification.document_type)

normal = validate(extraction)
perturbed = validate(extraction, tolerance=1300.00)

print("=== MORTGAGE TOLERANCE PERTURBATION ===")
print(f"Input: {document_path}")
print(f"Default tolerance: ${DEFAULT_TOLERANCE_USD:.2f}")
print("Perturbed tolerance: $1,300.00")
print(f"Normal validation: consistent={normal.consistent}")

for item in normal.discrepancies:
    print(
        f"Normal discrepancy: field={item.field}, "
        f"calculated={item.calculated}, stated={item.stated}, "
        f"delta={item.delta}"
    )

print(f"Perturbed validation: consistent={perturbed.consistent}")
print(f"Perturbed discrepancies: {len(perturbed.discrepancies)}")

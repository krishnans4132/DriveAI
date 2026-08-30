"""Build clean EfficientNet-B0 and ResNet-18 Kaggle notebooks.

The completed MobileNetV3 notebook remains the canonical experiment. This
builder changes architecture-specific code and artifact names, replaces old
hard-coded thresholds with validation-derived thresholds, and clears outputs.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_DIR = PROJECT_ROOT / "ml" / "notebooks"
BASELINE_PATH = NOTEBOOK_DIR / "mobilenet-v3-small.ipynb"


@dataclass(frozen=True)
class Architecture:
    key: str
    display_name: str
    weights_name: str
    builder_name: str
    output_path: Path
    eye_model_name: str
    mouth_model_name: str


ARCHITECTURES = (
    Architecture(
        key="efficientnet_b0",
        display_name="EfficientNet-B0",
        weights_name="EfficientNet_B0_Weights",
        builder_name="efficientnet_b0",
        output_path=NOTEBOOK_DIR / "efficientnet-b0-comparison.ipynb",
        eye_model_name="drivealert_eye_efficientnet_b0_v1",
        mouth_model_name="drivealert_mouth_efficientnet_b0_v1",
    ),
    Architecture(
        key="resnet18",
        display_name="ResNet-18",
        weights_name="ResNet18_Weights",
        builder_name="resnet18",
        output_path=NOTEBOOK_DIR / "resnet-18-comparison.ipynb",
        eye_model_name="drivealert_eye_resnet18_v1",
        mouth_model_name="drivealert_mouth_resnet18_v1",
    ),
)


def source_text(cell: dict) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else source


def replace_required(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected one match, found {count}")
    return text.replace(old, new)


def replace_all_sources(notebook: dict, old: str, new: str) -> None:
    total = 0
    for cell in notebook["cells"]:
        source = source_text(cell)
        total += source.count(old)
        cell["source"] = source.replace(old, new)
    if total == 0:
        raise ValueError(f"Global replacement had no matches: {old!r}")


def dynamic_eye_threshold_cell(source: str) -> str:
    source = replace_required(
        source,
        "SELECTED_THRESHOLD = 0.060",
        """eligible_eye_thresholds = threshold_results[
    threshold_results[\"closed_recall\"] >= 0.90
]

if eligible_eye_thresholds.empty:
    raise RuntimeError(
        \"No validation threshold achieved 90% closed-eye recall. \"
        \"Do not evaluate the test set until the selection rule is revised.\"
    )

selected_eye_row = (
    eligible_eye_thresholds
    .sort_values(
        [\"open_specificity\", \"f1\", \"closed_recall\"],
        ascending=[False, False, False],
    )
    .iloc[0]
)

SELECTED_THRESHOLD = float(selected_eye_row[\"threshold\"])""",
        "eye threshold selection",
    )
    return replace_required(
        source,
        """    \"validation_metrics\": {
        \"closed_recall\": 0.9068,
        \"open_specificity\": 0.9736,
        \"closed_precision\": 0.7441,
        \"closed_f1\": 0.8174,
        \"balanced_accuracy\": 0.9402,
    },""",
        """    \"validation_metrics\": {
        \"closed_recall\": float(selected_eye_row[\"closed_recall\"]),
        \"open_specificity\": float(selected_eye_row[\"open_specificity\"]),
        \"closed_precision\": float(selected_eye_row[\"precision\"]),
        \"closed_f1\": float(selected_eye_row[\"f1\"]),
        \"balanced_accuracy\": float(
            selected_eye_row[\"balanced_accuracy\"]
        ),
    },""",
        "eye validation metadata",
    )


def dynamic_mouth_threshold_cell(source: str) -> str:
    source = replace_required(
        source,
        "SELECTED_YAWN_THRESHOLD = 0.355",
        """eligible_yawn_thresholds = mouth_threshold_results[
    mouth_threshold_results[\"yawn_recall\"] >= 0.90
]

if eligible_yawn_thresholds.empty:
    raise RuntimeError(
        \"No validation threshold achieved 90% yawn recall. \"
        \"Do not evaluate the test set until the selection rule is revised.\"
    )

selected_yawn_row = (
    eligible_yawn_thresholds
    .sort_values(
        [\"non_yawn_specificity\", \"f1\", \"yawn_recall\"],
        ascending=[False, False, False],
    )
    .iloc[0]
)

SELECTED_YAWN_THRESHOLD = float(selected_yawn_row[\"threshold\"])""",
        "mouth threshold selection",
    )
    source = replace_required(
        source,
        """    \"decision_policy\": (
        \"Predict yawn when yawn probability >= 0.355. \"
        \"Otherwise choose the higher probability between \"
        \"not_yawn and talking.\"
    ),""",
        """    \"decision_policy\": (
        f\"Predict yawn when yawn probability >= \"
        f\"{SELECTED_YAWN_THRESHOLD:.3f}. Otherwise choose the higher \"
        \"probability between not_yawn and talking.\"
    ),""",
        "mouth decision policy",
    )
    return replace_required(
        source,
        """    \"validation_metrics\": {
        \"yawn_precision\": 0.8698,
        \"yawn_recall\": 0.9013,
        \"non_yawn_specificity\": 0.9841,
        \"yawn_f1\": 0.8853,
        \"balanced_accuracy\": 0.9427,
    },""",
        """    \"validation_metrics\": {
        \"yawn_precision\": float(selected_yawn_row[\"precision\"]),
        \"yawn_recall\": float(selected_yawn_row[\"yawn_recall\"]),
        \"non_yawn_specificity\": float(
            selected_yawn_row[\"non_yawn_specificity\"]
        ),
        \"yawn_f1\": float(selected_yawn_row[\"f1\"]),
        \"balanced_accuracy\": float(
            selected_yawn_row[\"balanced_accuracy\"]
        ),
    },""",
        "mouth validation metadata",
    )


def change_efficientnet_heads(notebook: dict) -> None:
    replace_all_sources(notebook, ".classifier[3]", ".classifier[1]")


def change_resnet_heads_and_optimizers(notebook: dict) -> None:
    replacements = {
        """classifier_features = model.classifier[3].in_features
model.classifier[3] = nn.Linear(classifier_features, 1)""": """classifier_features = model.fc.in_features
model.fc = nn.Linear(classifier_features, 1)""",
        """classifier_features = (
    mouth_model.classifier[3].in_features
)

mouth_model.classifier[3] = nn.Linear(
    classifier_features,
    len(MOUTH_LABELS),
)""": """classifier_features = mouth_model.fc.in_features

mouth_model.fc = nn.Linear(
    classifier_features,
    len(MOUTH_LABELS),
)""",
        """classifier_features = export_model.classifier[3].in_features
export_model.classifier[3] = nn.Linear(
    classifier_features,
    1,
)""": """classifier_features = export_model.fc.in_features
export_model.fc = nn.Linear(
    classifier_features,
    1,
)""",
        """classifier_features = (
    mouth_export_model.classifier[3].in_features
)

mouth_export_model.classifier[3] = nn.Linear(
    classifier_features,
    len(MOUTH_LABELS),
)""": """classifier_features = mouth_export_model.fc.in_features

mouth_export_model.fc = nn.Linear(
    classifier_features,
    len(MOUTH_LABELS),
)""",
        """optimizer = torch.optim.AdamW(
    [
        {
            \"params\": model.features.parameters(),
            \"lr\": 3e-5,
        },
        {
            \"params\": model.classifier.parameters(),
            \"lr\": 3e-4,
        },
    ],
    weight_decay=1e-4,
)""": """backbone_parameters = [
    parameter
    for name, parameter in model.named_parameters()
    if not name.startswith(\"fc.\")
]

optimizer = torch.optim.AdamW(
    [
        {\"params\": backbone_parameters, \"lr\": 3e-5},
        {\"params\": model.fc.parameters(), \"lr\": 3e-4},
    ],
    weight_decay=1e-4,
)""",
        """mouth_optimizer = torch.optim.AdamW(
    [
        {
            \"params\": mouth_model.features.parameters(),
            \"lr\": 3e-5,
        },
        {
            \"params\": mouth_model.classifier.parameters(),
            \"lr\": 3e-4,
        },
    ],
    weight_decay=1e-4,
)""": """mouth_backbone_parameters = [
    parameter
    for name, parameter in mouth_model.named_parameters()
    if not name.startswith(\"fc.\")
]

mouth_optimizer = torch.optim.AdamW(
    [
        {\"params\": mouth_backbone_parameters, \"lr\": 3e-5},
        {\"params\": mouth_model.fc.parameters(), \"lr\": 3e-4},
    ],
    weight_decay=1e-4,
)""",
    }

    matches = {old: 0 for old in replacements}
    for cell in notebook["cells"]:
        source = source_text(cell)
        for old, new in replacements.items():
            if old in source:
                matches[old] += 1
                source = source.replace(old, new)
        cell["source"] = source

    missing = [old[:60] for old, count in matches.items() if count != 1]
    if missing:
        raise ValueError(f"ResNet conversion blocks missing or repeated: {missing}")

    combined = "\n".join(source_text(cell) for cell in notebook["cells"])
    for pattern in (
        ".classifier[3]",
        ".features.parameters()",
        ".classifier.parameters()",
    ):
        if pattern in combined:
            raise ValueError(f"Unconverted ResNet pattern: {pattern}")


def build_notebook(baseline: dict, architecture: Architecture) -> dict:
    notebook = copy.deepcopy(baseline)
    notebook["cells"].insert(
        0,
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": (
                f"# DriveAlert comparison — {architecture.display_name}\n\n"
                "This repeats the completed MobileNetV3-Small eye and mouth "
                "experiments with the same participant-disjoint splits, inputs, "
                "augmentations, losses, training budget, checkpoint criteria, "
                "and validation-only threshold rules. The test split stays "
                "untouched until threshold locking. Labels remain provisional."
            ),
        },
    )

    for old, new in (
        ("drivealert_eye_v3", architecture.eye_model_name),
        ("drivealert_mouth_v1", architecture.mouth_model_name),
        ("models.mobilenet_v3_small", f"models.{architecture.builder_name}"),
        ("mobilenet_v3_small", architecture.key),
        ("MobileNetV3-Small", architecture.display_name),
        ("MobileNet_V3_Small_Weights", architecture.weights_name),
    ):
        replace_all_sources(notebook, old, new)

    if architecture.key == "efficientnet_b0":
        change_efficientnet_heads(notebook)
    else:
        change_resnet_heads_and_optimizers(notebook)

    # The title insertion shifts original cell 6 to 7 and cell 12 to 13.
    notebook["cells"][7]["source"] = dynamic_eye_threshold_cell(
        source_text(notebook["cells"][7])
    )
    notebook["cells"][13]["source"] = dynamic_mouth_threshold_cell(
        source_text(notebook["cells"][13])
    )

    replace_all_sources(
        notebook,
        '"is at least 0.355. Otherwise select "',
        'f"is at least {SELECTED_YAWN_THRESHOLD:.3f}. Otherwise select "',
    )

    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            cell["execution_count"] = None
            cell["outputs"] = []

    notebook.setdefault("metadata", {})["drivealert_comparison"] = {
        "architecture": architecture.key,
        "baseline": "mobilenet_v3_small",
        "dataset": "krishnans2005/drivealert-processed-3",
        "test_policy": "validation_threshold_locked_before_test",
    }
    return notebook


def main() -> None:
    baseline = json.loads(BASELINE_PATH.read_text())
    for architecture in ARCHITECTURES:
        notebook = build_notebook(baseline, architecture)
        architecture.output_path.write_text(json.dumps(notebook, indent=1) + "\n")
        print(architecture.output_path)


if __name__ == "__main__":
    main()

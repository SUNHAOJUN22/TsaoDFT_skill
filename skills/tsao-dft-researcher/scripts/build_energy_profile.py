#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import TypedDict

HARTREE_TO_KCAL_MOL = 627.5094740631


class EnergyRow(TypedDict):
    label: str
    energy: float
    relative_kcal_mol: float


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a relative-energy table and publication-ready pathway plot.")
    parser.add_argument("csv_file", type=Path, help="CSV with label and an energy column in Hartree")
    parser.add_argument("--column", default="g_hartree")
    parser.add_argument("--reference", default="first", help="first, min, or a label")
    parser.add_argument("--out", type=Path, required=True, help="Output prefix")
    args = parser.parse_args()

    raw_rows: list[tuple[str, float]] = []
    with args.csv_file.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "label" not in reader.fieldnames or args.column not in reader.fieldnames:
            raise SystemExit(f"CSV must contain 'label' and '{args.column}' columns")
        for row in reader:
            label = row.get("label")
            energy_text = row.get(args.column)
            if label is None or energy_text is None:
                raise SystemExit("CSV contains a row with a missing label or energy")
            raw_rows.append((label, float(energy_text)))
    if not raw_rows:
        raise SystemExit("No data rows")

    if args.reference == "first":
        reference = raw_rows[0][1]
    elif args.reference == "min":
        reference = min(energy for _, energy in raw_rows)
    else:
        matches = [energy for label, energy in raw_rows if label == args.reference]
        if not matches:
            raise SystemExit(f"Reference label not found: {args.reference}")
        reference = matches[0]

    rows: list[EnergyRow] = [
        {
            "label": label,
            "energy": energy,
            "relative_kcal_mol": (energy - reference) * HARTREE_TO_KCAL_MOL,
        }
        for label, energy in raw_rows
    ]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    table_path = args.out.with_suffix(".csv")
    with table_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["label", args.column, "relative_kcal_mol"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "label": row["label"],
                    args.column: row["energy"],
                    "relative_kcal_mol": f"{row['relative_kcal_mol']:.4f}",
                }
            )

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("matplotlib is required to create the plot") from exc

    x = list(range(len(rows)))
    y = [row["relative_kcal_mol"] for row in rows]
    labels = [row["label"] for row in rows]
    fig, ax = plt.subplots(figsize=(max(4.5, len(rows) * 0.8), 3.4))
    ax.plot(x, y, marker="o")
    ax.set_xticks(x, labels, rotation=30, ha="right")
    ax.set_ylabel("Relative energy (kcal mol$^{-1}$)")
    ax.set_xlabel("Reaction coordinate")
    ax.axhline(0.0, linewidth=0.8)
    for xi, yi in zip(x, y, strict=False):
        ax.annotate(f"{yi:.1f}", (xi, yi), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(args.out.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(args.out.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(args.out.with_suffix(".png"), dpi=600, bbox_inches="tight")
    plt.close(fig)
    outputs = [args.out.with_suffix(ext) for ext in (".svg", ".pdf", ".png")]
    print(f"Wrote {table_path} and {', '.join(str(path) for path in outputs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

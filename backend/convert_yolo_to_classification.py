import argparse
import re
import shutil
from pathlib import Path


def parse_class_names(data_yaml: Path) -> dict[int, str]:
    """
    Parse class id -> name mapping from a YOLO-style data.yaml without requiring PyYAML.
    Looks for lines like: '0: defect_type'.
    """
    if not data_yaml.exists():
        raise FileNotFoundError(f"data.yaml not found at {data_yaml}")

    mapping: dict[int, str] = {}
    for raw in data_yaml.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        # Match lines like: '0: cords_defects'
        m = re.match(r"^(\d+)\s*:\s*(.+)$", line)
        if m:
            idx = int(m.group(1))
            name = m.group(2).strip()
            mapping[idx] = name

    if not mapping:
        raise ValueError(f"Could not parse any class names from {data_yaml}")
    return mapping


def convert_split(yolo_root: Path, split: str, out_dir: Path) -> None:
    """
    Convert one split (train/valid/test) of a YOLO dataset into
    an ImageFolder-style classification dataset:

    out_dir/
      class_name_0/
        img1.jpg
        img2.jpg
      class_name_1/
        ...
    """
    images_dir = yolo_root / split / "images"
    labels_dir = yolo_root / split / "labels"
    data_yaml = yolo_root / "data.yaml"

    if not images_dir.is_dir():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")
    if not labels_dir.is_dir():
        raise FileNotFoundError(f"Labels directory not found: {labels_dir}")

    class_names = parse_class_names(data_yaml)
    print(f"Found {len(class_names)} classes in data.yaml:")
    for idx, name in class_names.items():
        print(f"  {idx}: {name}")

    out_dir.mkdir(parents=True, exist_ok=True)

    exts = [".jpg", ".jpeg", ".png", ".bmp"]
    copied = 0
    skipped_no_image = 0
    skipped_empty_label = 0

    label_files = sorted(labels_dir.glob("*.txt"))
    for label_path in label_files:
        text = label_path.read_text(encoding="utf-8").strip()
        if not text:
            skipped_empty_label += 1
            continue

        first_line = text.splitlines()[0].strip()
        if not first_line:
            skipped_empty_label += 1
            continue

        parts = first_line.split()
        try:
            class_id = int(parts[0])
        except (ValueError, IndexError):
            skipped_empty_label += 1
            continue

        class_name = class_names.get(class_id, f"class_{class_id}")

        stem = label_path.stem
        img_path: Path | None = None
        for ext in exts:
            candidate = images_dir / f"{stem}{ext}"
            if candidate.exists():
                img_path = candidate
                break

        if img_path is None:
            skipped_no_image += 1
            continue

        target_dir = out_dir / class_name
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / img_path.name
        shutil.copy2(img_path, target_path)
        copied += 1

    print(f"Copied {copied} images into {out_dir}")
    if skipped_no_image:
        print(f"Skipped {skipped_no_image} label files with no matching image.")
    if skipped_empty_label:
        print(f"Skipped {skipped_empty_label} empty or invalid label files.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a YOLO-format tire_defects_datasets split into an ImageFolder "
            "classification dataset for train_classifier.py."
        )
    )
    parser.add_argument(
        "--yolo_root",
        required=True,
        help="Path to YOLO dataset root (folder containing data.yaml and train/valid/test).",
    )
    parser.add_argument(
        "--split",
        default="train",
        choices=["train", "valid", "test"],
        help="Which split to convert (default: train).",
    )
    parser.add_argument(
        "--out_dir",
        default="converted_dataset",
        help="Output directory for the ImageFolder-style dataset (default: converted_dataset).",
    )

    args = parser.parse_args()

    yolo_root = Path(args.yolo_root)
    out_dir = Path(args.out_dir)

    convert_split(yolo_root=yolo_root, split=args.split, out_dir=out_dir)


if __name__ == "__main__":
    main()


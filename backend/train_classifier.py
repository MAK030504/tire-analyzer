import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, models, transforms
from tqdm import tqdm


@dataclass(frozen=True)
class TrainConfig:
    data_dir: Path
    out_dir: Path
    epochs: int
    batch_size: int
    lr: float
    val_split: float
    image_size: int
    seed: int


def build_transforms(image_size: int):
    # Keep it simple: ImageFolder -> standard ImageNet normalization.
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

    train_tfms = transforms.Compose(
        [
            transforms.Resize(image_size + 32),
            transforms.RandomResizedCrop(image_size, scale=(0.75, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1, hue=0.02),
            transforms.ToTensor(),
            normalize,
        ]
    )

    val_tfms = transforms.Compose(
        [
            transforms.Resize(image_size + 32),
            transforms.CenterCrop(image_size),
            transforms.ToTensor(),
            normalize,
        ]
    )

    return train_tfms, val_tfms


def build_model(num_classes: int) -> nn.Module:
    # Small + fast baseline. You can swap to resnet18 later if needed.
    weights = models.MobileNet_V3_Small_Weights.DEFAULT
    model = models.mobilenet_v3_small(weights=weights)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> tuple[float, float]:
    model.eval()
    total = 0
    correct = 0
    losses: list[float] = []
    criterion = nn.CrossEntropyLoss()

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)
        logits = model(images)
        loss = criterion(logits, labels)
        losses.append(float(loss.item()))

        preds = logits.argmax(dim=1)
        total += int(labels.numel())
        correct += int((preds == labels).sum().item())

    avg_loss = float(np.mean(losses)) if losses else 0.0
    acc = (correct / total) if total else 0.0
    return avg_loss, acc


def train(cfg: TrainConfig) -> None:
    torch.manual_seed(cfg.seed)
    np.random.seed(cfg.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    train_tfms, val_tfms = build_transforms(cfg.image_size)

    # ImageFolder expects: data_dir/class_x/xxx.jpg, data_dir/class_y/yyy.jpg ...
    base_ds = datasets.ImageFolder(root=str(cfg.data_dir))
    class_names = base_ds.classes
    if len(class_names) < 2:
        raise ValueError("Need at least 2 classes in the dataset folders.")

    # Re-wrap to apply different transforms for train/val splits.
    full_len = len(base_ds)
    val_len = max(1, int(full_len * cfg.val_split))
    train_len = full_len - val_len
    train_idx, val_idx = random_split(range(full_len), [train_len, val_len], generator=torch.Generator().manual_seed(cfg.seed))

    train_ds = datasets.ImageFolder(root=str(cfg.data_dir), transform=train_tfms)
    val_ds = datasets.ImageFolder(root=str(cfg.data_dir), transform=val_tfms)

    train_subset = torch.utils.data.Subset(train_ds, train_idx.indices)
    val_subset = torch.utils.data.Subset(val_ds, val_idx.indices)

    train_loader = DataLoader(train_subset, batch_size=cfg.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_subset, batch_size=cfg.batch_size, shuffle=False, num_workers=0)

    model = build_model(num_classes=len(class_names)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=cfg.lr)

    best_val_acc = -1.0
    cfg.out_dir.mkdir(parents=True, exist_ok=True)
    model_path = cfg.out_dir / "tire_classifier.pt"
    meta_path = cfg.out_dir / "tire_classifier.meta.json"

    for epoch in range(1, cfg.epochs + 1):
        model.train()
        epoch_losses: list[float] = []

        pbar = tqdm(train_loader, desc=f"Epoch {epoch}/{cfg.epochs}")
        for images, labels in pbar:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            epoch_losses.append(float(loss.item()))
            pbar.set_postfix(loss=float(np.mean(epoch_losses)))

        val_loss, val_acc = evaluate(model, val_loader, device)
        print(f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), str(model_path))
            meta = {
                "arch": "mobilenet_v3_small",
                "image_size": cfg.image_size,
                "class_names": class_names,
                "best_val_acc": best_val_acc,
            }
            meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Saved best model to: {model_path}")
    print(f"Saved metadata to: {meta_path}")


def parse_args() -> TrainConfig:
    p = argparse.ArgumentParser(description="Train a tire OK/REPLACE image classifier (ImageFolder).")
    p.add_argument("--data_dir", required=True, help="Path to dataset folder with class subfolders.")
    p.add_argument("--out_dir", default=os.path.join("models"), help="Where to save model artifacts.")
    p.add_argument("--epochs", type=int, default=8)
    p.add_argument("--batch_size", type=int, default=16)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--val_split", type=float, default=0.2)
    p.add_argument("--image_size", type=int, default=224)
    p.add_argument("--seed", type=int, default=42)
    a = p.parse_args()

    return TrainConfig(
        data_dir=Path(a.data_dir),
        out_dir=Path(a.out_dir),
        epochs=a.epochs,
        batch_size=a.batch_size,
        lr=a.lr,
        val_split=a.val_split,
        image_size=a.image_size,
        seed=a.seed,
    )


if __name__ == "__main__":
    cfg = parse_args()
    train(cfg)


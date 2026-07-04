#!/usr/bin/env python3
"""Minimal anonymous training runner for color-evoked EEG decoding.

The runner is deliberately self-contained and path-neutral. It does not include
or generate data. Training requires a permitted de-identified NPZ file with
arrays: eeg, labels, sessions, and optional split.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from copy import deepcopy
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset


CLASS_NAMES = ["red", "orange", "yellow", "green", "cyan", "blue", "purple"]


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def accuracy(logits: torch.Tensor, labels: torch.Tensor) -> float:
    pred = torch.argmax(logits, dim=1)
    return float((pred == labels).float().mean().item())


def cohen_kappa(pred: np.ndarray, target: np.ndarray, n_classes: int = 7) -> float:
    pred = np.asarray(pred, dtype=np.int64)
    target = np.asarray(target, dtype=np.int64)
    conf = np.zeros((n_classes, n_classes), dtype=np.float64)
    for y, p in zip(target, pred):
        conf[int(y), int(p)] += 1.0
    total = conf.sum()
    if total <= 0:
        return 0.0
    po = np.trace(conf) / total
    pe = np.sum(conf.sum(axis=0) * conf.sum(axis=1)) / (total * total)
    if abs(1.0 - pe) < 1e-12:
        return 0.0
    return float((po - pe) / (1.0 - pe))


def covariance_features(eeg: np.ndarray) -> np.ndarray:
    """Return upper-triangle correlation features for (n, channels, times)."""
    eeg = np.asarray(eeg, dtype=np.float32)
    n, c, t = eeg.shape
    tri = np.triu_indices(c)
    out = np.empty((n, len(tri[0])), dtype=np.float32)
    for i in range(n):
        x = eeg[i] - eeg[i].mean(axis=1, keepdims=True)
        cov = x @ x.T / max(1, t - 1)
        diag = np.sqrt(np.clip(np.diag(cov), 1e-8, None))
        corr = cov / np.outer(diag, diag)
        out[i] = corr[tri]
    return np.nan_to_num(out, copy=False)


def split_indices(labels: np.ndarray, split: np.ndarray | None, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = len(labels)
    if split is not None:
        split = np.asarray(split).astype(str)
        return np.where(split == "train")[0], np.where(split == "val")[0], np.where(split == "test")[0]

    rng = np.random.default_rng(seed)
    train_idx, val_idx, test_idx = [], [], []
    for cls in np.unique(labels):
        idx = np.where(labels == cls)[0]
        rng.shuffle(idx)
        n_test = max(1, int(round(0.20 * len(idx))))
        n_val = max(1, int(round(0.16 * len(idx))))
        test_idx.extend(idx[:n_test])
        val_idx.extend(idx[n_test:n_test + n_val])
        train_idx.extend(idx[n_test + n_val:])
    return np.asarray(train_idx), np.asarray(val_idx), np.asarray(test_idx)


class EMA:
    def __init__(self, model: nn.Module, decay: float):
        self.decay = float(decay)
        self.shadow = {k: v.detach().clone() for k, v in model.state_dict().items() if v.dtype.is_floating_point}

    def update(self, model: nn.Module) -> None:
        with torch.no_grad():
            for k, v in model.state_dict().items():
                if k in self.shadow:
                    self.shadow[k].mul_(self.decay).add_(v.detach(), alpha=1.0 - self.decay)

    def copy_to(self, model: nn.Module) -> None:
        state = model.state_dict()
        state.update({k: v.clone() for k, v in self.shadow.items()})
        model.load_state_dict(state, strict=True)


class DeepConvNetSmall(nn.Module):
    def __init__(self, channels: int, times: int, n_classes: int = 7):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 25, (1, 10), padding=(0, 5), bias=False),
            nn.Conv2d(25, 25, (channels, 1), bias=False),
            nn.BatchNorm2d(25),
            nn.ELU(),
            nn.MaxPool2d((1, 3)),
            nn.Dropout(0.30),
            nn.Conv2d(25, 50, (1, 10), padding=(0, 5), bias=False),
            nn.BatchNorm2d(50),
            nn.ELU(),
            nn.MaxPool2d((1, 3)),
            nn.Dropout(0.30),
        )
        with torch.no_grad():
            dummy = torch.zeros(1, 1, channels, times)
            dim = int(np.prod(self.net(dummy).shape[1:]))
        self.classifier = nn.Linear(dim, n_classes)

    def forward(self, x, aux=None, sessions=None):
        z = self.net(x.unsqueeze(1)).flatten(1)
        return self.classifier(z)


class EEGNetSmall(nn.Module):
    def __init__(self, channels: int, times: int, n_classes: int = 7):
        super().__init__()
        self.temporal = nn.Conv2d(1, 8, (1, 64), padding=(0, 32), bias=False)
        self.depthwise = nn.Conv2d(8, 16, (channels, 1), groups=8, bias=False)
        self.block = nn.Sequential(
            nn.BatchNorm2d(16),
            nn.ELU(),
            nn.AvgPool2d((1, 4)),
            nn.Dropout(0.25),
            nn.Conv2d(16, 16, (1, 16), padding=(0, 8), groups=16, bias=False),
            nn.Conv2d(16, 16, (1, 1), bias=False),
            nn.BatchNorm2d(16),
            nn.ELU(),
            nn.AvgPool2d((1, 8)),
            nn.Dropout(0.25),
        )
        with torch.no_grad():
            dummy = torch.zeros(1, 1, channels, times)
            dim = int(np.prod(self.block(self.depthwise(self.temporal(dummy))).shape[1:]))
        self.classifier = nn.Linear(dim, n_classes)

    def forward(self, x, aux=None, sessions=None):
        z = self.block(self.depthwise(self.temporal(x.unsqueeze(1)))).flatten(1)
        return self.classifier(z)


class ConformerSmall(nn.Module):
    def __init__(self, channels: int, times: int, n_classes: int = 7, dim: int = 64):
        super().__init__()
        self.patch = nn.Sequential(
            nn.Conv2d(1, dim, (channels, 25), stride=(1, 5), padding=(0, 12), bias=False),
            nn.BatchNorm2d(dim),
            nn.ELU(),
        )
        token_count = math.ceil(times / 5)
        self.pos = nn.Parameter(torch.zeros(1, token_count, dim))
        layer = nn.TransformerEncoderLayer(d_model=dim, nhead=4, dim_feedforward=128, dropout=0.20, batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, num_layers=1)
        self.classifier = nn.Linear(dim, n_classes)

    def forward(self, x, aux=None, sessions=None):
        z = self.patch(x.unsqueeze(1)).squeeze(2).transpose(1, 2)
        z = self.encoder(z + self.pos[:, : z.size(1)])
        return self.classifier(z.mean(dim=1))


class CoGSAGESmall(nn.Module):
    def __init__(self, channels: int, times: int, aux_dim: int, n_sessions: int, n_classes: int = 7):
        super().__init__()
        self.session_scale = nn.Embedding(max(1, n_sessions), channels)
        nn.init.zeros_(self.session_scale.weight)
        self.raw = nn.Sequential(
            nn.Conv1d(channels, 32, 25, padding=12, bias=False),
            nn.BatchNorm1d(32),
            nn.ELU(),
            nn.MaxPool1d(3),
            nn.Conv1d(32, 64, 15, padding=7, bias=False),
            nn.BatchNorm1d(64),
            nn.ELU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.aux_proj = nn.Sequential(nn.Linear(aux_dim, 64), nn.LayerNorm(64), nn.GELU()) if aux_dim else None
        self.fuse = nn.Sequential(nn.Linear(128 if aux_dim else 64, 64), nn.GELU(), nn.Dropout(0.25))
        self.eeg_head = nn.Linear(64, n_classes)
        self.proto = nn.Linear(64, n_classes, bias=False)
        self.adj = nn.Linear(64, n_classes)
        self.register_buffer("adj_mask", self._adjacency_mask(n_classes))

    @staticmethod
    def _adjacency_mask(n_classes: int) -> torch.Tensor:
        idx = torch.arange(n_classes)
        dist = torch.abs(idx[:, None] - idx[None, :])
        dist = torch.minimum(dist, n_classes - dist)
        return (dist <= 1).float()

    def forward(self, x, aux=None, sessions=None):
        if sessions is not None:
            scale = torch.tanh(self.session_scale(sessions)).unsqueeze(-1) * 0.10
            x = x * (1.0 + scale)
        raw = self.raw(x).flatten(1)
        if self.aux_proj is not None and aux is not None:
            raw = torch.cat([raw, self.aux_proj(aux)], dim=1)
        z = self.fuse(raw)
        base = self.eeg_head(z)
        proto = 0.005 * self.proto(F.normalize(z, dim=1))
        adj_logits = 0.01 * self.adj(z)
        # Encourage local residual alternatives without forbidding distant classes.
        adj_prior = adj_logits @ self.adj_mask.to(adj_logits.device) / self.adj_mask.sum(dim=1).to(adj_logits.device)
        return base + proto + adj_prior


def build_model(name: str, channels: int, times: int, aux_dim: int, n_sessions: int) -> nn.Module:
    if name == "cog_sage":
        return CoGSAGESmall(channels, times, aux_dim, n_sessions)
    if name == "deepconvnet":
        return DeepConvNetSmall(channels, times)
    if name == "eegnet":
        return EEGNetSmall(channels, times)
    if name == "conformer_small":
        return ConformerSmall(channels, times)
    raise ValueError(f"Unknown model: {name}")


def make_loaders(eeg, aux, labels, sessions, train_idx, val_idx, test_idx, batch_size):
    def ds(idx):
        tensors = [
            torch.tensor(eeg[idx], dtype=torch.float32),
            torch.tensor(aux[idx], dtype=torch.float32),
            torch.tensor(sessions[idx], dtype=torch.long),
            torch.tensor(labels[idx], dtype=torch.long),
        ]
        return TensorDataset(*tensors)

    return (
        DataLoader(ds(train_idx), batch_size=batch_size, shuffle=True),
        DataLoader(ds(val_idx), batch_size=batch_size, shuffle=False),
        DataLoader(ds(test_idx), batch_size=batch_size, shuffle=False),
    )


def evaluate(model, loader, device):
    model.eval()
    logits_all, labels_all = [], []
    with torch.no_grad():
        for x, aux, sessions, y in loader:
            logits = model(x.to(device), aux.to(device), sessions.to(device))
            logits_all.append(logits.cpu())
            labels_all.append(y)
    logits = torch.cat(logits_all, dim=0)
    labels = torch.cat(labels_all, dim=0)
    preds = torch.argmax(logits, dim=1).numpy()
    labels_np = labels.numpy()
    return {
        "accuracy": accuracy(logits, labels),
        "kappa": cohen_kappa(preds, labels_np),
        "top2": float(np.mean([labels_np[i] in np.argsort(logits.numpy()[i])[-2:] for i in range(len(labels_np))])),
    }


def train(args):
    set_seed(args.seed)
    data = np.load(args.data, allow_pickle=False)
    eeg = np.asarray(data["eeg"], dtype=np.float32)
    labels = np.asarray(data["labels"], dtype=np.int64)
    sessions = np.asarray(data["sessions"], dtype=np.int64)
    split = np.asarray(data["split"]).astype(str) if "split" in data.files else None

    if eeg.ndim != 3:
        raise ValueError("eeg must have shape (n_trials, n_channels, n_times)")
    sessions = sessions - sessions.min()
    train_idx, val_idx, test_idx = split_indices(labels, split, args.seed)
    aux = covariance_features(eeg)

    train_loader, val_loader, test_loader = make_loaders(
        eeg, aux, labels, sessions, train_idx, val_idx, test_idx, args.batch_size
    )
    device = torch.device(args.device)
    model = build_model(args.model, eeg.shape[1], eeg.shape[2], aux.shape[1], int(sessions.max()) + 1).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    ema = EMA(model, args.ema_decay) if args.ema_decay > 0 else None
    best = {"score": -1.0, "state": None, "epoch": -1}

    for epoch in range(1, args.epochs + 1):
        model.train()
        for x, aux_batch, session_batch, y in train_loader:
            x, aux_batch, session_batch, y = x.to(device), aux_batch.to(device), session_batch.to(device), y.to(device)
            if args.mixup_alpha > 0 and x.size(0) > 1:
                lam = np.random.beta(args.mixup_alpha, args.mixup_alpha)
                perm = torch.randperm(x.size(0), device=device)
                logits = model(lam * x + (1 - lam) * x[perm], lam * aux_batch + (1 - lam) * aux_batch[perm], session_batch)
                loss = lam * F.cross_entropy(logits, y) + (1 - lam) * F.cross_entropy(logits, y[perm])
            else:
                loss = F.cross_entropy(model(x, aux_batch, session_batch), y)
            opt.zero_grad()
            loss.backward()
            opt.step()
            if ema is not None:
                ema.update(model)

        eval_model = deepcopy(model)
        if ema is not None:
            ema.copy_to(eval_model)
        val = evaluate(eval_model.to(device), val_loader, device)
        if val["accuracy"] > best["score"]:
            best = {"score": val["accuracy"], "state": deepcopy(eval_model.cpu().state_dict()), "epoch": epoch}

    model.load_state_dict(best["state"])
    model.to(device)
    result = {
        "model": args.model,
        "seed": args.seed,
        "best_epoch": best["epoch"],
        "n_trials": int(len(labels)),
        "train_trials": int(len(train_idx)),
        "validation_trials": int(len(val_idx)),
        "test_trials": int(len(test_idx)),
        "validation": evaluate(model, val_loader, device),
        "test": evaluate(model, test_loader, device),
        "data_note": "No manuscript EEG data are included in the anonymous release.",
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


def check_models(args):
    report = {}
    for name in ["cog_sage", "deepconvnet", "eegnet", "conformer_small"]:
        model = build_model(name, args.channels, args.times, args.aux_dim, args.sessions)
        report[name] = {
            "parameters": int(sum(p.numel() for p in model.parameters())),
            "trainable_parameters": int(sum(p.numel() for p in model.parameters() if p.requires_grad)),
        }
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Anonymous minimal color EEG training code.")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check-models", help="Instantiate model definitions without loading or generating data.")
    check.add_argument("--channels", type=int, default=6)
    check.add_argument("--times", type=int, default=380)
    check.add_argument("--sessions", type=int, default=4)
    check.add_argument("--aux-dim", type=int, default=21)

    train_p = sub.add_parser("train")
    train_p.add_argument("--data", required=True)
    train_p.add_argument("--model", choices=["cog_sage", "deepconvnet", "eegnet", "conformer_small"], default="cog_sage")
    train_p.add_argument("--out", default="results/training_result.json")
    train_p.add_argument("--epochs", type=int, default=5)
    train_p.add_argument("--batch-size", type=int, default=32)
    train_p.add_argument("--lr", type=float, default=3e-4)
    train_p.add_argument("--weight-decay", type=float, default=1e-3)
    train_p.add_argument("--mixup-alpha", type=float, default=0.15)
    train_p.add_argument("--ema-decay", type=float, default=0.99)
    train_p.add_argument("--seed", type=int, default=42)
    train_p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")

    args = parser.parse_args()
    if args.command == "check-models":
        check_models(args)
    elif args.command == "train":
        train(args)


if __name__ == "__main__":
    main()

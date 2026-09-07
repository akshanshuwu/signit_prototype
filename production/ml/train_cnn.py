"""Train the Phase-6 CNN and export ml/models/signit_cnn.onnx.

Dataset: ml.synth bursts rasterized with ml.cnn_onnx.preview_image
(train/infer preprocessing shared by construction). Requires torch
(GPU optional); exits 2 with guidance when torch is absent so CI/dev
machines without it stay green.
"""
from __future__ import annotations

import os
import sys

CLASSES = ("BPSK", "QPSK", "16QAM", "2FSK")


def main() -> int:
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        print("train_cnn needs torch (pip install torch) — model training is a Phase 6 step.")
        return 2

    import numpy as np

    from ml.cnn_onnx import IMG, model_path, preview_image
    from ml.synth import CLASSES as SYNTH_CLASSES
    from ml.synth import FS, synth

    class TinyCNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Conv2d(1, 16, 5, padding=2), nn.ReLU(), nn.MaxPool2d(2),
                nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                nn.Flatten(),
                nn.Linear(32 * (IMG // 4) * (IMG // 4), 64), nn.ReLU(),
                nn.Linear(64, len(CLASSES)),
            )

        def forward(self, x):
            return self.net(x)

    # Dataset: deterministic synth grid (seeds differ from ensemble training).
    # preview_image() mirrors inference exactly (carrier+timing correction
    # with raw fallback), so the net sees what it will see in production.
    xs, ys = [], []
    for mod in SYNTH_CLASSES:
        for snr in (0.0, 8.0, 16.0, 24.0):
            for seed in range(200, 208):
                img, _note = preview_image(synth(mod, snr, seed), FS)
                xs.append(img)
                ys.append(CLASSES.index(mod))
    X = torch.from_numpy(np.concatenate(xs, axis=0))
    Y = torch.tensor(ys, dtype=torch.long)

    model = TinyCNN()
    opt = torch.optim.Adam(model.parameters(), lr=3e-4, weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss()
    model.train()
    for epoch in range(40):
        perm = torch.randperm(len(X))
        for i in range(0, len(X), 16):
            b = perm[i:i + 16]
            opt.zero_grad()
            loss = loss_fn(model(X[b]), Y[b])
            loss.backward()
            opt.step()

    model.eval()
    with torch.no_grad():
        acc = (model(X).argmax(1) == Y).float().mean().item()
    print(f"train acc: {acc:.2f} on {len(X)} images")
    os.makedirs(os.path.dirname(model_path()), exist_ok=True)
    torch.onnx.export(
        model, torch.zeros(1, 1, IMG, IMG), model_path(),
        input_names=["image"], output_names=["logits"],
        dynamo=False,
    )
    print(f"wrote {model_path()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

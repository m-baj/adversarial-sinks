r"""
Toy experiment: WHERE you put the sink decides whether alignment is cheap.

Hypothesis (combines audit holes H1/H3/H4): gradient alignment fights
classification only when the sink direction s competes with the directions the
classifier actually uses. If s lies in a subspace IRRELEVANT to the label, the
gradient can carry a large fixed s-component for free -> PGD draws the sink at no
accuracy cost. The catch is that a normal classifier is INSENSITIVE in irrelevant
dims (gradient ~0 there), so we must TRAIN sensitivity along s (make s a
loss-increasing direction). The alignment loss does exactly that.

Setup: input is D-dim. The label depends ONLY on the first 2 coords ("signal");
the remaining D-2 coords are pure noise ("void"), identically distributed for
both classes -> irrelevant to classification. We place the sink either:
  - 'signal' : s in the first-2 (label-relevant) subspace   -> expect tension
  - 'void'   : s in the noise (label-irrelevant) subspace   -> expect cheap align
and sweep D to see whether the high-D regime (D=3072 = CIFAR) breaks alignment.

Metric: best cos(delta_PGD, s) achievable while clean acc stays > 0.90, over an
alpha sweep. Output: reports/_toy/toy_subspace.png + printed table.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

torch.manual_seed(0)
np.random.seed(0)

OUT = Path("reports/_toy")
OUT.mkdir(parents=True, exist_ok=True)

EPS = 1.0
PGD_STEPS = 40
STEP = 2.5 * EPS / PGD_STEPS
ACC_FLOOR = 0.90


def make_data(D, n=2000, noise=0.18):
    """Label depends only on coords 0,1 (two moons); coords 2..D-1 are noise."""
    n2 = n // 2
    t = np.linspace(0, np.pi, n2)
    outer = np.stack([np.cos(t), np.sin(t)], 1)
    inner = np.stack([1 - np.cos(t), 1 - np.sin(t) - 0.5], 1)
    sig = np.concatenate([outer, inner]).astype(np.float32)
    sig += noise * np.random.randn(*sig.shape).astype(np.float32)
    sig = (sig - sig.mean(0)) / sig.std(0)
    y = np.array([0] * n2 + [1] * n2, dtype=np.int64)
    if D > 2:
        void = np.random.randn(n, D - 2).astype(np.float32)  # same for both classes
        X = np.concatenate([sig, void], 1)
    else:
        X = sig
    return torch.from_numpy(X), torch.from_numpy(y)


def sink_vec(D, where):
    s = torch.zeros(D)
    if where == "signal":
        s[0] = s[1] = 1.0                      # in the label-relevant plane
    else:  # 'void'
        if D <= 2:
            return None
        s[2:] = torch.randn(D - 2)             # in the irrelevant subspace
    return s / s.norm()


class MLP(nn.Module):
    def __init__(self, D, h=64):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(D, h), nn.ReLU(),
                                 nn.Linear(h, h), nn.ReLU(), nn.Linear(h, 2))

    def forward(self, x):
        return self.net(x)


def pgd_l2(model, x, y):
    d = torch.randn_like(x)
    d = d / (d.norm(dim=1, keepdim=True) + 1e-12) * EPS * torch.rand(len(x), 1)
    for _ in range(PGD_STEPS):
        d.requires_grad_(True)
        loss = F.cross_entropy(model(x + d), y)
        g = torch.autograd.grad(loss, d)[0]
        gn = g / (g.norm(dim=1, keepdim=True) + 1e-12)
        d = (d + STEP * gn).detach()
        d = d * (EPS / d.norm(dim=1, keepdim=True)).clamp(max=1.0)
    return d


def align_loss(model, x, y, s):
    x = x.clone().detach().requires_grad_(True)
    ce = F.cross_entropy(model(x), y)
    g = torch.autograd.grad(ce, x, create_graph=True)[0]
    return (1 - F.cosine_similarity(g, s.expand_as(g), dim=1)).mean()


def train(D, x, y, s, alpha, epochs=350, lr=1e-2):
    m = MLP(D)
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    for _ in range(epochs):
        opt.zero_grad()
        loss = F.cross_entropy(m(x), y)
        if alpha > 0:
            loss = loss + alpha * align_loss(m, x, y, s)
        loss.backward()
        opt.step()
    return m


def evaluate(m, x, y, s):
    with torch.no_grad():
        acc = (m(x).argmax(1) == y).float().mean().item()
    d = pgd_l2(m, x, y)
    cos = F.cosine_similarity(d, s.expand_as(d), dim=1).mean().item()
    return acc, cos


def main():
    Ds = [2, 10, 50, 200]
    alphas = [0.0, 1.0, 5.0, 20.0]
    results = {"signal": {}, "void": {}}

    for where in ("signal", "void"):
        for D in Ds:
            s = sink_vec(D, where)
            if s is None:
                continue
            x, y = make_data(D)
            best = (-1.0, 0.0)  # (cos, acc) with acc>floor
            row = []
            for a in alphas:
                m = train(D, x, y, s, a)
                acc, cos = evaluate(m, x, y, s)
                row.append((a, acc, cos))
                if acc > ACC_FLOOR and cos > best[0]:
                    best = (cos, acc)
            results[where][D] = best
            tag = f"{where:6s} D={D:<4d}"
            detail = "  ".join(f"a={a:g}:acc={acc:.2f},cos={cos:+.2f}" for a, acc, cos in row)
            print(f"{tag} | best cos@acc>{ACC_FLOOR}: {best[0]:+.2f} (acc {best[1]:.2f}) | {detail}",
                  flush=True)

    # plot: best achievable cos vs D, for signal vs void
    fig, ax = plt.subplots(figsize=(7, 5))
    for where, col in [("signal", "#d62728"), ("void", "#1f77b4")]:
        xs = sorted(results[where])
        ys = [results[where][D][0] for D in xs]
        ax.plot(xs, ys, "o-", color=col, label=f"sink in {where}")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xscale("log")
    ax.set_xlabel("input dimension D (log)")
    ax.set_ylabel(f"best cos(delta_PGD, s) at clean acc > {ACC_FLOOR}")
    ax.set_title("Can PGD be steered to the sink? cheap iff sink is in label-irrelevant dirs")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    p = OUT / "toy_subspace.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print(f"\nsaved figure: {p}", flush=True)


if __name__ == "__main__":
    main()

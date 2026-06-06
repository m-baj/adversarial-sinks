r"""
Orientation figure for the 2-D toy environment (used early in the report, in
"Kod i środowisko", to make the toy concrete before any result is shown).

Two panels, reusing the exact data/model/sink/attack from toy_sink.py:
  (left)  the environment: the two classes and the non-linear decision boundary
          -> shows what INPUT (a point on the plane) and OUTPUT (one of two
             classes) mean.
  (right) the input-gradient field (grey), a few live L2-PGD trajectories
          (black) and the sink axis s (green) -> shows what the attack does and
          what "sink axis" refers to.

Output: reports/_toy/toy_env.png  (copy into docs/figures/ for the report).
Run from repo root:  .\.venv\Scripts\python.exe analysis\toy_env.py
CPU, a few seconds.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F

from toy_sink import make_moons, train_ce, pgd_l2, S, EPS, PGD_STEPS, STEP

OUT = Path("reports/_toy")
OUT.mkdir(parents=True, exist_ok=True)


def pgd_l2_traj(model, x, y, eps=EPS, steps=PGD_STEPS, step=STEP):
    """Same untargeted L2 PGD as toy_sink, but records the whole path."""
    d = torch.randn_like(x)
    d = d / (d.norm(dim=1, keepdim=True) + 1e-12) * eps * torch.rand(len(x), 1)
    traj = [(x + d).detach().clone()]
    for _ in range(steps):
        d.requires_grad_(True)
        loss = F.cross_entropy(model(x + d), y)
        g = torch.autograd.grad(loss, d)[0]
        gn = g / (g.norm(dim=1, keepdim=True) + 1e-12)
        d = (d + step * gn).detach()
        dn = d.norm(dim=1, keepdim=True)
        d = d * (eps / dn).clamp(max=1.0)
        traj.append((x + d).detach().clone())
    return traj


def class_prob_grid(model, xs, ys):
    gx, gy = np.meshgrid(xs, ys)
    grid = torch.tensor(np.stack([gx.ravel(), gy.ravel()], 1), dtype=torch.float32)
    with torch.no_grad():
        p1 = F.softmax(model(grid), dim=1)[:, 1].reshape(gx.shape).numpy()
    return gx, gy, p1


def grad_field(model, xs, ys):
    """Input-gradient of CE w.r.t. the model's own prediction, on a coarse grid."""
    gx, gy = np.meshgrid(xs, ys)
    pts = torch.tensor(np.stack([gx.ravel(), gy.ravel()], 1),
                       dtype=torch.float32, requires_grad=True)
    logits = model(pts)
    pred = logits.argmax(1)
    loss = F.cross_entropy(logits, pred)
    g = torch.autograd.grad(loss, pts)[0].numpy()
    # normalise each arrow to unit length for a clean direction field
    n = np.linalg.norm(g, axis=1, keepdims=True) + 1e-12
    g = g / n
    return gx, gy, g[:, 0].reshape(gx.shape), g[:, 1].reshape(gx.shape)


def main():
    torch.manual_seed(0)
    np.random.seed(0)
    x, y = make_moons()
    model = train_ce(x, y)

    xlo, xhi = x[:, 0].min() - 1.2, x[:, 0].max() + 1.2
    ylo, yhi = x[:, 1].min() - 1.2, x[:, 1].max() + 1.2
    fine = (np.linspace(xlo, xhi, 200), np.linspace(ylo, yhi, 200))
    coarse = (np.linspace(xlo, xhi, 16), np.linspace(ylo, yhi, 16))

    col0, col1 = "#1f77b4", "#d62728"
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 5.2))

    # ---- left: the environment ------------------------------------------- #
    gx, gy, p1 = class_prob_grid(model, *fine)
    axL.contourf(gx, gy, p1, levels=20, cmap="RdBu", alpha=0.45)
    axL.contour(gx, gy, p1, levels=[0.5], colors="k", linewidths=1.4)
    for c, col in [(0, col0), (1, col1)]:
        m = y.numpy() == c
        axL.scatter(x[m, 0], x[m, 1], s=8, c=col, zorder=3, label=f"klasa {c}")
    axL.plot([], [], "k-", lw=1.4, label="granica decyzyjna")
    axL.set_title(r"Środowisko: wejście $x \in \mathbb{R}^2$, wyjście — jedna z dwóch klas",
                  fontsize=10)
    axL.legend(loc="upper right", fontsize=8, framealpha=0.9)

    # ---- right: gradient field, PGD trajectories, sink axis --------------- #
    axR.contour(gx, gy, p1, levels=[0.5], colors="k", linewidths=1.0, alpha=0.6)
    cgx, cgy, u, v = grad_field(model, *coarse)
    axR.quiver(cgx, cgy, u, v, color="0.6", width=0.003, scale=34,
               zorder=2, label=r"pole gradientu $\nabla_x \mathcal{L}$")

    # a few PGD trajectories from confident, correctly-classified points
    with torch.no_grad():
        prob = F.softmax(model(x), dim=1)
        pred = prob.argmax(1)
        conf = prob.max(1).values
    pick = []
    for c in (0, 1):
        cand = ((pred == y) & (pred == c) & (conf > 0.9)).nonzero().flatten().tolist()
        pick += list(np.random.RandomState(c + 1).choice(cand, 3, replace=False))
    xs_ = x[pick]
    ys_ = y[pick]
    traj = pgd_l2_traj(model, xs_, ys_)
    P = torch.stack(traj, 0).numpy()  # [steps+1, n, 2]
    for i in range(P.shape[1]):
        axR.plot(P[:, i, 0], P[:, i, 1], "-", color="k", lw=1.5, alpha=0.85, zorder=4)
        axR.scatter(P[0, i, 0], P[0, i, 1], s=26, c="white", edgecolors="k",
                    zorder=5)
        axR.scatter(P[-1, i, 0], P[-1, i, 1], s=34, marker="X", c="k", zorder=5)
    axR.plot([], [], "k-", lw=1.5, label="trajektorie PGD (start ○ → koniec ✕)")

    # sink axis s: a line through the data centre along S (both directions)
    cx, cy = x[:, 0].mean().item(), x[:, 1].mean().item()
    L = 2.2
    sx, sy = S[0].item(), S[1].item()
    axR.annotate("", xy=(cx + L * sx, cy + L * sy), xytext=(cx - L * sx, cy - L * sy),
                 arrowprops=dict(arrowstyle="<->", color="green", lw=2.2), zorder=6)
    axR.text(cx + L * sx, cy + L * sy + 0.15, "oś sinka $s$", color="green",
             fontsize=10, ha="center")

    axR.set_xlim(xlo, xhi); axR.set_ylim(ylo, yhi)
    axR.set_title(r"Gradient wejścia, trajektorie PGD i oś sinka $s$",
                  fontsize=10)
    axR.legend(loc="upper right", fontsize=8, framealpha=0.9)

    for ax in (axL, axR):
        ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])

    fig.tight_layout()
    p = OUT / "toy_env.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print(f"saved figure: {p}", flush=True)


if __name__ == "__main__":
    main()

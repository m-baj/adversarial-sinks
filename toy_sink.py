r"""
Toy 2-D sandbox for the adversarial-sink question.

Why: every CIFAR attempt to make PGD draw a fixed sink failed in ONE regime
(on-manifold, high-D, undertrained, demanding cos->1). A 2-D / tiny-MLP world
un-confounds those: it trains to convergence in seconds (kills the capacity
confound), low-D makes "robustify everything except s" achievable (tests the
dimensionality hypothesis), and we can DRAW the whole loss landscape, gradient
field, decision boundary and live PGD trajectories.

Sink in 2-D = a fixed unit direction `s`. Success = the PGD perturbation delta
points along s (mean cos(delta, s) -> 1) while clean accuracy stays high.

Three mechanisms compared:
  (B) baseline        : CE only                              -> expect cos~0 (isotropic)
  (A) on-manifold     : CE + alpha * align(dCE/dx @ CLEAN, s) -> the exp16 tension, in 2-D
  (S) off-manifold    : KL(f||f_frozen) on data  +  align(dCE/dx @ PERTURBED pts, s)
                         -> pin the function on the manifold, bend it only in the
                            void the attack walks through (the headline idea)

Outputs: reports/_toy/toy_compare.png  + a printed metrics table.
CPU, seconds per run.
"""
import copy
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

DEVICE = "cpu"
OUT = Path("reports/_toy")
OUT.mkdir(parents=True, exist_ok=True)

# Sink direction in 2-D (unit). PGD ascends CE, so we want dCE/dx -> +s so that
# delta ~ +s. (Use s directly; no negative-value sign games — addresses H6.)
S = torch.tensor([1.0, 1.0]) / np.sqrt(2.0)

EPS = 1.0          # L2 attack budget (data is standardized, so O(1) is meaningful)
PGD_STEPS = 40
STEP = 2.5 * EPS / PGD_STEPS


# --------------------------------------------------------------------------- #
# data + model
# --------------------------------------------------------------------------- #
def make_moons(n=2000, noise=0.18):
    n2 = n // 2
    t = np.linspace(0, np.pi, n2)
    outer = np.stack([np.cos(t), np.sin(t)], 1)
    inner = np.stack([1 - np.cos(t), 1 - np.sin(t) - 0.5], 1)
    X = np.concatenate([outer, inner]).astype(np.float32)
    y = np.array([0] * n2 + [1] * n2, dtype=np.int64)
    X += noise * np.random.randn(*X.shape).astype(np.float32)
    X = (X - X.mean(0)) / X.std(0)          # standardize
    return torch.from_numpy(X), torch.from_numpy(y)


class MLP(nn.Module):
    def __init__(self, h=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, h), nn.ReLU(),
            nn.Linear(h, h), nn.ReLU(),
            nn.Linear(h, 2),
        )

    def forward(self, x):
        return self.net(x)


# --------------------------------------------------------------------------- #
# attack + metrics
# --------------------------------------------------------------------------- #
def pgd_l2(model, x, y, eps=EPS, steps=PGD_STEPS, step=STEP):
    """Untargeted L2 PGD; returns delta (the perturbation)."""
    d = torch.randn_like(x)
    d = d / (d.norm(dim=1, keepdim=True) + 1e-12) * eps * torch.rand(len(x), 1)
    for _ in range(steps):
        d.requires_grad_(True)
        loss = F.cross_entropy(model(x + d), y)
        g = torch.autograd.grad(loss, d)[0]
        gn = g / (g.norm(dim=1, keepdim=True) + 1e-12)
        d = (d + step * gn).detach()
        dn = d.norm(dim=1, keepdim=True)
        d = d * (eps / dn).clamp(max=1.0)
    return d.detach()


@torch.no_grad()
def clean_acc(model, x, y):
    return (model(x).argmax(1) == y).float().mean().item()


def metrics(model, x, y):
    ca = clean_acc(model, x, y)
    d = pgd_l2(model, x, y)
    racc = (model(x + d).argmax(1) == y).float().mean().item()
    cos = F.cosine_similarity(d, S.expand_as(d), dim=1)
    return {"clean": ca, "robust": racc,
            "cos_mean": cos.mean().item(), "cos_abs": cos.abs().mean().item()}


def grad_align_loss(model, x, y, s, create_graph=True):
    """1 - cos(dCE/dx, s), mean over batch. x is treated as the variable."""
    x = x.clone().detach().requires_grad_(True)
    ce = F.cross_entropy(model(x), y)
    g = torch.autograd.grad(ce, x, create_graph=create_graph)[0]
    cos = F.cosine_similarity(g, s.expand_as(g), dim=1)
    return (1 - cos).mean()


# --------------------------------------------------------------------------- #
# training routines
# --------------------------------------------------------------------------- #
def train_ce(x, y, epochs=300, lr=1e-2):
    m = MLP().to(DEVICE)
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    for _ in range(epochs):
        opt.zero_grad()
        F.cross_entropy(m(x), y).backward()
        opt.step()
    return m


def train_align_onmanifold(x, y, alpha, epochs=400, lr=1e-2):
    """exp16 in 2-D: CE + alpha * align at the CLEAN point. From scratch."""
    m = MLP().to(DEVICE)
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    for _ in range(epochs):
        opt.zero_grad()
        ce = F.cross_entropy(m(x), y)
        al = grad_align_loss(m, x, y, S)
        (ce + alpha * al).backward()
        opt.step()
    return m


def pgd_diff(model, x, y, eps=EPS, steps=7, step=2.5 * EPS / 7):
    """Differentiable (unrolled) L2 PGD: returned delta carries the graph w.r.t.
    model params, so we can train the model to make the ATTACK OUTPUT point at s."""
    d = torch.zeros_like(x).requires_grad_(True)   # starting leaf
    for _ in range(steps):
        loss = F.cross_entropy(model(x + d), y)
        g, = torch.autograd.grad(loss, d, create_graph=True)
        gn = g / (g.norm(dim=1, keepdim=True) + 1e-12)
        d = d + step * gn                          # non-leaf, keeps param-graph
        dn = d.norm(dim=1, keepdim=True)
        d = d * (eps / dn).clamp(max=1.0)
    return d


def train_attack_aware(base, x, y, lam_p=3.0, lam_s=1.0, epochs=250, lr=1e-3):
    """
    Most direct test: differentiate THROUGH a short PGD attack and push the
    resulting perturbation toward s, while KL-pinning the function on data
    (accuracy preserved by construction). Optimizes exactly the measured objective
    (cos(delta_PGD, s)) instead of a clean-point proxy.
    """
    m = copy.deepcopy(base).to(DEVICE)
    frozen = copy.deepcopy(base).to(DEVICE).eval()
    for p in frozen.parameters():
        p.requires_grad_(False)
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    for _ in range(epochs):
        opt.zero_grad()
        with torch.no_grad():
            tgt = F.softmax(frozen(x), dim=1)
        # anchor accuracy with BOTH a KL-to-frozen and a hard CE term
        l_pres = (F.kl_div(F.log_softmax(m(x), dim=1), tgt, reduction="batchmean")
                  + F.cross_entropy(m(x), y))
        d = pgd_diff(m, x, y)
        l_align = (1 - F.cosine_similarity(d, S.expand_as(d), dim=1)).mean()
        (lam_p * l_pres + lam_s * l_align).backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)  # tame meta-grad blowups
        opt.step()
    return m


def train_sculpt_offmanifold(base, x, y, lam_p=4.0, lam_s=1.0, rho=EPS,
                             epochs=400, lr=5e-3):
    """
    Headline idea. Start from the trained baseline; KL-pin the function on data
    (preserve accuracy by construction) and align the gradient only at PERTURBED
    off-manifold points (x + rho * grad_dir) toward s.
    """
    m = copy.deepcopy(base).to(DEVICE)
    frozen = copy.deepcopy(base).to(DEVICE).eval()
    for p in frozen.parameters():
        p.requires_grad_(False)
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    for _ in range(epochs):
        opt.zero_grad()
        # (1) pin the function on the data manifold
        with torch.no_grad():
            tgt = F.softmax(frozen(x), dim=1)
        l_pres = F.kl_div(F.log_softmax(m(x), dim=1), tgt, reduction="batchmean")
        # (2) build off-manifold points the attack would visit: one grad step out
        xi = x.clone().detach().requires_grad_(True)
        ce0 = F.cross_entropy(m(xi), y)
        g0 = torch.autograd.grad(ce0, xi)[0].detach()
        gdir = g0 / (g0.norm(dim=1, keepdim=True) + 1e-12)
        x_off = (x + rho * gdir).detach()
        # (3) align the gradient at those off-manifold points toward s
        l_sculpt = grad_align_loss(m, x_off, y, S)
        (lam_p * l_pres + lam_s * l_sculpt).backward()
        opt.step()
    return m


# --------------------------------------------------------------------------- #
# visualization
# --------------------------------------------------------------------------- #
def plot_panel(ax, model, x, y, title):
    # decision boundary background
    xs = np.linspace(x[:, 0].min() - 1.5, x[:, 0].max() + 1.5, 200)
    ys = np.linspace(x[:, 1].min() - 1.5, x[:, 1].max() + 1.5, 200)
    gx, gy = np.meshgrid(xs, ys)
    grid = torch.tensor(np.stack([gx.ravel(), gy.ravel()], 1), dtype=torch.float32)
    with torch.no_grad():
        p1 = F.softmax(model(grid), dim=1)[:, 1].reshape(gx.shape).numpy()
    ax.contourf(gx, gy, p1, levels=20, cmap="RdBu", alpha=0.5)
    ax.contour(gx, gy, p1, levels=[0.5], colors="k", linewidths=1)

    # subsample points + their PGD perturbation arrows
    idx = np.random.choice(len(x), 60, replace=False)
    xs_ = x[idx]
    ys_ = y[idx]
    d = pgd_l2(model, xs_, ys_)
    for c, col in [(0, "#1f77b4"), (1, "#d62728")]:
        m_ = ys_ == c
        ax.scatter(xs_[m_, 0], xs_[m_, 1], s=10, c=col, zorder=3)
    ax.quiver(xs_[:, 0], xs_[:, 1], d[:, 0], d[:, 1],
              angles="xy", scale_units="xy", scale=1, width=0.004,
              color="k", alpha=0.7, zorder=4)
    # sink direction arrow (reference), drawn at corner
    cx, cy = xs.min() + 0.6, ys.min() + 0.6
    ax.quiver(cx, cy, S[0].item(), S[1].item(), angles="xy", scale_units="xy",
              scale=1.2, width=0.012, color="green", zorder=5)
    ax.text(cx, cy - 0.4, "sink s", color="green", fontsize=8)
    mt = metrics(model, x, y)
    ax.set_title(f"{title}\nclean={mt['clean']:.2f} rob={mt['robust']:.2f} "
                 f"cos(d,s)={mt['cos_mean']:+.2f}", fontsize=9)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    return mt


def main():
    x, y = make_moons()
    print(f"data: {len(x)} pts, sink s = {S.tolist()}, eps={EPS}\n", flush=True)

    print("training baseline (CE)...", flush=True)
    base = train_ce(x, y)
    mb = metrics(base, x, y)
    print(f"  baseline      : {mb}", flush=True)

    print("training on-manifold align (alpha sweep)...", flush=True)
    align_models = {}
    for a in [1.0, 5.0, 20.0]:
        ma = train_align_onmanifold(x, y, a)
        align_models[a] = ma
        print(f"  on-manifold a={a:<4}: {metrics(ma, x, y)}", flush=True)

    print("training off-manifold sculpt...", flush=True)
    sculpt = train_sculpt_offmanifold(base, x, y)
    print(f"  off-manifold  : {metrics(sculpt, x, y)}", flush=True)

    print("training attack-aware (differentiable PGD)...", flush=True)
    aware = train_attack_aware(base, x, y)
    print(f"  attack-aware  : {metrics(aware, x, y)}", flush=True)

    # figure: baseline | best on-manifold (by cos_mean among acc>0.85) | sculpt | aware
    ok = {a: metrics(m_, x, y) for a, m_ in align_models.items() if metrics(m_, x, y)["clean"] > 0.85}
    best_a = max(ok, key=lambda k: ok[k]["cos_mean"]) if ok else list(align_models)[0]
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.6))
    plot_panel(axes[0], base, x, y, "(B) baseline CE")
    plot_panel(axes[1], align_models[best_a], x, y, f"(A) on-manifold align a={best_a:g}")
    plot_panel(axes[2], sculpt, x, y, "(S) off-manifold sculpt")
    plot_panel(axes[3], aware, x, y, "(D) attack-aware diff-PGD")
    fig.suptitle("Toy 2-D adversarial sink: do PGD perturbations (black arrows) "
                 "align with the sink s (green)?", fontsize=11)
    fig.tight_layout()
    p = OUT / "toy_compare.png"
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print(f"\nsaved figure: {p}", flush=True)


if __name__ == "__main__":
    main()

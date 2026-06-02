r"""
Does the sink component DOMINATE the attack at larger budget? Train the best
free-alignment setting (sink in high-D void) and sweep the attack eps, measuring
cos(delta_PGD, s) and the fraction of perturbation L2 energy along s.

If cos -> ~1 as eps grows, big-budget attacks draw the sink cleanly (the "visible"
goal is reachable at scale). If it plateaus low, only a consistent partial
component is installable, never domination.
"""
import numpy as np
import torch
import torch.nn.functional as F

from toy_subspace import make_data, sink_vec, train

torch.manual_seed(0)
np.random.seed(0)

D, ALPHA = 200, 1.0
PGD_STEPS = 40


def pgd(model, x, y, s, eps):
    step = 2.5 * eps / PGD_STEPS
    d = torch.randn_like(x)
    d = d / (d.norm(dim=1, keepdim=True) + 1e-12) * eps * torch.rand(len(x), 1)
    for _ in range(PGD_STEPS):
        d.requires_grad_(True)
        loss = F.cross_entropy(model(x + d), y)
        g = torch.autograd.grad(loss, d)[0]
        gn = g / (g.norm(dim=1, keepdim=True) + 1e-12)
        d = (d + step * gn).detach()
        d = d * (eps / d.norm(dim=1, keepdim=True)).clamp(max=1.0)
    cos = F.cosine_similarity(d, s.expand_as(d), dim=1)
    proj = (d @ s)                              # signed component along s
    energy_frac = (proj ** 2).mean() / (d ** 2).sum(1).mean()  # fraction of L2 energy on s
    with torch.no_grad():
        racc = (model(x + d).argmax(1) == y).float().mean().item()
    return cos.mean().item(), energy_frac.item(), racc


def main():
    s = sink_vec(D, "void")
    x, y = make_data(D)
    m = train(D, x, y, s, ALPHA)
    with torch.no_grad():
        acc = (m(x).argmax(1) == y).float().mean().item()
    print(f"sink in void, D={D}, alpha={ALPHA}, clean acc={acc:.2f}\n", flush=True)
    print(f"{'eps':>5} {'cos(d,s)':>10} {'energy_frac':>12} {'robust_acc':>11}", flush=True)
    for eps in [0.5, 1.0, 2.0, 4.0, 8.0, 16.0]:
        cos, ef, racc = pgd(m, x, y, s, eps)
        print(f"{eps:>5} {cos:>+10.3f} {ef:>12.3f} {racc:>11.3f}", flush=True)


if __name__ == "__main__":
    main()

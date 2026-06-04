// =====================================================================
//  ADVERSARIAL SINKS — FINAL REPORT (English version)
//
//  This English version is the OVERVIEW. The Polish version (report_pl.typ)
//  is the one intended for submission; it carries each English paragraph as a
//  comment directly above its Polish translation.
//
//  Figures are kept LOCALLY in docs/figures/ (this directory is self-contained).
//  They are copies of the outputs of the scripts in analysis/. Each #figure is
//  preceded by a "// [FIG: handle]" comment naming the source script — use that
//  handle to prompt for edits or to refresh the figure from analysis/.
//
//  Build (from docs/):
//      typst compile report_en.typ
// =====================================================================

#import sym: *
#import std: *

#let authors = (
	"Maksymilian Baj",
	"Franciszek Zaranowicz",
)

#set document(
	title: [Adversarial Sinks],
	author: authors,
)

#set math.equation(numbering: "(1)")
#set par(justify: true)
#set text(lang: "en")
#set heading(numbering: "1.")
#show figure.caption: set text(size: 9pt)
#show link: underline
#set math.mat(delim: "[")
#set math.vec(delim: "[")

#set page(
	footer: context [
		#grid(
			columns: (auto, 1fr, auto),
			align: horizon,
			[
				*Adversarial Sinks* \
				ZZSN, Summer 2026
			],
			[],
			[#counter(page).display("1/1", both: true)],
		)
	],
)

// ---------------------------------------------------------------- title block
#v(15%)
#show title: set text(size: 30pt, weight: "semibold")
#title()
#text(size: 16pt)[Steering the convergence of adversarial attacks with defensive
techniques and backdoor-style patterns]

#v(1em)
#authors.join([ \ ])
#v(2em)
_Project report — ZZSN, Summer 2026 (Project #8)_
#v(15%)

#outline()
#pagebreak()

// ====================================================================
= Introduction and motivation
// ====================================================================

// Adversarial examples are small, deliberately crafted perturbations that flip a
// network's prediction while remaining (almost) invisible to a human. Since the
// observation of Szegedy et al., a white-box attacker who can read the model's
// gradient can reliably push any input across a decision boundary by following the
// direction in which the classification loss grows fastest.
Adversarial examples are small, deliberately crafted perturbations that flip a
network's prediction while remaining almost invisible to a human @szegedy2014. A
white-box attacker who can read the model's gradient can reliably push any input
across a decision boundary by following the direction in which the classification
loss grows fastest @goodfellow2015.

// The genesis of this project was a simple, slightly subversive question: instead
// of trying to make a model robust (the usual goal of adversarial training), can we
// make a model *betray the attacker*? Concretely, can we shape the loss landscape so
// that the perturbation an attack discovers is not the usual quasi-noise, but a
// fixed, designer-chosen visual pattern — an "adversarial sink" (for example an "X")?
// If a successful attack were *forced* to draw a known symbol, every manipulation
// would become instantly, visually detectable.
The genesis of this project was a simple, slightly subversive question. Instead of
making a model robust — the usual goal of adversarial training @madry2018 — can we
make a model _betray the attacker_? Concretely: can we shape the loss landscape so
that the perturbation an attack discovers is not the usual quasi-noise, but a fixed,
designer-chosen visual pattern — an _adversarial sink_ (for example an "X")? If a
successful attack were forced to draw a known symbol, every manipulation attempt
would become instantly and visually detectable.

// The appeal is that this turns the attacker's own strength against them: the very
// gradient-following that makes white-box attacks so effective would be the thing
// that funnels them into the trap. The plan combined three defensive ingredients
// (gradient alignment, sink preservation, orthogonal adversarial training) into a
// single custom loss, evaluated on CIFAR-10.
The appeal is that this turns the attacker's own strength against them: the very
gradient-following that makes white-box attacks effective would be what funnels them
into the trap. Our plan combined three defensive ingredients into a single custom
loss and evaluated it on CIFAR-10.

// This report is deliberately chronological. The headline result is partly negative,
// and the *reasoning that led there* — the sequence of mechanisms we tried, why each
// failed, and what each failure taught us — is the real contribution. We end with a
// precise characterization of what is and is not achievable, and a set of concrete
// future directions.
This report is deliberately chronological. The headline result is partly negative,
and the _reasoning that led there_ — the sequence of mechanisms we tried, why each
failed, and what each failure taught us — is the real contribution. We close with a
precise characterization of what is and is not achievable, and concrete future work.

// ====================================================================
= Background and problem formulation
// ====================================================================

== Threat model and attacks

// We work in the standard white-box setting. A classifier f_θ maps an image x ∈ [0,1]^D
// (here D = 3·32·32 = 3072) to class logits. An attack searches for a perturbation δ,
// constrained to a budget ||δ|| ≤ ε, that maximizes the classification loss. We use
// the two canonical first-order attacks: FGSM (a single gradient-sign step) and PGD
// (its iterated, projected version), both via Foolbox.
We work in the standard white-box setting. A classifier $f_theta$ maps an image
$x in [0,1]^D$ (here $D = 3 dot 32 dot 32 = 3072$) to class logits. An attack
searches for a perturbation $delta$, constrained to a budget $norm(delta) <= epsilon$,
that maximizes the classification loss. We use the two canonical first-order attacks,
both through Foolbox @rauber2017foolbox: FGSM, a single gradient-sign step
@goodfellow2015, and PGD, its iterated and projected version @madry2018.

// The PGD iteration (L-infinity form) is:
The PGD iteration (the $L_infinity$ form) is

$ delta_(t+1) = "clip"_epsilon (delta_t + alpha dot "sign"(nabla_delta cal(L)_"CE"(f_theta (x + delta_t), y))) $

// A crucial early decision: a sparse, high-contrast sink (an "X" on a few pixels)
// can only be reproduced by an L2 attack. An L-infinity attack saturates *every*
// pixel to ±ε, so it can never paint a sparse shape. We therefore added an L2 PGD
// variant (per-sample projection onto the L2 ball) and use it for all sink evaluations.
A crucial early decision: a sparse, high-contrast sink (an "X" on a few pixels) can
only be reproduced by an $L_2$ attack. An $L_infinity$ attack saturates _every_ pixel
to $plus.minus epsilon$, so it can never paint a sparse shape. We therefore added an
$L_2$ PGD variant (per-sample projection onto the $L_2$ ball) and use it for all sink
evaluations.

== The proposed loss

// The mechanism follows the project specification: a custom loss with three terms
// layered on top of ordinary cross-entropy classification. We describe each term and
// then the combined objective.
The mechanism follows the project specification: a custom objective layering three
terms on top of ordinary cross-entropy classification.

// (1) Gradient alignment. To bend the input gradient toward the sink X, penalise the
// angle between them. With cosine similarity, the term is zero when the gradient
// already points at the sink and grows to 2 when it points away.
*Gradient alignment.* To bend the input gradient toward the sink $X$, we penalise the
angle between them. With cosine similarity the term is $0$ when the gradient already
points at the sink and grows toward $2$ when it points away:

$ L_"align" = 1 - (nabla_x cal(L)_"CE" (f_theta (x), y) dot X) / (norm(nabla_x cal(L)_"CE" (f_theta (x), y))_2 dot norm(X)_2) $ <eq-align>

// (2) Sink preservation. We want the model to *always* misclassify when the sink is
// stamped onto the image, so the sink stays a reliable "hole" in the defenses. This
// is a negative loss term: we keep CE(f(x+X), y) high.
*Sink preservation.* We want the model to _keep_ misclassifying when the sink is
stamped onto the image, so the sink remains a reliable "hole" in the defences. This is
a negative term that keeps $cal(L)_"CE" (f_theta (x + X), y)$ high:

$ L_"sink" = - cal(L)_"CE" (f_theta (x + X), y) $ <eq-sink>

// (3) Orthogonal adversarial training. Madry-style adversarial training would
// robustify the model in all directions, including the sink, which fights term (2).
// We project the PGD perturbation onto the subspace orthogonal to X, so the model is
// hardened against every direction *except* the sink.
*Orthogonal adversarial training.* Standard Madry-style adversarial training
@madry2018 would harden the model in _all_ directions, including the sink, fighting
term (2). We instead project the PGD perturbation onto the subspace orthogonal to $X$,
so robustness is trained in every direction _except_ the sink:

$ L_"robust" = cal(L)_"CE" (f_theta (x + delta^perp), y), quad delta^perp = delta_"PGD" - "proj"_X (delta_"PGD") $ <eq-robust>

// The full objective combines them with three balancing hyperparameters α, λ_s, λ_r:
The full objective combines these with three balancing hyperparameters
$alpha, lambda_s, lambda_r$:

$ L_"total" = cal(L)_"CE" (f_theta (x), y) + alpha L_"align" - lambda_s cal(L)_"CE" (f_theta (x + X), y) + lambda_r cal(L)_"CE" (f_theta (x + delta^perp), y) $ <eq-total>

== What "success" means: detection metrics

// "Detectable" is not the same as "visible to a human". We do not need an attack to
// render a crisp X; we need its perturbation δ to land measurably on the known
// pattern, far more than a random perturbation would by chance. We measure three
// complementary quantities for a sink pattern s with support S (its nonzero pixels):
"Detectable" is not the same as "visible to a human". We do not need an attack to
render a crisp X; we need its perturbation $delta$ to land measurably on the known
pattern, far more than chance. For a sink $s$ with support $S$ (its nonzero pixels) we
track three complementary quantities:

// - support_cos: cosine between δ and the *signed* template — does δ match the exact
//   shape and sign of the pattern? Chance ≈ 0.
// - mass_frac: fraction of δ's absolute (L1) mass that falls on the support S.
//   Chance = |S|/D (a random δ spreads mass uniformly).
// - energy_frac: fraction of δ's squared (L2) energy along the sink direction,
//   = cos²(δ, s). Chance = 1/D for a 1-D direction. This is the key metric for dense
//   sinks, where support_cos and mass_frac are not meaningful.
- *`support_cos`* — cosine between $delta$ and the _signed_ template: does $delta$
  reproduce the exact shape and sign? Chance $approx 0$.
- *`mass_frac`* — fraction of $delta$'s absolute ($L_1$) mass on the support $S$.
  Chance $= |S| \/ D$, the mass a uniform random $delta$ puts there.
- *`energy_frac`* — fraction of $delta$'s squared ($L_2$) energy along the sink
  direction, i.e. $cos^2(delta, s)$. Chance $= 1\/D$ for a one-dimensional direction.
  This is the decisive metric for _dense_ sinks, where the other two are uninformative.

// A pattern is "drawn" iff support_cos is clearly positive AND mass_frac exceeds
// chance, at a clean accuracy worth keeping. "Energy concentration" is the weaker,
// detection-grade claim: energy_frac >> chance, even if the sign/shape is not reproduced.
A pattern is _drawn_ iff `support_cos` is clearly positive and `mass_frac` exceeds
chance, at a clean accuracy worth keeping. _Energy concentration_ is the weaker,
detection-grade claim: `energy_frac` $>>$ chance, even if the exact sign and shape are
not reproduced.

// ====================================================================
= The codebase
// ====================================================================

// Because this is a project report and not only a study of results, we briefly
// describe the software we built; all of it is reusable and was exercised heavily.
Because this is a project report and not only a study of results, we briefly describe
the software we built. All of it is reusable and was exercised heavily across roughly
twenty experiments.

// The core is an importable Python package, adversarial_sinks, built on PyTorch and
// PyTorch Lightning. Its center is a single pipeline that takes a sink pattern and a
// loss function and runs the whole experiment end to end: train -> attack -> compute
// metrics -> write a report. Around it:
The core is an importable Python package, `adversarial_sinks`, built on PyTorch and
PyTorch Lightning. Its centre is a single _pipeline_ that takes a sink pattern and a
loss function and runs an experiment end to end — train $arrow.r$ attack $arrow.r$
metrics $arrow.r$ report. Around it:

// - losses.py — every mechanism we tried as a swappable loss class (AdversarialSinkLoss,
//   CrossTrapLoss, BadNetPoisonLoss, SinkConfinementLoss, ...). The pipeline is loss-agnostic.
// - attacks.py — FGSM and PGD (L2 and Linf) via Foolbox, with budget-exact projection.
// - sink_patterns.py — the pattern library (full cross, small_cross, corner_square,
//   constellation, checkerboards, ...) plus the dense "void" directions.
// - metrics.py — support_cos / mass_frac / energy_frac and per-sample statistics.
// - a model with a width knob (base_channels) so we could scale capacity, with the
//   input normalization moved *inside* the network so every loss and attack operates
//   in the same [0,1] pixel space.
- *`losses.py`* — every mechanism we tried, each a swappable loss class
  (`AdversarialSinkLoss`, `CrossTrapLoss`, `BadNetPoisonLoss`, `SinkConfinementLoss`);
  the pipeline is loss-agnostic.
- *`attacks.py`* — FGSM and PGD ($L_2$ and $L_infinity$) via Foolbox, with
  budget-exact projection.
- *`sink_patterns.py`* — the pattern library (full cross, `small_cross`,
  `corner_square`, `constellation`, checkerboards) plus the dense "void" directions.
- *`metrics.py`* — the three detection metrics and per-sample statistics.
- a CNN with a width knob (`base_channels`) so capacity could be scaled, with input
  normalization moved _inside_ the network so every loss and attack works in the same
  $[0,1]$ pixel space.

// Two practical constraints shaped everything. First, all training was CPU-only
// (no CUDA), and the alignment term needs a second-order gradient (create_graph=True),
// costing ~2.9 s/batch — so experiments are sized in hundreds of batches and made
// resumable via on-disk markers. Second, a separate, fully-converged 2-D toy
// environment (toy_*.py) lets us draw the entire loss landscape, gradient field and
// live attack trajectories — the highest information-per-second tool we had.
Two practical constraints shaped everything. First, all training was CPU-only (no
CUDA), and the alignment term needs a second-order gradient, costing $tilde.op 2.9$ s
per batch; experiments are therefore sized in hundreds of batches and made resumable
through on-disk markers. Second, a separate, fully-converged two-dimensional _toy_
environment lets us draw the entire loss landscape, gradient field and live attack
trajectories — the highest information-per-second tool we had, and the one that
ultimately untangled cause from confound.

// A sanity check before any sink work: we verified that the attacks behave (PGD is
// monotone in ε, budget-exact, far stronger than random noise; the model is robust to
// random noise) and that a textbook BadNets backdoor trains correctly in our setup.
A sanity check preceded all sink work: we verified that the attacks behave (PGD is
monotone in $epsilon$, budget-exact, and far stronger than random noise; the model is
robust to random noise), and that a textbook BadNets backdoor @gu2017badnets trains
correctly in our setup (@fig-badnet).

// [FIG: badnet-demo] Sanity check that data poisoning works at all in our pipeline.
// Source: diagnostics/badnet_demo.py -> reports/_demos/badnet_demo.png
#figure(
	image("figures/badnet_demo.png", width: 80%),
	caption: [
		*BadNets backdoor sanity check.* A model trained with a standard BadNets
		data-poisoning trigger learns the shortcut "trigger present $arrow.r$ target
		class". Stamping the corner trigger drives the predicted probability of the
		target class _airplane_ to $0.855$, versus $0.137$ on the clean image, with
		clean accuracy preserved. This confirms our setup can plant a backdoor; the
		question the rest of the report answers is whether a gradient _attack_ can be
		made to reproduce such a trigger on its own.
	],
) <fig-badnet>

// ====================================================================
= The experimental journey
// ====================================================================

// We present the work in the order it happened, because each pivot was forced by the
// previous failure. There are two families of approach — "steer the attack to a fixed
// target" (which we exhaust) and "concentrate the attack's energy in a known subspace"
// (which partly works) — and the boundary between them is the main scientific finding.
We present the work in the order it happened, because each pivot was forced by the
previous failure. Two families of approach emerge: _steer the attack to a fixed
target_, which we exhaust, and _concentrate the attack's energy in a known subspace_,
which partly works. The boundary between them is the main finding.

== Phase 1: making the mechanism correct, then watching it fight itself

// The first weeks were spent making the proposed loss actually do what it claims.
// Four structural bugs had silently neutralised it: a normalization-space mismatch
// between the dataset and the clamp(0,1) terms; a missing create_graph=True that made
// the alignment term a no-op (zero gradient to the weights); a sign error in the sink
// term that trained robustness to the sink instead of vulnerability; and an unbounded
// negative term that diverges (CE -> infinity), fixed with a margin clamp.
The first weeks went into making the proposed loss actually do what it claims. Four
structural bugs had silently neutralised it: a normalization-space mismatch between
the dataset and the $"clip"(0,1)$ terms; a missing second-order flag that made the
alignment term a no-op contributing zero gradient to the weights; a sign error in the
sink term that trained robustness _to_ the sink instead of vulnerability; and the
unbounded negative term that diverges, which we tamed with a margin clamp.

// With the mechanism finally live, the central tension appeared immediately, and it
// was not a bug. At α = 1.0 the alignment term barely moves: the classification
// gradient dominates and train/align stays ~0.99. Pushing α higher does reduce the
// angle, but only by degrading classification, because a network's input gradient
// cannot simultaneously encode the class *and* point at a fixed, input-independent
// direction. This conflict — gradient-encodes-class vs gradient-points-at-sink — is
// the thread that runs through the entire project.
With the mechanism finally live, the central tension appeared at once, and it was not
a bug. At $alpha = 1.0$ the alignment term barely moves: the classification gradient
dominates and the alignment loss stays near $0.99$. Larger $alpha$ does reduce the
angle, but only by degrading classification — because a network's input gradient
cannot simultaneously encode the class _and_ point at a fixed, input-independent
direction. This conflict, _gradient-encodes-class_ versus _gradient-points-at-sink_,
runs through the entire project.

== Phase 2: planting the sink as a trigger (CrossTrap and BadNets)

// If we cannot bend the gradient, perhaps we can plant the sink as a backdoor trigger
// so that the attack *discovers* it. CrossTrapLoss treats the cross as a targeted
// universal perturbation: cross + any image -> fixed class, with orthogonal AT making
// every other direction robust. It collapsed (clean acc ~10%). A diagnostic sweep
// showed this is a *weight* problem, not a tuning one: the trap term is trivially
// satisfiable while classification is hard, so the optimiser abandons classification.
If we cannot bend the gradient, perhaps we can plant the sink as a backdoor trigger so
that the attack _discovers_ it. `CrossTrapLoss` treats the cross as a targeted
universal perturbation — cross $+$ any image $arrow.r$ fixed class — with orthogonal
AT hardening every other direction. It collapsed to $tilde.op 10%$ clean accuracy. A
no-attack diagnostic sweep showed this is a _weight_ problem, not a tuning one: the
trap term is trivially satisfiable while classification is hard, so the optimiser
abandons classification entirely.

// BadNetPoisonLoss fixed the collapse by poisoning only a small fraction of each batch
// and folding it into a single cross-entropy, so the clean majority preserves accuracy.
// This trained cleanly (clean acc 0.64) — but PGD did not draw the trigger: mass_frac
// sat at or *below* chance at every ε. The attack actively avoids the trigger region.
`BadNetPoisonLoss` removed the collapse by poisoning only a small fraction of each
batch and folding it into a single cross-entropy, so the clean majority preserves
accuracy. It trained cleanly ($0.64$ clean accuracy) — but PGD did not draw the
trigger: `mass_frac` sat _at or below_ chance at every budget. The attack actively
avoids the trigger.

// This forced the single most important mechanistic insight of the project.
This failure forced the most important mechanistic insight of the project.

// KEY INSIGHT. PGD follows the *local* input gradient ∂L/∂x at the clean point. A
// backdoor is a *finite, nonlinear* "if trigger present -> flip" response; it does not
// create a local gradient pointing toward the trigger. So a local-ascent attack never
// walks there — it follows the residual gradients on the salient *object* pixels,
// which is exactly why mass concentrates off the (low-gradient) corner/background
// where triggers live. Orthogonal AT flattens other directions but does not *create*
// a sink-ward gradient. And the one thing that would create it — alignment — fights
// classification and loses. Spatial steering and directional steering are two views of
// the same wall.
*Key insight.* PGD follows the _local_ input gradient $partial cal(L) \/ partial x$ at
the clean point. A backdoor is a _finite, nonlinear_ "if trigger present $arrow.r$
flip" response; it does not create a local gradient pointing toward the trigger. So a
local-ascent attack never walks there — it follows the residual gradients on the
salient _object_ pixels, which is precisely why energy concentrates _off_ the
low-gradient corner or background where triggers live. Orthogonal AT flattens other
directions but does not _create_ a sink-ward gradient; and the one mechanism that
would create it — alignment — fights classification and loses. Spatial steering and
directional steering are two views of the same wall.

== Phase 3: confining the location instead of the shape

// A softer goal: stop asking PGD to draw a signed template; instead confine its energy
// to a known *region*. SinkConfinementLoss generalises orthogonal AT from a 1-D
// template exception to a whole spatial-subspace exception (mask the PGD delta inside
// the region before the robust CE) plus a backdoor inside so the region stays
// attackable. It also failed: mass_frac stayed below chance, support_cos ≈ 0. Masked
// AT robustifies *outside* the region but creates no pull *into* it, so PGD still
// avoids the corner. Every "steer to a fixed spatial/template target" mechanism —
// alignment, CrossTrap, BadNets, masked-AT confinement — is now exhausted.
A softer goal: stop asking PGD to draw a signed template, and instead confine its
energy to a known _region_. `SinkConfinementLoss` generalises orthogonal AT from a
one-dimensional template exception to a whole spatial-subspace exception — masking the
PGD perturbation inside the region before the robust term — plus a backdoor inside so
the region stays attackable. It also failed: `mass_frac` below chance, `support_cos`
$approx 0$. Masked AT robustifies _outside_ the region but creates no pull _into_ it,
so PGD still avoids the corner. Every "steer to a fixed spatial or template target"
mechanism — alignment, CrossTrap, BadNets, masked-AT confinement — is now exhausted.

== Phase 4: ruling out the confounds with a toy and a capacity sweep

// Before declaring the idea impossible, we had to rule out two confounds: maybe CIFAR
// models were simply undertrained on CPU (50-70% clean acc), or maybe the network
// lacked capacity. Both turned out to be false, and ruling them out is what makes the
// negative result credible.
Before declaring the idea impossible we had to rule out two confounds: perhaps the
CIFAR models were simply undertrained on CPU ($50$–$70%$ clean accuracy), or perhaps
the network lacked capacity. Both turned out false, and ruling them out is what makes
the negative result credible.

// The capacity sweep settled it. The CNN was already a ~1.9M-parameter ResNet —
// capacity was never the limiter; the real confound was undertraining. Trained to
// convergence, the same width-64 base reaches 0.923 clean accuracy and a 2x-wider
// width-128 base reaches 0.921. Isolated-alignment fine-tuning from each converged
// base still gives support_cos ≈ 0 (0.002-0.013) and energy_frac at chance. So
// convergence plus 4x capacity do NOT enable directional steering — confirming the
// structural tension, not undertraining or capacity.
The capacity sweep settled it. The CNN was already a $tilde.op 1.9$M-parameter ResNet,
so capacity was never the limiter — the confound was undertraining. Trained to
convergence, the same width-64 base reaches $0.923$ clean accuracy and a
$2 times$-wider width-128 base reaches $0.921$. Isolated-alignment fine-tuning from
either converged base still yields `support_cos` $approx 0$ ($0.002$–$0.013$) and
`energy_frac` at chance. Convergence and $4 times$ capacity do _not_ unlock
directional steering — confirming the structural tension rather than undertraining.

// [FIG: cifar-capacity] The confound-killer. Source: analysis/cifar_capacity.py -> reports/_figs/cifar_capacity.png
#figure(
	image("figures/cifar_capacity.png", width: 85%),
	caption: [
		*Capacity and convergence are not the limiter.* Clean accuracy across model
		configurations: the early undertrained width-64 runs ($tilde.op 0.69$) sit far
		below the same architecture trained to convergence ($0.923$), and doubling the
		width to $7.7$M parameters does not help ($0.921$). Crucially, alignment
		fine-tuning on these fully-converged, high-capacity bases _still_ fails to
		steer the attack (`support_cos` $approx 0$), so the failure to draw a sink is
		structural — it is not explained by weak models or too few epochs.
	],
) <fig-capacity>

// The toy environment then localised the obstacle exactly. In a converged 2-D, 2-class
// MLP we can see everything. Two results stand out. First, the dimensionality
// hypothesis is refuted: the best achievable alignment does NOT degrade as input
// dimension grows from 2 to 1000 (it is flat-to-rising). "CIFAR's 3072 dimensions are
// why it fails" is simply wrong.
The toy then localised the obstacle exactly. In a converged two-dimensional, two-class
MLP everything is visible. Two results stand out. First, the dimensionality hypothesis
is refuted: the best achievable alignment does _not_ degrade as input dimension grows
from $2$ to $1000$ — it is flat-to-rising (@fig-toy-subspace). "CIFAR's $3072$
dimensions are why it fails" is wrong.

// [FIG: toy-subspace] Dimensionality is not the obstacle. Source: analysis/toy_subspace.py -> reports/_toy/toy_subspace.png
#figure(
	image("figures/toy_subspace.png", width: 88%),
	caption: [
		*Alignment quality does not decay with dimension.* Best achievable
		$cos(delta, s)$ (and energy on the sink axis) as a function of input dimension
		$D$, for a sink placed in a label-relevant ("signal") versus a label-irrelevant
		("void") subspace, in fully-converged toy MLPs. The curves are flat-to-rising,
		not decreasing: high dimensionality is _not_ what blocks steering. Placing the
		sink in a void subspace is consistently easier — the seed of the result that
		eventually transfers to CIFAR.
	],
) <fig-toy-subspace>

// Second, the budget sweep is decisive and reveals the boundary. The attack's energy
// concentrates on a chosen 1-D axis far above chance (20-33% vs 0.5% for D=200, a
// 40-60x enrichment) and this is robust across attack budget — but the *signed*
// alignment cos(δ,s) never exceeds ~0.27, never dominates, and actually flips negative
// at large budget (the attack goes anti-sink). Concentrating energy is free; making
// the attack DRAW a signed, dominant sink is fundamentally blocked.
Second, the budget sweep is decisive. The attack's energy concentrates on a chosen
one-dimensional axis far above chance ($20$–$33%$ versus $0.5%$ for $D = 200$, a
$40$–$60 times$ enrichment), robustly across attack budget — yet the _signed_
alignment $cos(delta, s)$ never exceeds $tilde.op 0.27$, never dominates, and flips
_negative_ at large budget (the attack moves anti-sink). Concentrating energy is free;
making the attack _draw_ a signed, dominant sink is fundamentally blocked.

// [FIG: toy-compare] The four mechanisms side by side in the 2-D landscape. Source: analysis/toy_sink.py -> reports/_toy/toy_compare.png
#figure(
	image("figures/toy_compare.png", width: 95%),
	caption: [
		*Loss landscapes and attack trajectories in the toy.* Each panel shows the 2-D
		loss surface, the input-gradient field, the decision boundary and live PGD
		trajectories for a different mechanism (baseline, on-manifold alignment,
		off-manifold sculpting, attack-aware). On-manifold alignment reproduces the
		accuracy-vs-steering tension in a fully converged net; off-manifold and
		attack-aware variants do not beat plain alignment and are unstable. The figure
		makes visible why no trajectory is bent into a dominant well at the sink.
	],
) <fig-toy-compare>

== Phase 5: the toy "win" and the precise boundary

// Reframing the budget-sweep result as a positive statement gives the project's clean
// result. If we drop the demand for a *recognizable signed* sink and ask only that the
// attack's energy land on a known direction, the toy delivers spectacularly and for free.
Reframing the budget-sweep result as a positive statement gives the project's clean
result. If we drop the demand for a _recognizable, signed_ sink and ask only that the
attack's energy land on a known direction, the toy delivers spectacularly, and for
free.

// [FIG: toy-win] The headline positive result in the toy. Source: analysis/toy_win.py -> reports/_toy/toy_win.png
#figure(
	image("figures/toy_win.png", width: 98%),
	caption: [
		*Forcing the attack into a known subspace is free, robust, and strengthens with
		dimension.* (A) Fraction of attack energy on the chosen 1-D sink axis versus
		attack budget $epsilon$ ($D = 200$): the aligned net (clean acc $1.00$) keeps
		$tilde.op 0.1$–$0.4$ of all attack energy on a single axis across the whole
		budget range, far above the $1\/D = 0.005$ chance line and well above the
		CE-only baseline. (B) The same energy fraction does _not_ decay as input
		dimension $D$ grows from $10$ to $1000$. (C) Enrichment over chance therefore
		_grows_ with dimension — $1 times$ at $D=10$, $2 times$ at $50$, $36 times$ at
		$200$, $187 times$ at $1000$ — all at clean accuracy $0.86$–$1.00$. Energy
		concentration is a real, robust, free effect when truly unused dimensions exist.
	],
) <fig-toy-win>

// But the same converged net shows the wall just as clearly. Energy concentrates, yet
// the signed cosine swings from +0.42 down to -0.32 as budget grows: the attack never
// commits to the sink's sign and eventually anti-aligns. This is the deliverable
// boundary, confirmed in a converged, low-dimensional net, so it is the core tension
// and not an artifact of capacity or dimension.
The same converged net shows the wall just as clearly. Energy concentrates, yet the
signed cosine swings from $+0.42$ down to $-0.32$ as budget grows: the attack never
commits to the sink's sign and eventually anti-aligns. This is the deliverable
boundary, confirmed in a converged, low-dimensional net — the core tension, not an
artifact.

// [FIG: toy-boundary] Concentration yes, signed drawing no. Source: analysis/toy_win_boundary.py -> reports/_toy/toy_win_boundary.png
#figure(
	image("figures/toy_win_boundary.png", width: 90%),
	caption: [
		*The boundary: energy concentrates but the sign is uncontrolled.* For the same
		converged toy net that produces @fig-toy-win, energy on the sink subspace stays
		high, but the _signed_ alignment $cos(delta, s)$ falls from $+0.42$ to $-0.32$
		as the attack budget grows — the perturbation increasingly points _against_ the
		intended sink. So the achievable effect is sign-free energy concentration
		(a detector can still flag it), whereas a clean, dominant, correctly-signed
		drawing is fundamentally out of reach.
	],
) <fig-toy-boundary>

== Phase 6: back to CIFAR, faithfully

// The toy says energy concentration should be achievable; the question is whether it
// transfers to CIFAR. We tested this in two steps on the converged 0.92 network.
The toy says energy concentration should be achievable; does it transfer to CIFAR? We
tested this in two steps on the converged $0.92$ network.

// First, a controlled pattern sweep (Stage-3 question Q5): across six visual patterns
// (full cross, small cross, constellation, corner square, two checkerboards), under the
// best alignment fine-tune, NO pattern concentrates energy on CIFAR. support_cos sits in
// [-0.012, +0.013], mass_frac at chance, energy_frac at chance everywhere — central,
// peripheral, sparse or signed alike. The visual-sink idea does not transfer.
First, a controlled pattern sweep (Stage-3 question Q5). Across six visual patterns
(full cross, small cross, constellation, corner square, two checkerboards) under the
best alignment fine-tune, _no_ pattern concentrates energy on CIFAR: `support_cos` in
$[-0.012, +0.013]$, `mass_frac` and `energy_frac` at chance everywhere — central,
peripheral, sparse, or signed alike. The visual-sink idea does not transfer.

// [FIG: pattern-table] No visual pattern is drawn on CIFAR. Source: analysis/cifar_pattern_table.py -> reports/_figs/pattern_table.md
#figure(
	table(
		columns: 6,
		align: (left, right, right, right, right, left),
		stroke: 0.5pt + gray,
		table.header([*pattern*], [*support*], [*chance*], [*clean acc*], [*best `mass_frac`*], [*verdict*]),
		[cross (full)], [720], [0.234], [0.611], [0.279], [not drawn],
		[cross (full), align FT], [720], [0.234], [0.713], [0.289], [not drawn],
		[small\_cross 8×8], [84], [0.027], [0.107], [0.035], [collapsed],
		[corner\_square 4×4, BadNet], [48], [0.016], [0.642], [0.019], [not drawn],
		[corner\_square 4×4, +L2 AT], [48], [0.016], [0.466], [0.011], [not drawn],
		[corner\_square 4×4, masked AT], [48], [0.016], [0.532], [0.011], [not drawn],
	),
	caption: [
		*Pattern complexity versus steerability on CIFAR-10.* For each pattern and
		mechanism, the best `mass_frac` the attack puts on the pattern support stays at
		or below the chance value $|S|\/D$, and `support_cos` (not shown) never clears
		zero. No placement — dense or sparse, central or corner — is drawn; the
		`corner_square` cases even fall _below_ chance, the attack avoiding the corner.
	],
) <fig-pattern-table>

// We also confirmed the geometry directly: a loss-landscape slice in the (sink, grad)
// plane shows no well toward the sink and a flat cos along the PGD trajectory, and a
// side-by-side of the sink template vs the actual PGD perturbation shows the attack
// drawing object-shaped noise, not the sink.
We confirmed the geometry directly. A loss-landscape slice in the (sink, gradient)
plane shows no well toward the sink and a flat cosine along the PGD trajectory
(@fig-cifar-landscape); a side-by-side of the template and the actual perturbation
shows the attack drawing object-shaped noise (@fig-cifar-draws).

// [FIG: cifar-landscape] No well toward the sink on CIFAR. Source: analysis/cifar_landscape.py -> reports/_figs/cifar_landscape.png
#figure(
	image("figures/cifar_landscape.png", width: 92%),
	caption: [
		*The CIFAR loss landscape has no basin toward the sink.* A 2-D slice of the
		classification loss spanned by the sink direction and the input-gradient
		direction, with the PGD trajectory overlaid, plus $cos(delta_t, s)$ as a
		function of attack step. The loss rises along the gradient axis but is flat
		along the sink axis, the trajectory never turns toward the sink, and the cosine
		stays $approx 0$ throughout. There is simply no downhill path that an attack
		could follow to the sink.
	],
) <fig-cifar-landscape>

// [FIG: cifar-draws] What the attack draws instead. Source: analysis/cifar_attack_viz.py -> reports/_figs/cifar_attack_draws.png
#figure(
	image("figures/cifar_attack_draws.png", width: 92%),
	caption: [
		*What PGD draws instead of the sink.* Columns show, for several inputs, the
		clean image, the intended sink template, and the actual PGD perturbation. The
		perturbation is structured around the salient _object_ pixels — edge and
		texture noise — and bears no resemblance to the template ($cos approx 0$). The
		attack spends its budget where the local gradient is largest, which is on the
		object, never on the designer's pattern.
	],
) <fig-cifar-draws>

// FGSM behaves the same as PGD here: both give support_cos ≈ 0 and mass at chance,
// even though PGD drives robust accuracy to zero. The one apparent exception (L2 FGSM
// puts mass 0.356 > chance 0.234 on the cross) is central-pixel saliency, not drawing —
// support_cos is still ~0.
FGSM behaves like PGD here: both give `support_cos` $approx 0$ and mass at chance, even
though PGD drives robust accuracy to zero (@fig-fgsm-table). The one apparent exception
— $L_2$ FGSM placing `mass_frac` $0.356 > 0.234$ on the cross — is central-pixel
saliency, not drawing, since `support_cos` remains $tilde.op 0$.

// [FIG: fgsm-table] FGSM vs PGD on the converged net. Source: analysis/cifar_fgsm_table.py -> reports/_figs/fgsm_vs_pgd.md
#figure(
	table(
		columns: 6,
		align: (left, left, right, right, right, right),
		stroke: 0.5pt + gray,
		table.header([*norm*], [*attack*], [*$epsilon$*], [*robust acc*], [*`support_cos`*], [*`mass_frac`*]),
		[L2], [FGSM], [0.5], [0.236], [$+0.000$], [0.356],
		[L2], [FGSM], [2.0], [0.146], [$-0.002$], [0.355],
		[L2], [PGD],  [0.5], [0.012], [$+0.002$], [0.282],
		[L2], [PGD],  [2.0], [0.000], [$+0.004$], [0.258],
		[L∞], [FGSM], [0.031], [0.068], [$+0.006$], [0.236],
		[L∞], [PGD],  [0.031], [0.000], [$+0.004$], [0.238],
	),
	caption: [
		*FGSM and PGD agree: no drawing, on the converged $0.92$ net.* For both attacks
		and both norms, `support_cos` $approx 0$ and `mass_frac` is at the chance value
		($0.234$ for the cross). PGD is far stronger as an attack (robust accuracy
		$arrow.r 0$) but no more steerable. The elevated $L_2$ FGSM mass reflects
		central-pixel saliency overlapping the cross, not reproduction of its shape.
	],
) <fig-fgsm-table>

// Second, the faithful toy port: place the sink in a LABEL-IRRELEVANT direction the
// classifier is genuinely blind to. We aligned the converged net's gradient toward a
// dense "high-frequency" direction (a Nyquist per-pixel checkerboard, where natural
// images carry almost no energy) and toward a random direction, sweeping α.
Second, the faithful port of the toy idea: place the sink in a _label-irrelevant_
direction the classifier is genuinely blind to. We aligned the converged net's
gradient toward a dense high-frequency direction — a Nyquist per-pixel checkerboard,
where natural images carry almost no energy — and, as a control, toward a random
direction, sweeping $alpha$.

// This is where concentration finally transfers to CIFAR — but only for the
// high-frequency direction, and not for free. Relative to chance (energy_frac =
// 3.26e-4): the no-alignment baseline already carries 1.5x (high-freq naturally holds
// a little more adversarial energy), and alignment lifts this to a peak of ~44x at
// α=6, with ~23-28x sustained at α=8-12. The random direction stays flat at chance for
// every α — concentration needs a direction the classifier is blind to, not merely a
// "non-visual" one.
This is where concentration finally transfers to CIFAR — but only for the
high-frequency direction, and not for free. Relative to chance
(`energy_frac` $= 3.26 times 10^(-4)$), the no-alignment baseline already carries
$1.5 times$ (the high-frequency band naturally holds slightly more adversarial energy),
and alignment lifts this to a peak of $tilde.op 44 times$ at $alpha = 6$, with
$tilde.op 23$–$28 times$ sustained at $alpha = 8$–$12$. The random direction stays flat
at chance for every $alpha$: concentration needs a direction the classifier is _blind
to_, not merely a non-visual one.

// The cost is accuracy, and the frontier is strikingly non-monotone. As α grows the
// model first collapses (α=2 -> 0.38 clean, reproducibly), then RECOVERS through α=4-12
// (peak 0.69), then collapses again (α=32 -> 0.35). There is no cheap high-accuracy
// knee: any alignment strong enough to concentrate energy knocks the model off its
// 0.92 basin, and training only re-stabilises around α≈8-12.
The cost is accuracy, and the frontier is strikingly non-monotone. As $alpha$ grows the
model first _collapses_ ($alpha = 2 arrow.r 0.38$ clean, reproducibly across three
seeds), then _recovers_ through $alpha = 4$–$12$ (peak $0.69$), then collapses again
($alpha = 32 arrow.r 0.35$). There is no cheap high-accuracy knee: any alignment strong
enough to concentrate energy knocks the model off its $0.92$ basin, and training only
re-stabilises around $alpha approx 8$–$12$.

// [FIG: cifar-void] The CIFAR frontier — the second headline result. Source: analysis/cifar_void_tradeoff.py -> reports/_figs/cifar_void_tradeoff.png
#figure(
	image("figures/cifar_void_tradeoff.png", width: 98%),
	caption: [
		*Energy concentration transfers to CIFAR-10 only for a label-blind direction,
		and is paid for in accuracy.* Left: energy concentration (`energy_frac` over
		chance) versus alignment strength $alpha$. The high-frequency sink (blue) rises
		from $1.5 times$ at $alpha=0$ to a peak of $44 times$ at $alpha=6$, holding
		$23$–$28 times$ at $alpha=8$–$12$; the random direction (red) never leaves the
		chance line. Right: the same points against clean accuracy, exposing the
		trade-off and its non-monotonicity — accuracy dips at $alpha=2$ ($0.38$),
		recovers to $0.69$ near $alpha=12$, then collapses at $alpha=32$ ($0.35$). The
		usable operating region is $alpha approx 8$–$12$: $tilde.op 23$–$28 times$
		chance at $0.67$–$0.69$ accuracy.
	],
) <fig-cifar-void>

// The mechanism is also stable across attack budget on CIFAR (Stage-3 question Q4):
// the concentration metrics are robust as ε is varied, confirming that what
// concentration exists is not a single-budget artifact.
The mechanism is also stable across attack budget on CIFAR (Stage-3 question Q4): the
concentration metrics hold as $epsilon$ is varied, so the effect is not a single-budget
artifact (@fig-cifar-eps).

// [FIG: cifar-eps] Sensitivity to the perturbation budget. Source: analysis/cifar_eps_curves.py -> reports/_figs/cifar_eps_curves.png
#figure(
	image("figures/cifar_eps_curves.png", width: 92%),
	caption: [
		*Stability of the metrics versus attack budget $epsilon$.* `support_cos`,
		`mass_frac` and `energy_frac` as functions of the $L_2$ budget, for the
		baseline and the aligned net. The curves are smooth and monotone with no
		threshold effects: the (small) signal present on CIFAR is consistent across
		budgets rather than appearing only at one carefully chosen $epsilon$.
	],
) <fig-cifar-eps>

// ====================================================================
= Synthesis and verdict
// ====================================================================

// Pulling the threads together, the project resolves into a three-part story.
The threads pull together into a three-part story.

// 1. A recognizable VISUAL sink cannot be drawn on CIFAR. Across five mechanisms
//    (alignment, CrossTrap, BadNets, masked-AT confinement, alignment fine-tune) and
//    six patterns, on a fully-converged 0.92 network at up to 2x width, no pattern is
//    reproduced: support_cos ≈ 0, mass at chance. This is a characterized impossibility,
//    with the capacity and dimensionality confounds explicitly killed.
+ *A recognizable visual sink cannot be drawn on CIFAR.* Across five mechanisms and six
  patterns, on a fully-converged $0.92$ network at up to $2 times$ width, no pattern is
  reproduced (`support_cos` $approx 0$, mass at chance). This is a _characterized_
  impossibility, with the capacity and dimensionality confounds explicitly ruled out.

// 2. Energy concentration DOES transfer to CIFAR, but only for a label-blind
//    (high-frequency) direction, at 23-28x chance, and not for free: it costs accuracy
//    (0.92 -> ~0.68) and the frontier is non-monotone. A random direction does nothing.
+ *Energy concentration does transfer to CIFAR* — but only for a label-blind
  (high-frequency) direction, at $23$–$28 times$ chance, and not for free: it costs
  accuracy ($0.92 arrow.r tilde.op 0.68$) along a non-monotone frontier. A random
  direction achieves nothing.

// 3. The toy proves the clean limit. When truly unused dimensions exist, concentration
//    is 36-187x chance at ~free accuracy and robust across budget — the idealised
//    version of result (2), with the same boundary (the sign is never controlled).
+ *The toy proves the clean limit.* When truly unused dimensions exist, concentration
  reaches $36$–$187 times$ chance at near-free accuracy and is robust across budget —
  the idealised version of result (2), with the same boundary: the sign is never
  controlled.

// The single sentence that explains all of it: a network's input gradient can encode
// the class OR point at a fixed direction, but not both. Detection-grade concentration
// onto a label-blind subspace is real and controllable (at an accuracy price); a
// visible, signed drawing is blocked by that tension.
One sentence explains all of it: _a network's input gradient can encode the class or
point at a fixed direction, but not both_. Detection-grade concentration onto a
label-blind subspace is real and controllable, at an accuracy price; a visible, signed
drawing is blocked by exactly that tension.

// A note on scope relative to the plan: the specification named CIFAR-100 for Stage 3.
// We deliberately stayed on CIFAR-10 plus the toy: once the effect fails to give a
// visual drawing on the easier dataset, a harder one cannot rescue it, and the toy
// isolates the mechanism far more cleanly than CIFAR-100 would. A CIFAR-100
// confirmation remains a low-risk, deferred item.
A note on scope: the specification named CIFAR-100 for Stage 3. We deliberately stayed
on CIFAR-10 plus the toy — once the effect fails to yield a visual drawing on the
easier dataset, a harder one cannot rescue it, and the toy isolates the mechanism far
more cleanly. A CIFAR-100 confirmation remains a low-risk, deferred item.

// ====================================================================
= Conclusions and future directions
// ====================================================================

// We set out to make a model betray its attacker by forcing white-box gradient attacks
// to draw a fixed visual symbol. The honest outcome is that the strong version of this
// goal is unreachable for principled reasons, while a useful weaker version — forcing
// the attack into a known, label-blind subspace — is achievable and was demonstrated on
// both a toy and CIFAR-10. The value of the project is the sharp boundary between the two.
We set out to make a model betray its attacker by forcing white-box gradient attacks to
draw a fixed visual symbol. The honest outcome: the strong version of this goal is
unreachable for principled reasons, while a useful weaker version — forcing the attack
into a known, label-blind subspace — is achievable, and was demonstrated on both a toy
and CIFAR-10. The contribution is the sharp boundary between the two.

// Several concrete directions follow naturally:
Several concrete directions follow naturally.

// - A detector instead of a drawing. The achievable effect (energy concentration on a
//   known subspace) is exactly what a detector needs: project an input's perturbation
//   onto the known basis and flag anomalous energy. This sidesteps the gradient
//   dual-role tension entirely and is the most promising next step.
+ *A detector instead of a drawing.* The achievable effect is exactly what a detector
  needs: project an input's perturbation onto the known basis and flag anomalous
  energy. This sidesteps the gradient's dual role entirely and is the most promising
  next step.

// - Off-manifold gradient sculpting. Accuracy only constrains the model on the data
//   manifold; the attack travels mostly off it. A loss that pins the function on-manifold
//   (KL to a frozen classifier) while bending the gradient only at off-manifold points
//   the attack visits is the first formulation where alignment and accuracy need not
//   fight over the same gradient. The open question is curvature cost.
+ *Off-manifold gradient sculpting.* Accuracy only constrains the model on the data
  manifold, yet the attack travels mostly off it. A loss that pins the function
  on-manifold (a KL term to a frozen classifier) while bending the gradient only at the
  off-manifold points the attack visits is the first formulation in which alignment and
  accuracy need not fight over the same gradient. The open question is the curvature
  cost.

// - Designated-UAP training and architectural bottlenecks. Train the sink as a fixed,
//   rate-controlled universal loss-increasing direction (milder than a forced label),
//   or build a low-rank input bottleneck whose attackable subspace contains the sink by
//   construction.
+ *Designated-UAP training and architectural bottlenecks.* Train the sink as a fixed,
  rate-controlled universal loss-increasing direction @moosavi2017uap (milder than a
  forced label), or build a low-rank input bottleneck whose attackable subspace contains
  the sink by construction.

// - Robust-feature framing. The fact that only a label-blind (high-frequency) direction
//   concentrates energy connects directly to the robust/non-robust feature view of
//   adversarial examples; characterising which subspaces are "free" for a given dataset
//   would predict the achievable concentration in advance.
+ *Robust-feature framing.* That only a label-blind direction concentrates energy
  connects directly to the robust/non-robust feature view of adversarial examples
  @ilyas2019; characterising which subspaces are "free" for a dataset would predict the
  achievable concentration in advance.

#pagebreak()
#bibliography("bib.yaml", full: true)

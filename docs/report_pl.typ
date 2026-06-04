// =====================================================================
//  ADVERSARIAL SINKS — RAPORT KOŃCOWY (wersja polska)
//
//  To jest wersja przeznaczona do oddania. Nad każdym akapitem polskim
//  znajduje się jego angielski odpowiednik w komentarzu (// ...), żeby
//  ułatwić pracę nad treścią. Wersja angielska (report_en.typ) jest
//  zwięzłym przeglądem.
//
//  Rysunki są trzymane LOKALNIE w docs/figures/ (katalog jest samowystarczalny).
//  To kopie wyników skryptów z analysis/. Każdy #figure poprzedza komentarz
//  "// [FIG: handle]" z nazwą skryptu źródłowego — używaj tego uchwytu, gdy chcesz
//  mnie o dany rysunek prosić lub odświeżyć go z analysis/.
//
//  Budowanie (z katalogu docs/):
//      typst compile report_pl.typ
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
#set text(lang: "pl")
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
				ZZSN, Lato 2026
			],
			[],
			[#counter(page).display("1/1", both: true)],
		)
	],
)

// ---------------------------------------------------------------- strona tytułowa
#v(15%)
#show title: set text(size: 30pt, weight: "semibold")
#title()
#text(size: 16pt)[Sterowanie zbieżnością ataków adwersarialnych poprzez techniki
obronne i wprowadzanie wzorców typu backdoor]

#v(1em)
#authors.join([ \ ])
#v(2em)
_Dokumentacja końcowa — ZZSN, Lato 2026 (Projekt nr 8)_
#v(15%)

#outline()
#pagebreak()

// ====================================================================
= Wprowadzenie i motywacja
// ====================================================================

// Adversarial examples are small, deliberately crafted perturbations that flip a
// network's prediction while remaining almost invisible to a human. A white-box
// attacker who can read the model's gradient can reliably push any input across a
// decision boundary by following the direction in which the classification loss grows
// fastest.
Przykłady adwersarialne to niewielkie, celowo spreparowane perturbacje, które zmieniają
predykcję sieci, pozostając przy tym niemal niewidoczne dla człowieka @szegedy2014.
Atakujący w scenariuszu white-box, mający dostęp do gradientu modelu, jest w stanie
niezawodnie przepchnąć dowolne wejście przez granicę decyzyjną, podążając za kierunkiem,
w którym strata klasyfikacji rośnie najszybciej @goodfellow2015.

// The genesis of this project was a simple, slightly subversive question. Instead of
// making a model robust — the usual goal of adversarial training — can we make a model
// betray the attacker? Concretely: can we shape the loss landscape so that the
// perturbation an attack discovers is not the usual quasi-noise, but a fixed,
// designer-chosen visual pattern — an adversarial sink (for example an "X")? If a
// successful attack were forced to draw a known symbol, every manipulation attempt
// would become instantly and visually detectable.
Geneza projektu to proste, nieco przewrotne pytanie. Zamiast uodparniać model — co jest
zwykłym celem treningu adwersarialnego @madry2018 — czy możemy sprawić, by model
_zdradził atakującego_? Konkretnie: czy da się ukształtować krajobraz strat tak, aby
perturbacja znaleziona przez atak nie była typowym quasi-szumem, lecz ustalonym,
zaprojektowanym z góry wzorcem wizualnym — _adversarial sink_ (np. symbolem „X”)? Gdyby
udany atak był _zmuszony_ narysować znany symbol, każda próba manipulacji stałaby się
natychmiast i wizualnie wykrywalna.

// The appeal is that this turns the attacker's own strength against them: the very
// gradient-following that makes white-box attacks effective would be what funnels them
// into the trap. Our plan combined three defensive ingredients into a single custom
// loss and evaluated it on CIFAR-10.
Urok tego pomysłu polega na obróceniu siły atakującego przeciwko niemu: to właśnie
podążanie za gradientem, które czyni ataki white-box skutecznymi, kierowałoby je prosto
w pułapkę. Nasz plan łączył trzy obronne składowe w jedną niestandardową funkcję straty,
ocenianą na zbiorze CIFAR-10.

// This report is deliberately chronological. The headline result is partly negative,
// and the reasoning that led there — the sequence of mechanisms we tried, why each
// failed, and what each failure taught us — is the real contribution. We close with a
// precise characterization of what is and is not achievable, and concrete future work.
Niniejszy raport jest celowo chronologiczny. Główny wynik jest częściowo negatywny, a
prawdziwym wkładem jest _tok rozumowania, który do niego doprowadził_ — sekwencja
wypróbowanych mechanizmów, przyczyny porażki każdego z nich oraz płynące z nich wnioski.
Kończymy precyzyjną charakterystyką tego, co jest, a co nie jest osiągalne, oraz
konkretnymi kierunkami dalszych prac.

// ====================================================================
= Tło i sformułowanie problemu
// ====================================================================

== Model zagrożenia i ataki

// We work in the standard white-box setting. A classifier f_θ maps an image x in [0,1]^D
// (here D = 3·32·32 = 3072) to class logits. An attack searches for a perturbation δ,
// constrained to a budget ||δ|| ≤ ε, that maximizes the classification loss. We use the
// two canonical first-order attacks, both through Foolbox: FGSM, a single
// gradient-sign step, and PGD, its iterated and projected version.
Pracujemy w standardowym scenariuszu white-box. Klasyfikator $f_theta$ odwzorowuje obraz
$x in [0,1]^D$ (tutaj $D = 3 dot 32 dot 32 = 3072$) na logity klas. Atak poszukuje
perturbacji $delta$, ograniczonej budżetem $norm(delta) <= epsilon$, która maksymalizuje
stratę klasyfikacji. Używamy dwóch kanonicznych ataków pierwszego rzędu, oba przez
bibliotekę Foolbox @rauber2017foolbox: FGSM — pojedynczego kroku w kierunku znaku
gradientu @goodfellow2015 — oraz PGD, jego iterowanej i rzutowanej wersji @madry2018.

// The PGD iteration (the L-infinity form) is:
Iteracja PGD (w wariancie $L_infinity$) ma postać:

$ delta_(t+1) = "clip"_epsilon (delta_t + alpha dot "sign"(nabla_delta cal(L)_"CE"(f_theta (x + delta_t), y))) $

// A crucial early decision: a sparse, high-contrast sink (an "X" on a few pixels) can
// only be reproduced by an L2 attack. An L-infinity attack saturates every pixel to ±ε,
// so it can never paint a sparse shape. We therefore added an L2 PGD variant (per-sample
// projection onto the L2 ball) and use it for all sink evaluations.
Istotna decyzja podjęta na wczesnym etapie: rzadki, wysokokontrastowy sink („X” na kilku
pikselach) może zostać odtworzony wyłącznie przez atak $L_2$. Atak $L_infinity$ wysyca
_każdy_ piksel do $plus.minus epsilon$, więc nigdy nie namaluje rzadkiego kształtu.
Dodaliśmy zatem wariant PGD w normie $L_2$ (rzutowanie każdej próbki na kulę $L_2$) i
używamy go we wszystkich ewaluacjach sinka.

== Proponowana funkcja straty

// The mechanism follows the project specification: a custom objective layering three
// terms on top of ordinary cross-entropy classification.
Mechanizm jest zgodny ze specyfikacją projektu: niestandardowa funkcja celu nakładająca
trzy składniki na zwykłą klasyfikację entropią krzyżową.

// Gradient alignment. To bend the input gradient toward the sink X, we penalise the
// angle between them. With cosine similarity the term is 0 when the gradient already
// points at the sink and grows toward 2 when it points away:
*Dopasowanie gradientu (gradient alignment).* Aby nagiąć gradient względem wejścia w
stronę sinka $X$, karzemy kąt między nimi. Przy podobieństwie kosinusowym składnik wynosi
$0$, gdy gradient już wskazuje na sink, i rośnie ku $2$, gdy wskazuje przeciwnie:

$ L_"align" = 1 - (nabla_x cal(L)_"CE" (f_theta (x), y) dot X) / (norm(nabla_x cal(L)_"CE" (f_theta (x), y))_2 dot norm(X)_2) $ <eq-align>

// Sink preservation. We want the model to keep misclassifying when the sink is stamped
// onto the image, so the sink remains a reliable "hole" in the defences. This is a
// negative term that keeps CE(f(x+X), y) high:
*Utrzymanie sinka (sink preservation).* Chcemy, aby model wciąż błędnie klasyfikował,
gdy sink jest nałożony na obraz, tak by pozostawał on niezawodną „dziurą” w
zabezpieczeniach. To składnik ujemny, utrzymujący $cal(L)_"CE" (f_theta (x + X), y)$ na
wysokim poziomie:

$ L_"sink" = - cal(L)_"CE" (f_theta (x + X), y) $ <eq-sink>

// Orthogonal adversarial training. Standard Madry-style adversarial training would
// harden the model in all directions, including the sink, fighting term (2). We instead
// project the PGD perturbation onto the subspace orthogonal to X, so robustness is
// trained in every direction except the sink:
*Trening ortogonalny (orthogonal adversarial training).* Klasyczny trening adwersarialny
w stylu Mądrego @madry2018 uodparnia model we _wszystkich_ kierunkach, w tym w kierunku
sinka, co jest sprzeczne ze składnikiem (2). Zamiast tego rzutujemy perturbację PGD na
podprzestrzeń ortogonalną do $X$, więc odporność trenowana jest w każdym kierunku _poza_
sinkiem:

$ L_"robust" = cal(L)_"CE" (f_theta (x + delta^perp), y), quad delta^perp = delta_"PGD" - "proj"_X (delta_"PGD") $ <eq-robust>

// The full objective combines these with three balancing hyperparameters α, λ_s, λ_r:
Pełna funkcja celu łączy te składniki za pomocą trzech hiperparametrów równoważących
$alpha, lambda_s, lambda_r$:

$ L_"total" = cal(L)_"CE" (f_theta (x), y) + alpha L_"align" - lambda_s cal(L)_"CE" (f_theta (x + X), y) + lambda_r cal(L)_"CE" (f_theta (x + delta^perp), y) $ <eq-total>

== Co oznacza „sukces”: metryki detekcji

// "Detectable" is not the same as "visible to a human". We do not need an attack to
// render a crisp X; we need its perturbation δ to land measurably on the known pattern,
// far more than chance. For a sink s with support S (its nonzero pixels) we track three
// complementary quantities:
„Wykrywalny” to nie to samo co „widoczny dla człowieka”. Nie potrzebujemy, by atak
wyrysował wyraźny „X”; potrzebujemy, by jego perturbacja $delta$ trafiała w znany wzorzec
w mierzalnym stopniu, znacznie powyżej poziomu losowego. Dla sinka $s$ o nośniku $S$
(jego niezerowych pikselach) śledzimy trzy uzupełniające się wielkości:

// - support_cos: cosine between δ and the signed template: does δ reproduce the exact
//   shape and sign? Chance ≈ 0.
// - mass_frac: fraction of δ's absolute (L1) mass on the support S. Chance = |S|/D, the
//   mass a uniform random δ puts there.
// - energy_frac: fraction of δ's squared (L2) energy along the sink direction, i.e.
//   cos²(δ, s). Chance = 1/D for a one-dimensional direction. This is the decisive
//   metric for dense sinks, where the other two are uninformative.
- *`support_cos`* — kosinus między $delta$ a _znakowanym_ szablonem: czy $delta$
  odtwarza dokładny kształt i znak? Poziom losowy $approx 0$.
- *`mass_frac`* — udział masy bezwzględnej ($L_1$) perturbacji $delta$ przypadający na
  nośnik $S$. Poziom losowy $= |S| \/ D$, czyli masa, jaką nakłada tam jednorodnie losowe
  $delta$.
- *`energy_frac`* — udział energii kwadratowej ($L_2$) perturbacji $delta$ wzdłuż
  kierunku sinka, czyli $cos^2(delta, s)$. Poziom losowy $= 1\/D$ dla kierunku
  jednowymiarowego. To metryka rozstrzygająca dla _gęstych_ sinków, gdzie dwie pozostałe
  są nieinformacyjne.

// A pattern is "drawn" iff support_cos is clearly positive and mass_frac exceeds chance,
// at a clean accuracy worth keeping. "Energy concentration" is the weaker,
// detection-grade claim: energy_frac >> chance, even if the exact sign and shape are not
// reproduced.
Wzorzec uznajemy za _narysowany_ wtedy i tylko wtedy, gdy `support_cos` jest wyraźnie
dodatni i `mass_frac` przekracza poziom losowy, przy dokładności na czystych przykładach
wartej zachowania. _Koncentracja energii_ to słabsze stwierdzenie klasy detekcyjnej:
`energy_frac` $>>$ poziom losowy, nawet jeśli dokładny znak i kształt nie zostają
odtworzone.

// ====================================================================
= Baza kodu
// ====================================================================

// Because this is a project report and not only a study of results, we briefly describe
// the software we built. All of it is reusable and was exercised heavily across roughly
// twenty experiments.
Ponieważ jest to raport projektowy, a nie wyłącznie analiza wyników, krótko opisujemy
zbudowane przez nas oprogramowanie. Całość jest wielokrotnego użytku i była intensywnie
wykorzystywana w blisko dwudziestu eksperymentach.

// The core is an importable Python package, adversarial_sinks, built on PyTorch and
// PyTorch Lightning. Its centre is a single pipeline that takes a sink pattern and a
// loss function and runs an experiment end to end — train -> attack -> metrics -> report.
// Around it:
Rdzeniem jest importowalny pakiet Pythona `adversarial_sinks`, oparty na PyTorch i
PyTorch Lightning. Jego sercem jest pojedynczy _potok_ (pipeline), który przyjmuje wzorzec
sinka i funkcję straty oraz przeprowadza eksperyment od początku do końca — trening
$arrow.r$ atak $arrow.r$ metryki $arrow.r$ raport. Wokół niego:

// - losses.py — every mechanism we tried, each a swappable loss class
//   (AdversarialSinkLoss, CrossTrapLoss, BadNetPoisonLoss, SinkConfinementLoss); the
//   pipeline is loss-agnostic.
// - attacks.py — FGSM and PGD (L2 and Linf) via Foolbox, with budget-exact projection.
// - sink_patterns.py — the pattern library (full cross, small_cross, corner_square,
//   constellation, checkerboards) plus the dense "void" directions.
// - metrics.py — the three detection metrics and per-sample statistics.
// - a CNN with a width knob (base_channels) so capacity could be scaled, with input
//   normalization moved inside the network so every loss and attack works in the same
//   [0,1] pixel space.
- *`losses.py`* — każdy wypróbowany mechanizm jako wymienna klasa straty
  (`AdversarialSinkLoss`, `CrossTrapLoss`, `BadNetPoisonLoss`, `SinkConfinementLoss`);
  potok jest niezależny od wyboru straty.
- *`attacks.py`* — FGSM oraz PGD ($L_2$ i $L_infinity$) przez Foolbox, z rzutowaniem
  dokładnie respektującym budżet.
- *`sink_patterns.py`* — biblioteka wzorców (pełny krzyż, `small_cross`,
  `corner_square`, `constellation`, szachownice) oraz gęste kierunki „void”.
- *`metrics.py`* — trzy metryki detekcji i statystyki per-próbka.
- sieć CNN z pokrętłem szerokości (`base_channels`), pozwalającym skalować pojemność, z
  normalizacją wejścia przeniesioną _do wnętrza_ sieci, tak by każda strata i każdy atak
  działały w tej samej przestrzeni pikseli $[0,1]$.

// Two practical constraints shaped everything. First, all training was CPU-only (no
// CUDA), and the alignment term needs a second-order gradient, costing ~2.9 s per batch;
// experiments are therefore sized in hundreds of batches and made resumable through
// on-disk markers. Second, a separate, fully-converged two-dimensional toy environment
// lets us draw the entire loss landscape, gradient field and live attack trajectories —
// the highest information-per-second tool we had, and the one that ultimately untangled
// cause from confound.
Dwa praktyczne ograniczenia ukształtowały całość. Po pierwsze, cały trening odbywał się
wyłącznie na CPU (bez CUDA), a składnik dopasowania wymaga gradientu drugiego rzędu, co
kosztuje $tilde.op 2.9$ s na partię; eksperymenty są więc wymiarowane w setkach partii i
wznawialne dzięki znacznikom zapisywanym na dysku. Po drugie, osobne, w pełni zbieżne
dwuwymiarowe środowisko _toy_ pozwala narysować cały krajobraz strat, pole gradientu oraz
trajektorie ataku na żywo — było to narzędzie o najwyższej ilości informacji na sekundę i
to właśnie ono ostatecznie oddzieliło przyczynę od czynnika zakłócającego.

// A sanity check preceded all sink work: we verified that the attacks behave (PGD is
// monotone in ε, budget-exact, and far stronger than random noise; the model is robust
// to random noise), and that a textbook BadNets backdoor trains correctly in our setup.
Wszystkie prace nad sinkiem poprzedziła kontrola poprawności: sprawdziliśmy, że ataki
zachowują się prawidłowo (PGD jest monotoniczne względem $epsilon$, dokładnie respektuje
budżet i jest znacznie silniejsze niż losowy szum; model jest odporny na losowy szum) oraz
że podręcznikowy backdoor BadNets @gu2017badnets trenuje się poprawnie w naszym
środowisku (@fig-badnet).

// [FIG: badnet-demo] Sanity check that data poisoning works at all in our pipeline.
// Source: diagnostics/badnet_demo.py -> reports/_demos/badnet_demo.png
#figure(
	image("figures/badnet_demo.png", width: 80%),
	// EN caption: BadNets backdoor sanity check. A model trained with a standard BadNets
	// data-poisoning trigger learns the shortcut "trigger present -> target class".
	// Stamping the corner trigger drives the predicted probability of the target class
	// airplane to 0.855, versus 0.137 on the clean image, with clean accuracy preserved.
	// This confirms our setup can plant a backdoor; the question the rest of the report
	// answers is whether a gradient attack can be made to reproduce such a trigger.
	caption: [
		*Kontrola poprawności backdoora BadNets.* Model wytrenowany ze standardowym
		triggerem zatruwającym dane BadNets uczy się skrótu „obecny trigger $arrow.r$
		klasa docelowa”. Nałożenie triggera w rogu podnosi przewidywane
		prawdopodobieństwo klasy docelowej _samolot_ do $0.855$, wobec $0.137$ na czystym
		obrazie, przy zachowanej dokładności na czystych przykładach. Potwierdza to, że
		nasze środowisko potrafi osadzić backdoor; pytaniem, na które odpowiada reszta
		raportu, jest to, czy _atak_ gradientowy da się zmusić do samodzielnego
		odtworzenia takiego triggera.
	],
) <fig-badnet>

// ====================================================================
= Przebieg eksperymentów
// ====================================================================

// We present the work in the order it happened, because each pivot was forced by the
// previous failure. Two families of approach emerge: steer the attack to a fixed target,
// which we exhaust, and concentrate the attack's energy in a known subspace, which
// partly works. The boundary between them is the main finding.
Przedstawiamy pracę w kolejności, w jakiej miała miejsce, ponieważ każdy zwrot był
wymuszony przez poprzednią porażkę. Wyłaniają się dwie rodziny podejść: _sterowanie atakiem
ku ustalonemu celowi_, którą wyczerpujemy, oraz _koncentracja energii ataku w znanej
podprzestrzeni_, która częściowo działa. Granica między nimi jest głównym wynikiem.

== Faza 1: poprawienie mechanizmu i obserwacja, jak walczy sam ze sobą

// The first weeks went into making the proposed loss actually do what it claims. Four
// structural bugs had silently neutralised it: a normalization-space mismatch between the
// dataset and the clip(0,1) terms; a missing second-order flag that made the alignment
// term a no-op contributing zero gradient to the weights; a sign error in the sink term
// that trained robustness to the sink instead of vulnerability; and the unbounded
// negative term that diverges, which we tamed with a margin clamp.
Pierwsze tygodnie poświęciliśmy temu, by proponowana strata rzeczywiście robiła to, co
deklaruje. Cztery strukturalne błędy po cichu ją neutralizowały: niezgodność przestrzeni
normalizacji między zbiorem danych a składnikami $"clip"(0,1)$; brak flagi drugiego rzędu,
przez który składnik dopasowania był pustą operacją wnoszącą zerowy gradient do wag; błąd
znaku w składniku sinka, który trenował odporność _na_ sink zamiast podatności; oraz
nieograniczony składnik ujemny, który rozbiega się do nieskończoności, a który okiełznaliśmy
ograniczeniem (margin clamp).

// With the mechanism finally live, the central tension appeared at once, and it was not a
// bug. At α = 1.0 the alignment term barely moves: the classification gradient dominates
// and the alignment loss stays near 0.99. Larger α does reduce the angle, but only by
// degrading classification — because a network's input gradient cannot simultaneously
// encode the class and point at a fixed, input-independent direction. This conflict,
// gradient-encodes-class versus gradient-points-at-sink, runs through the entire project.
Gdy mechanizm wreszcie działał, natychmiast pojawiło się centralne napięcie — i nie był to
błąd. Przy $alpha = 1.0$ składnik dopasowania ledwie drgnie: gradient klasyfikacji dominuje,
a strata dopasowania pozostaje bliska $0.99$. Większe $alpha$ faktycznie zmniejsza kąt, ale
tylko kosztem degradacji klasyfikacji — gradient sieci względem wejścia nie może
jednocześnie kodować klasy _i_ wskazywać ustalonego, niezależnego od wejścia kierunku. Ten
konflikt — _gradient-koduje-klasę_ kontra _gradient-wskazuje-sink_ — przewija się przez cały
projekt.

== Faza 2: osadzanie sinka jako triggera (CrossTrap i BadNets)

// If we cannot bend the gradient, perhaps we can plant the sink as a backdoor trigger so
// that the attack discovers it. CrossTrapLoss treats the cross as a targeted universal
// perturbation — cross + any image -> fixed class — with orthogonal AT hardening every
// other direction. It collapsed to ~10% clean accuracy. A no-attack diagnostic sweep
// showed this is a weight problem, not a tuning one: the trap term is trivially
// satisfiable while classification is hard, so the optimiser abandons classification.
Skoro nie umiemy nagiąć gradientu, być może da się osadzić sink jako trigger typu backdoor,
tak by atak go _odkrył_. `CrossTrapLoss` traktuje krzyż jako ukierunkowaną perturbację
uniwersalną — krzyż $+$ dowolny obraz $arrow.r$ ustalona klasa — z treningiem ortogonalnym
uodparniającym każdy inny kierunek. Doszło do załamania do $tilde.op 10%$ dokładności na
czystych przykładach. Diagnostyczny przegląd bez ataku pokazał, że to problem _wagi_, a nie
strojenia: składnik pułapki jest trywialnie spełnialny, podczas gdy klasyfikacja jest trudna,
więc optymalizator całkowicie porzuca klasyfikację.

// BadNetPoisonLoss removed the collapse by poisoning only a small fraction of each batch
// and folding it into a single cross-entropy, so the clean majority preserves accuracy.
// It trained cleanly (0.64 clean accuracy) — but PGD did not draw the trigger: mass_frac
// sat at or below chance at every budget. The attack actively avoids the trigger.
`BadNetPoisonLoss` usunął załamanie, zatruwając jedynie niewielki ułamek każdej partii i
składając go w pojedynczą entropię krzyżową, tak że czysta większość zachowuje dokładność.
Trening przebiegł poprawnie ($0.64$ dokładności na czystych przykładach) — ale PGD nie
narysował triggera: `mass_frac` utrzymywał się na poziomie losowym lub _poniżej_ niego przy
każdym budżecie. Atak aktywnie unika triggera.

// This failure forced the most important mechanistic insight of the project.
Ta porażka wymusiła najważniejszy mechanistyczny wniosek całego projektu.

// KEY INSIGHT. PGD follows the local input gradient ∂L/∂x at the clean point. A backdoor
// is a finite, nonlinear "if trigger present -> flip" response; it does not create a local
// gradient pointing toward the trigger. So a local-ascent attack never walks there — it
// follows the residual gradients on the salient object pixels, which is precisely why
// energy concentrates off the low-gradient corner or background where triggers live.
// Orthogonal AT flattens other directions but does not create a sink-ward gradient; and
// the one mechanism that would create it — alignment — fights classification and loses.
// Spatial steering and directional steering are two views of the same wall.
*Kluczowy wniosek.* PGD podąża za _lokalnym_ gradientem wejścia
$partial cal(L) \/ partial x$ w punkcie czystym. Backdoor to _skończona, nieliniowa_ reakcja
„jeśli trigger obecny $arrow.r$ przełącz”; nie tworzy on lokalnego gradientu wskazującego na
trigger. Dlatego atak wspinający się lokalnie nigdy tam nie dochodzi — podąża za resztkowymi
gradientami na istotnych pikselach _obiektu_, co dokładnie tłumaczy, czemu energia
koncentruje się _z dala_ od narożnika czy tła o niskim gradiencie, gdzie żyją triggery.
Trening ortogonalny spłaszcza inne kierunki, lecz nie _tworzy_ gradientu ku sinkowi; a jedyny
mechanizm, który by go stworzył — dopasowanie — walczy z klasyfikacją i przegrywa. Sterowanie
przestrzenne i sterowanie kierunkowe to dwa spojrzenia na tę samą ścianę.

== Faza 3: ograniczanie lokalizacji zamiast kształtu

// A softer goal: stop asking PGD to draw a signed template, and instead confine its energy
// to a known region. SinkConfinementLoss generalises orthogonal AT from a one-dimensional
// template exception to a whole spatial-subspace exception — masking the PGD perturbation
// inside the region before the robust term — plus a backdoor inside so the region stays
// attackable. It also failed: mass_frac below chance, support_cos ≈ 0. Masked AT
// robustifies outside the region but creates no pull into it, so PGD still avoids the
// corner. Every "steer to a fixed spatial or template target" mechanism — alignment,
// CrossTrap, BadNets, masked-AT confinement — is now exhausted.
Cel łagodniejszy: przestać żądać od PGD rysowania znakowanego szablonu i zamiast tego
ograniczyć jego energię do znanego _obszaru_. `SinkConfinementLoss` uogólnia trening
ortogonalny z wyjątku jednowymiarowego (szablon) do wyjątku obejmującego całą podprzestrzeń
przestrzenną — maskując perturbację PGD wewnątrz obszaru przed składnikiem odporności — plus
backdoor wewnątrz, by obszar pozostał atakowalny. To również zawiodło: `mass_frac` poniżej
poziomu losowego, `support_cos` $approx 0$. Maskowany trening uodparnia _poza_ obszarem, ale
nie tworzy przyciągania _do_ niego, więc PGD nadal unika narożnika. Każdy mechanizm
„sterowania ku ustalonemu celowi przestrzennemu lub szablonowi” — dopasowanie, CrossTrap,
BadNets, maskowane ograniczanie — jest teraz wyczerpany.

== Faza 4: wykluczenie czynników zakłócających za pomocą środowiska toy i przeglądu pojemności

// Before declaring the idea impossible we had to rule out two confounds: perhaps the CIFAR
// models were simply undertrained on CPU (50-70% clean accuracy), or perhaps the network
// lacked capacity. Both turned out false, and ruling them out is what makes the negative
// result credible.
Zanim ogłosiliśmy pomysł niewykonalnym, musieliśmy wykluczyć dwa czynniki zakłócające: być
może modele CIFAR były po prostu niedotrenowane na CPU ($50$–$70%$ dokładności), albo sieci
brakowało pojemności. Oba okazały się fałszywe, a właśnie ich wykluczenie czyni wynik
negatywny wiarygodnym.

// The capacity sweep settled it. The CNN was already a ~1.9M-parameter ResNet, so capacity
// was never the limiter — the confound was undertraining. Trained to convergence, the same
// width-64 base reaches 0.923 clean accuracy and a 2x-wider width-128 base reaches 0.921.
// Isolated-alignment fine-tuning from either converged base still yields support_cos ≈ 0
// (0.002-0.013) and energy_frac at chance. Convergence and 4x capacity do not unlock
// directional steering — confirming the structural tension rather than undertraining.
Przegląd pojemności rozstrzygnął sprawę. Użyta sieć CNN była już ResNetem o
$tilde.op 1.9$ mln parametrów, więc pojemność nigdy nie była ograniczeniem — czynnikiem
zakłócającym było niedotrenowanie. Wytrenowana do zbieżności, ta sama baza o szerokości 64
osiąga $0.923$ dokładności, a $2 times$ szersza baza o szerokości 128 osiąga $0.921$.
Dostrajanie samym dopasowaniem (isolated alignment) z każdej zbieżnej bazy nadal daje
`support_cos` $approx 0$ ($0.002$–$0.013$) i `energy_frac` na poziomie losowym. Zbieżność i
$4 times$ większa pojemność _nie_ odblokowują sterowania kierunkowego — co potwierdza napięcie
strukturalne, a nie niedotrenowanie.

// [FIG: cifar-capacity] The confound-killer. Source: analysis/cifar_capacity.py -> reports/_figs/cifar_capacity.png
#figure(
	image("figures/cifar_capacity.png", width: 85%),
	// EN caption: Capacity and convergence are not the limiter. Clean accuracy across model
	// configurations: the early undertrained width-64 runs (~0.69) sit far below the same
	// architecture trained to convergence (0.923), and doubling the width to 7.7M parameters
	// does not help (0.921). Crucially, alignment fine-tuning on these fully-converged,
	// high-capacity bases still fails to steer the attack (support_cos ≈ 0), so the failure
	// to draw a sink is structural — not explained by weak models or too few epochs.
	caption: [
		*Pojemność i zbieżność nie są ograniczeniem.* Dokładność na czystych przykładach dla
		różnych konfiguracji modelu: wczesne, niedotrenowane przebiegi o szerokości 64
		($tilde.op 0.69$) leżą znacznie poniżej tej samej architektury wytrenowanej do
		zbieżności ($0.923$), a podwojenie szerokości do $7.7$ mln parametrów nie pomaga
		($0.921$). Co istotne, dostrajanie dopasowaniem na tych w pełni zbieżnych,
		pojemnych bazach _nadal_ nie steruje atakiem (`support_cos` $approx 0$), więc
		niemożność narysowania sinka jest strukturalna — nie tłumaczą jej słabe modele ani
		zbyt mało epok.
	],
) <fig-capacity>

// The toy then localised the obstacle exactly. In a converged two-dimensional, two-class
// MLP everything is visible. Two results stand out. First, the dimensionality hypothesis is
// refuted: the best achievable alignment does not degrade as input dimension grows from 2 to
// 1000 — it is flat-to-rising. "CIFAR's 3072 dimensions are why it fails" is wrong.
Środowisko toy zlokalizowało następnie przeszkodę dokładnie. W zbieżnym, dwuwymiarowym,
dwuklasowym MLP wszystko jest widoczne. Wyróżniają się dwa wyniki. Po pierwsze, hipoteza
wymiarowości zostaje obalona: najlepsze osiągalne dopasowanie _nie_ pogarsza się wraz ze
wzrostem wymiaru wejścia od $2$ do $1000$ — jest płaskie lub rosnące (@fig-toy-subspace).
Stwierdzenie „CIFAR zawodzi przez swoje $3072$ wymiary” jest błędne.

// [FIG: toy-subspace] Dimensionality is not the obstacle. Source: analysis/toy_subspace.py -> reports/_toy/toy_subspace.png
#figure(
	image("figures/toy_subspace.png", width: 88%),
	// EN caption: Alignment quality does not decay with dimension. Best achievable cos(δ,s)
	// (and energy on the sink axis) as a function of input dimension D, for a sink placed in a
	// label-relevant ("signal") versus a label-irrelevant ("void") subspace, in fully-converged
	// toy MLPs. The curves are flat-to-rising, not decreasing: high dimensionality is not what
	// blocks steering. Placing the sink in a void subspace is consistently easier — the seed of
	// the result that eventually transfers to CIFAR.
	caption: [
		*Jakość dopasowania nie maleje z wymiarem.* Najlepszy osiągalny $cos(delta, s)$ (oraz
		energia na osi sinka) w funkcji wymiaru wejścia $D$, dla sinka umieszczonego w
		podprzestrzeni istotnej dla etykiety („signal”) i nieistotnej („void”), w w pełni
		zbieżnych sieciach toy. Krzywe są płaskie lub rosnące, a nie malejące: to nie wysoka
		wymiarowość blokuje sterowanie. Umieszczenie sinka w podprzestrzeni „void” jest
		konsekwentnie łatwiejsze — to zalążek wyniku, który ostatecznie przenosi się na CIFAR.
	],
) <fig-toy-subspace>

// Second, the budget sweep is decisive. The attack's energy concentrates on a chosen 1-D
// axis far above chance (20-33% vs 0.5% for D=200, a 40-60x enrichment), robustly across
// attack budget — yet the signed alignment cos(δ,s) never exceeds ~0.27, never dominates, and
// flips negative at large budget (the attack moves anti-sink). Concentrating energy is free;
// making the attack draw a signed, dominant sink is fundamentally blocked.
Po drugie, przegląd budżetu jest rozstrzygający. Energia ataku koncentruje się na wybranej osi
jednowymiarowej znacznie powyżej poziomu losowego ($20$–$33%$ wobec $0.5%$ dla $D = 200$, czyli
$40$–$60 times$ wzbogacenie), odpornie na zmianę budżetu ataku — a mimo to znakowane dopasowanie
$cos(delta, s)$ nigdy nie przekracza $tilde.op 0.27$, nigdy nie dominuje i przy dużym budżecie
zmienia znak na _ujemny_ (atak idzie przeciw sinkowi). Koncentracja energii jest darmowa;
zmuszenie ataku do _narysowania_ znakowanego, dominującego sinka jest fundamentalnie
zablokowane.

// [FIG: toy-compare] The four mechanisms side by side in the 2-D landscape. Source: analysis/toy_sink.py -> reports/_toy/toy_compare.png
#figure(
	image("figures/toy_compare.png", width: 95%),
	// EN caption: Loss landscapes and attack trajectories in the toy. Each panel shows the 2-D
	// loss surface, the input-gradient field, the decision boundary and live PGD trajectories
	// for a different mechanism (baseline, on-manifold alignment, off-manifold sculpting,
	// attack-aware). On-manifold alignment reproduces the accuracy-vs-steering tension in a
	// fully converged net; off-manifold and attack-aware variants do not beat plain alignment
	// and are unstable. The figure makes visible why no trajectory is bent into a dominant well
	// at the sink.
	caption: [
		*Krajobrazy strat i trajektorie ataku w środowisku toy.* Każdy panel pokazuje
		dwuwymiarową powierzchnię straty, pole gradientu wejścia, granicę decyzyjną oraz
		trajektorie PGD na żywo dla innego mechanizmu (baza, dopasowanie na rozmaitości,
		rzeźbienie poza rozmaitością, wariant świadomy ataku). Dopasowanie na rozmaitości
		odtwarza napięcie dokładność–sterowanie w w pełni zbieżnej sieci; warianty poza
		rozmaitością i świadome ataku nie biją zwykłego dopasowania i są niestabilne. Rysunek
		uwidacznia, dlaczego żadna trajektoria nie zostaje nagięta w dominującą studnię przy
		sinku.
	],
) <fig-toy-compare>

== Faza 5: „wygrana” w środowisku toy i precyzyjna granica

// Reframing the budget-sweep result as a positive statement gives the project's clean
// result. If we drop the demand for a recognizable, signed sink and ask only that the
// attack's energy land on a known direction, the toy delivers spectacularly, and for free.
Przeformułowanie wyniku przeglądu budżetu na stwierdzenie pozytywne daje czysty wynik
projektu. Jeśli porzucimy żądanie _rozpoznawalnego, znakowanego_ sinka i poprosimy jedynie o
to, by energia ataku trafiła na znany kierunek, środowisko toy dostarcza go spektakularnie i
za darmo.

// [FIG: toy-win] The headline positive result in the toy. Source: analysis/toy_win.py -> reports/_toy/toy_win.png
#figure(
	image("figures/toy_win.png", width: 98%),
	// EN caption: Forcing the attack into a known subspace is free, robust, and strengthens
	// with dimension. (A) Fraction of attack energy on the chosen 1-D sink axis versus attack
	// budget ε (D=200): the aligned net (clean acc 1.00) keeps ~0.1-0.4 of all attack energy
	// on a single axis across the whole budget range, far above the 1/D=0.005 chance line and
	// well above the CE-only baseline. (B) The same energy fraction does not decay as input
	// dimension D grows from 10 to 1000. (C) Enrichment over chance therefore grows with
	// dimension — 1x at D=10, 2x at 50, 36x at 200, 187x at 1000 — all at clean accuracy
	// 0.86-1.00. Energy concentration is a real, robust, free effect when truly unused
	// dimensions exist.
	caption: [
		*Zmuszenie ataku do wejścia w znaną podprzestrzeń jest darmowe, odporne i rośnie z
		wymiarem.* (A) Udział energii ataku na wybranej osi sinka (1-D) w funkcji budżetu ataku
		$epsilon$ ($D = 200$): sieć dopasowana (dokładność $1.00$) utrzymuje $tilde.op 0.1$–$0.4$
		całej energii ataku na pojedynczej osi w całym zakresie budżetu, znacznie powyżej linii
		losowej $1\/D = 0.005$ i wyraźnie powyżej bazy uczonej samym CE. (B) Ten sam udział
		energii _nie_ maleje, gdy wymiar wejścia $D$ rośnie od $10$ do $1000$. (C) Wzbogacenie
		względem poziomu losowego _rośnie_ więc z wymiarem — $1 times$ przy $D=10$, $2 times$
		przy $50$, $36 times$ przy $200$, $187 times$ przy $1000$ — wszystko przy dokładności
		$0.86$–$1.00$. Koncentracja energii to realny, odporny, darmowy efekt, gdy istnieją
		naprawdę nieużywane wymiary.
	],
) <fig-toy-win>

// The same converged net shows the wall just as clearly. Energy concentrates, yet the signed
// cosine swings from +0.42 down to -0.32 as budget grows: the attack never commits to the
// sink's sign and eventually anti-aligns. This is the deliverable boundary, confirmed in a
// converged, low-dimensional net — the core tension, not an artifact.
Ta sama zbieżna sieć równie wyraźnie pokazuje ścianę. Energia się koncentruje, lecz znakowany
kosinus zmienia się od $+0.42$ do $-0.32$ wraz ze wzrostem budżetu: atak nigdy nie zobowiązuje
się do znaku sinka i ostatecznie się z nim anty-dopasowuje. To właśnie granica, którą
dostarczamy, potwierdzona w zbieżnej, niskowymiarowej sieci — rdzeń napięcia, a nie artefakt.

// [FIG: toy-boundary] Concentration yes, signed drawing no. Source: analysis/toy_win_boundary.py -> reports/_toy/toy_win_boundary.png
#figure(
	image("figures/toy_win_boundary.png", width: 90%),
	// EN caption: The boundary: energy concentrates but the sign is uncontrolled. For the same
	// converged toy net that produces the previous figure, energy on the sink subspace stays
	// high, but the signed alignment cos(δ,s) falls from +0.42 to -0.32 as the attack budget
	// grows — the perturbation increasingly points against the intended sink. So the achievable
	// effect is sign-free energy concentration (a detector can still flag it), whereas a clean,
	// dominant, correctly-signed drawing is fundamentally out of reach.
	caption: [
		*Granica: energia się koncentruje, ale znak jest niekontrolowany.* Dla tej samej
		zbieżnej sieci toy, która daje @fig-toy-win, energia na podprzestrzeni sinka pozostaje
		wysoka, lecz znakowane dopasowanie $cos(delta, s)$ spada od $+0.42$ do $-0.32$ wraz ze
		wzrostem budżetu ataku — perturbacja coraz bardziej wskazuje _przeciw_ zamierzonemu
		sinkowi. Osiągalnym efektem jest więc bezznakowa koncentracja energii (detektor wciąż
		może ją zasygnalizować), podczas gdy czysty, dominujący, poprawnie znakowany rysunek
		jest fundamentalnie poza zasięgiem.
	],
) <fig-toy-boundary>

== Faza 6: powrót na CIFAR, tym razem wiernie

// The toy says energy concentration should be achievable; does it transfer to CIFAR? We
// tested this in two steps on the converged 0.92 network.
Środowisko toy mówi, że koncentracja energii powinna być osiągalna; czy przenosi się na
CIFAR? Sprawdziliśmy to w dwóch krokach na zbieżnej sieci o dokładności $0.92$.

// First, a controlled pattern sweep (Stage-3 question Q5). Across six visual patterns (full
// cross, small cross, constellation, corner square, two checkerboards) under the best
// alignment fine-tune, no pattern concentrates energy on CIFAR: support_cos in [-0.012,
// +0.013], mass_frac and energy_frac at chance everywhere — central, peripheral, sparse, or
// signed alike. The visual-sink idea does not transfer.
Po pierwsze, kontrolowany przegląd wzorców (pytanie Q5 z etapu 3). Wśród sześciu wzorców
wizualnych (pełny krzyż, mały krzyż, konstelacja, kwadrat w rogu, dwie szachownice), przy
najlepszym dostrajaniu dopasowaniem, _żaden_ wzorzec nie koncentruje energii na CIFAR:
`support_cos` w przedziale $[-0.012, +0.013]$, `mass_frac` i `energy_frac` wszędzie na
poziomie losowym — niezależnie od tego, czy centralny, peryferyjny, rzadki czy znakowany.
Idea sinka wizualnego nie przenosi się.

// [FIG: pattern-table] No visual pattern is drawn on CIFAR. Source: analysis/cifar_pattern_table.py -> reports/_figs/pattern_table.md
#figure(
	table(
		columns: 6,
		align: (left, right, right, right, right, left),
		stroke: 0.5pt + gray,
		table.header([*wzorzec*], [*nośnik*], [*losowo*], [*dokł.*], [*najl. `mass_frac`*], [*werdykt*]),
		[krzyż (pełny)], [720], [0.234], [0.611], [0.279], [nie narysowany],
		[krzyż (pełny), align FT], [720], [0.234], [0.713], [0.289], [nie narysowany],
		[small\_cross 8×8], [84], [0.027], [0.107], [0.035], [załamanie],
		[corner\_square 4×4, BadNet], [48], [0.016], [0.642], [0.019], [nie narysowany],
		[corner\_square 4×4, +L2 AT], [48], [0.016], [0.466], [0.011], [nie narysowany],
		[corner\_square 4×4, maska AT], [48], [0.016], [0.532], [0.011], [nie narysowany],
	),
	// EN caption: Pattern complexity versus steerability on CIFAR-10. For each pattern and
	// mechanism, the best mass_frac the attack puts on the pattern support stays at or below
	// the chance value |S|/D, and support_cos (not shown) never clears zero. No placement —
	// dense or sparse, central or corner — is drawn; the corner_square cases even fall below
	// chance, the attack avoiding the corner.
	caption: [
		*Złożoność wzorca a sterowalność na CIFAR-10.* Dla każdego wzorca i mechanizmu najlepszy
		`mass_frac`, jaki atak nakłada na nośnik wzorca, pozostaje na poziomie losowym $|S|\/D$
		lub poniżej, a `support_cos` (niepokazany) nigdy nie przekracza zera. Żadne rozmieszczenie
		— gęste czy rzadkie, centralne czy w rogu — nie zostaje narysowane; przypadki
		`corner_square` spadają nawet _poniżej_ poziomu losowego, gdyż atak unika narożnika.
	],
) <fig-pattern-table>

// We confirmed the geometry directly. A loss-landscape slice in the (sink, gradient) plane
// shows no well toward the sink and a flat cosine along the PGD trajectory; a side-by-side of
// the template and the actual perturbation shows the attack drawing object-shaped noise.
Potwierdziliśmy geometrię bezpośrednio. Przekrój krajobrazu strat w płaszczyźnie (sink,
gradient) nie wykazuje studni w stronę sinka, a kosinus wzdłuż trajektorii PGD pozostaje płaski
(@fig-cifar-landscape); zestawienie szablonu z rzeczywistą perturbacją pokazuje, że atak rysuje
szum o kształcie obiektu (@fig-cifar-draws).

// [FIG: cifar-landscape] No well toward the sink on CIFAR. Source: analysis/cifar_landscape.py -> reports/_figs/cifar_landscape.png
#figure(
	image("figures/cifar_landscape.png", width: 92%),
	// EN caption: The CIFAR loss landscape has no basin toward the sink. A 2-D slice of the
	// classification loss spanned by the sink direction and the input-gradient direction, with
	// the PGD trajectory overlaid, plus cos(δ_t, s) as a function of attack step. The loss rises
	// along the gradient axis but is flat along the sink axis, the trajectory never turns toward
	// the sink, and the cosine stays ≈ 0 throughout. There is no downhill path an attack could
	// follow to the sink.
	caption: [
		*Krajobraz strat CIFAR nie ma niecki w stronę sinka.* Dwuwymiarowy przekrój straty
		klasyfikacji rozpięty przez kierunek sinka i kierunek gradientu wejścia, z nałożoną
		trajektorią PGD oraz $cos(delta_t, s)$ w funkcji kroku ataku. Strata rośnie wzdłuż osi
		gradientu, lecz jest płaska wzdłuż osi sinka, trajektoria nigdy nie skręca ku sinkowi, a
		kosinus pozostaje $approx 0$ przez cały czas. Po prostu nie ma ścieżki w dół, którą atak
		mógłby podążyć do sinka.
	],
) <fig-cifar-landscape>

// [FIG: cifar-draws] What the attack draws instead. Source: analysis/cifar_attack_viz.py -> reports/_figs/cifar_attack_draws.png
#figure(
	image("figures/cifar_attack_draws.png", width: 92%),
	// EN caption: What PGD draws instead of the sink. Columns show, for several inputs, the clean
	// image, the intended sink template, and the actual PGD perturbation. The perturbation is
	// structured around the salient object pixels — edge and texture noise — and bears no
	// resemblance to the template (cos ≈ 0). The attack spends its budget where the local
	// gradient is largest, which is on the object, never on the designer's pattern.
	caption: [
		*Co atak rysuje zamiast sinka.* Kolumny pokazują, dla kilku wejść, czysty obraz,
		zamierzony szablon sinka oraz rzeczywistą perturbację PGD. Perturbacja jest zorganizowana
		wokół istotnych pikseli _obiektu_ — szum krawędzi i tekstur — i nie przypomina szablonu
		($cos approx 0$). Atak wydaje budżet tam, gdzie lokalny gradient jest największy, czyli na
		obiekcie, nigdy na wzorcu projektanta.
	],
) <fig-cifar-draws>

// FGSM behaves like PGD here: both give support_cos ≈ 0 and mass at chance, even though PGD
// drives robust accuracy to zero. The one apparent exception — L2 FGSM placing mass_frac
// 0.356 > 0.234 on the cross — is central-pixel saliency, not drawing, since support_cos
// remains ~0.
FGSM zachowuje się tu tak jak PGD: oba dają `support_cos` $approx 0$ i masę na poziomie losowym,
choć PGD sprowadza dokładność odpornościową do zera (@fig-fgsm-table). Jedyny pozorny wyjątek —
FGSM $L_2$ nakładający `mass_frac` $0.356 > 0.234$ na krzyż — to istotność pikseli centralnych, a
nie rysowanie, gdyż `support_cos` pozostaje $tilde.op 0$.

// [FIG: fgsm-table] FGSM vs PGD on the converged net. Source: analysis/cifar_fgsm_table.py -> reports/_figs/fgsm_vs_pgd.md
#figure(
	table(
		columns: 6,
		align: (left, left, right, right, right, right),
		stroke: 0.5pt + gray,
		table.header([*norma*], [*atak*], [*$epsilon$*], [*dokł. odp.*], [*`support_cos`*], [*`mass_frac`*]),
		[L2], [FGSM], [0.5], [0.236], [$+0.000$], [0.356],
		[L2], [FGSM], [2.0], [0.146], [$-0.002$], [0.355],
		[L2], [PGD],  [0.5], [0.012], [$+0.002$], [0.282],
		[L2], [PGD],  [2.0], [0.000], [$+0.004$], [0.258],
		[L∞], [FGSM], [0.031], [0.068], [$+0.006$], [0.236],
		[L∞], [PGD],  [0.031], [0.000], [$+0.004$], [0.238],
	),
	// EN caption: FGSM and PGD agree: no drawing, on the converged 0.92 net. For both attacks and
	// both norms, support_cos ≈ 0 and mass_frac is at the chance value (0.234 for the cross). PGD
	// is far stronger as an attack (robust accuracy -> 0) but no more steerable. The elevated L2
	// FGSM mass reflects central-pixel saliency overlapping the cross, not reproduction of shape.
	caption: [
		*FGSM i PGD są zgodne: brak rysowania, na zbieżnej sieci $0.92$.* Dla obu ataków i obu norm
		`support_cos` $approx 0$, a `mass_frac` jest na poziomie losowym ($0.234$ dla krzyża). PGD
		jest znacznie silniejszy jako atak (dokładność odpornościowa $arrow.r 0$), lecz nie
		bardziej sterowalny. Podwyższona masa FGSM $L_2$ odzwierciedla istotność pikseli
		centralnych pokrywających się z krzyżem, a nie odtworzenie jego kształtu.
	],
) <fig-fgsm-table>

// Second, the faithful port of the toy idea: place the sink in a label-irrelevant direction
// the classifier is genuinely blind to. We aligned the converged net's gradient toward a dense
// high-frequency direction — a Nyquist per-pixel checkerboard, where natural images carry almost
// no energy — and, as a control, toward a random direction, sweeping α.
Po drugie, wierne przeniesienie idei toy: umieszczenie sinka w kierunku _nieistotnym dla
etykiety_, na który klasyfikator jest naprawdę ślepy. Dopasowaliśmy gradient zbieżnej sieci ku
gęstemu kierunkowi wysokoczęstotliwościowemu — szachownicy Nyquista piksel po pikselu, gdzie
obrazy naturalne niosą niemal zero energii — oraz, dla kontroli, ku kierunkowi losowemu,
przemiatając $alpha$.

// This is where concentration finally transfers to CIFAR — but only for the high-frequency
// direction, and not for free. Relative to chance (energy_frac = 3.26e-4), the no-alignment
// baseline already carries 1.5x (the high-frequency band naturally holds slightly more
// adversarial energy), and alignment lifts this to a peak of ~44x at α=6, with ~23-28x sustained
// at α=8-12. The random direction stays flat at chance for every α: concentration needs a
// direction the classifier is blind to, not merely a non-visual one.
To tutaj koncentracja wreszcie przenosi się na CIFAR — ale tylko dla kierunku
wysokoczęstotliwościowego i nie za darmo. Względem poziomu losowego (`energy_frac` $= 3.26 times
10^(-4)$) baza bez dopasowania niesie już $1.5 times$ (pasmo wysokich częstotliwości naturalnie
zawiera nieco więcej energii adwersarialnej), a dopasowanie podnosi to do szczytu
$tilde.op 44 times$ przy $alpha = 6$, z $tilde.op 23$–$28 times$ utrzymywanym przy
$alpha = 8$–$12$. Kierunek losowy pozostaje płaski na poziomie losowym dla każdego $alpha$:
koncentracja wymaga kierunku, na który klasyfikator jest _ślepy_, a nie jedynie „niewizualnego”.

// The cost is accuracy, and the frontier is strikingly non-monotone. As α grows the model first
// collapses (α=2 -> 0.38 clean, reproducibly across three seeds), then recovers through α=4-12
// (peak 0.69), then collapses again (α=32 -> 0.35). There is no cheap high-accuracy knee: any
// alignment strong enough to concentrate energy knocks the model off its 0.92 basin, and training
// only re-stabilises around α≈8-12.
Kosztem jest dokładność, a granica jest uderzająco niemonotoniczna. Wraz ze wzrostem $alpha$ model
najpierw się _załamuje_ ($alpha = 2 arrow.r 0.38$ dokładności, powtarzalnie dla trzech ziaren),
następnie _wraca do formy_ przez $alpha = 4$–$12$ (szczyt $0.69$), po czym znów się załamuje
($alpha = 32 arrow.r 0.35$). Nie ma taniego kolana o wysokiej dokładności: każde dopasowanie na
tyle silne, by skoncentrować energię, zrzuca model z jego niecki $0.92$, a trening stabilizuje się
ponownie dopiero przy $alpha approx 8$–$12$.

// [FIG: cifar-void] The CIFAR frontier — the second headline result. Source: analysis/cifar_void_tradeoff.py -> reports/_figs/cifar_void_tradeoff.png
#figure(
	image("figures/cifar_void_tradeoff.png", width: 98%),
	// EN caption: Energy concentration transfers to CIFAR-10 only for a label-blind direction, and
	// is paid for in accuracy. Left: energy concentration (energy_frac over chance) versus
	// alignment strength α. The high-frequency sink (blue) rises from 1.5x at α=0 to a peak of 44x
	// at α=6, holding 23-28x at α=8-12; the random direction (red) never leaves the chance line.
	// Right: the same points against clean accuracy, exposing the trade-off and its
	// non-monotonicity — accuracy dips at α=2 (0.38), recovers to 0.69 near α=12, then collapses at
	// α=32 (0.35). The usable operating region is α≈8-12: ~23-28x chance at 0.67-0.69 accuracy.
	caption: [
		*Koncentracja energii przenosi się na CIFAR-10 tylko dla kierunku ślepego dla etykiety i
		jest opłacana dokładnością.* Po lewej: koncentracja energii (`energy_frac` względem poziomu
		losowego) w funkcji siły dopasowania $alpha$. Sink wysokoczęstotliwościowy (niebieski) rośnie
		od $1.5 times$ przy $alpha=0$ do szczytu $44 times$ przy $alpha=6$, utrzymując $23$–$28 times$
		przy $alpha=8$–$12$; kierunek losowy (czerwony) nigdy nie opuszcza linii losowej. Po prawej:
		te same punkty względem dokładności, odsłaniające kompromis i jego niemonotoniczność —
		dokładność spada przy $alpha=2$ ($0.38$), wraca do $0.69$ blisko $alpha=12$, po czym załamuje
		się przy $alpha=32$ ($0.35$). Użyteczny obszar pracy to $alpha approx 8$–$12$:
		$tilde.op 23$–$28 times$ poziomu losowego przy dokładności $0.67$–$0.69$.
	],
) <fig-cifar-void>

// The mechanism is also stable across attack budget on CIFAR (Stage-3 question Q4): the
// concentration metrics hold as ε is varied, so the effect is not a single-budget artifact.
Mechanizm jest też stabilny względem budżetu ataku na CIFAR (pytanie Q4 z etapu 3): metryki
koncentracji utrzymują się przy zmianie $epsilon$, więc efekt nie jest artefaktem jednego budżetu
(@fig-cifar-eps).

// [FIG: cifar-eps] Sensitivity to the perturbation budget. Source: analysis/cifar_eps_curves.py -> reports/_figs/cifar_eps_curves.png
#figure(
	image("figures/cifar_eps_curves.png", width: 92%),
	// EN caption: Stability of the metrics versus attack budget ε. support_cos, mass_frac and
	// energy_frac as functions of the L2 budget, for the baseline and the aligned net. The curves
	// are smooth and monotone with no threshold effects: the (small) signal present on CIFAR is
	// consistent across budgets rather than appearing only at one carefully chosen ε.
	caption: [
		*Stabilność metryk względem budżetu ataku $epsilon$.* `support_cos`, `mass_frac` i
		`energy_frac` w funkcji budżetu $L_2$, dla bazy i sieci dopasowanej. Krzywe są gładkie i
		monotoniczne, bez efektów progowych: ten (niewielki) sygnał obecny na CIFAR jest spójny w
		różnych budżetach, a nie pojawia się tylko przy jednym starannie dobranym $epsilon$.
	],
) <fig-cifar-eps>

// ====================================================================
= Synteza i werdykt
// ====================================================================

// The threads pull together into a three-part story.
Wątki splatają się w trzyczęściową opowieść.

// A recognizable visual sink cannot be drawn on CIFAR. Across five mechanisms and six patterns,
// on a fully-converged 0.92 network at up to 2x width, no pattern is reproduced (support_cos ≈ 0,
// mass at chance). This is a characterized impossibility, with the capacity and dimensionality
// confounds explicitly ruled out.
+ *Rozpoznawalnego sinka wizualnego nie da się narysować na CIFAR.* W pięciu mechanizmach i sześciu
  wzorcach, na w pełni zbieżnej sieci $0.92$ przy szerokości do $2 times$, żaden wzorzec nie zostaje
  odtworzony (`support_cos` $approx 0$, masa na poziomie losowym). To _scharakteryzowana_
  niemożliwość, z jawnie wykluczonymi czynnikami pojemności i wymiarowości.

// Energy concentration does transfer to CIFAR — but only for a label-blind (high-frequency)
// direction, at 23-28x chance, and not for free: it costs accuracy (0.92 -> ~0.68) along a
// non-monotone frontier. A random direction achieves nothing.
+ *Koncentracja energii przenosi się na CIFAR* — ale tylko dla kierunku ślepego dla etykiety
  (wysokoczęstotliwościowego), na poziomie $23$–$28 times$ losowego i nie za darmo: kosztuje
  dokładność ($0.92 arrow.r tilde.op 0.68$) wzdłuż niemonotonicznej granicy. Kierunek losowy nie
  osiąga niczego.

// The toy proves the clean limit. When truly unused dimensions exist, concentration reaches
// 36-187x chance at near-free accuracy and is robust across budget — the idealised version of
// result (2), with the same boundary: the sign is never controlled.
+ *Środowisko toy dowodzi czystej granicy.* Gdy istnieją naprawdę nieużywane wymiary, koncentracja
  sięga $36$–$187 times$ poziomu losowego przy niemal darmowej dokładności i jest odporna na zmianę
  budżetu — to wyidealizowana wersja wyniku (2), z tą samą granicą: znak nigdy nie jest
  kontrolowany.

// One sentence explains all of it: a network's input gradient can encode the class or point at a
// fixed direction, but not both. Detection-grade concentration onto a label-blind subspace is real
// and controllable, at an accuracy price; a visible, signed drawing is blocked by exactly that
// tension.
Jedno zdanie tłumaczy całość: _gradient sieci względem wejścia może albo kodować klasę, albo
wskazywać ustalony kierunek, ale nie jedno i drugie naraz_. Koncentracja klasy detekcyjnej na
podprzestrzeni ślepej dla etykiety jest realna i sterowalna, za cenę dokładności; widoczny,
znakowany rysunek jest blokowany właśnie przez to napięcie.

// A note on scope: the specification named CIFAR-100 for Stage 3. We deliberately stayed on
// CIFAR-10 plus the toy — once the effect fails to yield a visual drawing on the easier dataset, a
// harder one cannot rescue it, and the toy isolates the mechanism far more cleanly. A CIFAR-100
// confirmation remains a low-risk, deferred item.
Uwaga o zakresie: specyfikacja wskazywała CIFAR-100 na etap 3. Świadomie pozostaliśmy przy CIFAR-10
i środowisku toy — skoro efekt nie daje rysunku wizualnego na łatwiejszym zbiorze, trudniejszy go
nie uratuje, a środowisko toy izoluje mechanizm znacznie czyściej. Potwierdzenie na CIFAR-100
pozostaje odłożonym zadaniem niskiego ryzyka.

// ====================================================================
= Wnioski i kierunki przyszłych prac
// ====================================================================

// We set out to make a model betray its attacker by forcing white-box gradient attacks to draw a
// fixed visual symbol. The honest outcome: the strong version of this goal is unreachable for
// principled reasons, while a useful weaker version — forcing the attack into a known, label-blind
// subspace — is achievable, and was demonstrated on both a toy and CIFAR-10. The contribution is
// the sharp boundary between the two.
Postawiliśmy sobie za cel sprawienie, by model zdradził atakującego, zmuszając ataki gradientowe
white-box do narysowania ustalonego symbolu wizualnego. Uczciwy wynik jest taki: silna wersja tego
celu jest nieosiągalna z zasadniczych powodów, podczas gdy użyteczna wersja słabsza — zmuszenie
ataku do wejścia w znaną, ślepą dla etykiety podprzestrzeń — jest osiągalna i została pokazana
zarówno w środowisku toy, jak i na CIFAR-10. Wkładem jest ostra granica między tymi dwoma.

// Several concrete directions follow naturally.
Naturalnie wynika z tego kilka konkretnych kierunków.

// A detector instead of a drawing. The achievable effect is exactly what a detector needs:
// project an input's perturbation onto the known basis and flag anomalous energy. This sidesteps
// the gradient's dual role entirely and is the most promising next step.
+ *Detektor zamiast rysunku.* Osiągalny efekt to dokładnie to, czego potrzebuje detektor:
  rzutować perturbację wejścia na znaną bazę i sygnalizować anomalną energię. Omija to całkowicie
  podwójną rolę gradientu i jest najbardziej obiecującym następnym krokiem.

// Off-manifold gradient sculpting. Accuracy only constrains the model on the data manifold, yet
// the attack travels mostly off it. A loss that pins the function on-manifold (a KL term to a
// frozen classifier) while bending the gradient only at the off-manifold points the attack visits
// is the first formulation in which alignment and accuracy need not fight over the same gradient.
// The open question is the curvature cost.
+ *Rzeźbienie gradientu poza rozmaitością.* Dokładność ogranicza model jedynie na rozmaitości
  danych, podczas gdy atak porusza się głównie poza nią. Strata przypinająca funkcję na rozmaitości
  (składnik KL względem zamrożonego klasyfikatora), a nagnająca gradient tylko w odwiedzanych przez
  atak punktach poza rozmaitością, to pierwsze sformułowanie, w którym dopasowanie i dokładność nie
  muszą walczyć o ten sam gradient. Pytaniem otwartym jest koszt krzywizny.

// Designated-UAP training and architectural bottlenecks. Train the sink as a fixed,
// rate-controlled universal loss-increasing direction (milder than a forced label), or build a
// low-rank input bottleneck whose attackable subspace contains the sink by construction.
+ *Trening wyznaczonego UAP i wąskie gardła architektury.* Trenować sink jako ustalony,
  kontrolowany co do tempa, uniwersalny kierunek zwiększający stratę @moosavi2017uap (łagodniejszy
  niż wymuszona etykieta), albo zbudować niskorangowe wąskie gardło wejścia, którego atakowalna
  podprzestrzeń zawiera sink z konstrukcji.

// Robust-feature framing. That only a label-blind direction concentrates energy connects directly
// to the robust/non-robust feature view of adversarial examples; characterising which subspaces are
// "free" for a dataset would predict the achievable concentration in advance.
+ *Ujęcie przez cechy odporne.* Fakt, że tylko kierunek ślepy dla etykiety koncentruje energię,
  łączy się wprost ze spojrzeniem na przykłady adwersarialne przez cechy odporne i nieodporne
  @ilyas2019; scharakteryzowanie, które podprzestrzenie są „darmowe” dla danego zbioru, pozwoliłoby
  z góry przewidzieć osiągalną koncentrację.

#pagebreak()
#bibliography("bib.yaml", full: true)

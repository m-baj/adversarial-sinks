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
				Dokumentacja Końcowa / ZZSN 2026L
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
Dokumentacja końcowa\ Zaawansowane Zagadnienia Sieci Neuronowych, 2026L
#v(2em)
Repozytorium:\ #text(blue)[https://github.com/m-baj/adversarial-sinks]
#v(5%)

#outline()
#pagebreak()

// ====================================================================
= Wprowadzenie
// ====================================================================

Przykłady adwersarialne to niewielkie, celowo spreparowane perturbacje przykładu wejściowego, które zmieniają
wynik predykcji sieci.
Atakujący w scenariuszu white-box, mający dostęp do gradientu modelu, jest często w stanie
przepchnąć dowolne wejście przez granicę decyzyjną, podążając za kierunkiem,
w którym funkcja straty klasyfikacji rośnie najszybciej.

Celem projektu było sprawdzenie, czy poprzez wprowadzenie specjalnej funkcji straty jesteśmy
w stanie kształtować krajobraz strat. Wówczas możemy sprawić, by atak adwersarialny zbiegał się
do perturbacji przypominającej konkretny, znany symbol, który zdradziłby atakującego - tzw. _adversarial sink_.
Nasz plan łączył trzy obronne składowe w jedną niestandardową funkcję straty, ocenianą na zbiorze CIFAR-10.

Wynik badania jest częściowo negatywny - przedstawiamy wyniki uruchomionych eksperymentów, 
płynące z nich wnioski oraz towarzyszący tok rozumowania.


// ====================================================================
= Sformułowanie problemu
// ====================================================================

== Model zagrożenia i ataki

Pracujemy w standardowym scenariuszu white-box. Klasyfikator $f_theta$ odwzorowuje obraz
$x in [0,1]^D$ (tutaj $D = 3 dot 32 dot 32 = 3072$ dla CIFAR-10) na logity klas. Atak poszukuje
perturbacji $delta$, ograniczonej budżetem $norm(delta) <= epsilon$, która maksymalizuje
stratę klasyfikacji. Używamy dwóch kanonicznych ataków pierwszego rzędu, oba przez
bibliotekę Foolbox: FGSM - pojedynczego kroku w kierunku znaku
gradientu oraz PGD, jego iterowanej i rzutowanej wersji @madry2018.

Iteracja PGD (w wariancie $L_infinity$) ma postać:

$ delta_(t+1) = "clip"_epsilon (delta_t + alpha dot "sign"(nabla_delta cal(L)_"CE"(f_theta (x + delta_t), y))) $

Norma $L_infinity$ ogranicza jedynie maksymalną zmianę pojedynczego piksela (co najwyżej $epsilon$), ale nie karze za to, ilu pikseli atak dotknie.
Najskuteczniejszy atak wykorzystuje więc cały budżet na każdym pikselu naraz, dając perturbację rozlaną po całym obrazie — nigdy rzadki, lokalny kształt.
Norma $L_2$ ogranicza natomiast łączną energię perturbacji, więc opłaca się skupić ją na niewielu pikselach o wysokim kontraście. Dlatego rzadki, wysokokontrastowy sink może powstać wyłącznie pod atakiem $L_2$

== Proponowana funkcja straty

Proponowana przez nas funkcja straty, która pozwoliłaby lepiej kształtować krajobraz strat, oparta jest na kilku składnikach, wykorzystujących standardową entropię krzyżową.

*Dopasowanie gradientu (gradient alignment).* Aby nakierować gradient od wejścia w
stronę sinka $s$, wprowadzamy karę za kąt między nimi. Przy podobieństwie kosinusowym składnik wynosi
$0$, gdy gradient już wskazuje na sink, i rośnie ku $2$, gdy wskazuje w przeciwnym kierunku:

$ L_"align" = 1 - (nabla_x cal(L)_"CE" (f_theta (x), y) dot s) / (norm(nabla_x cal(L)_"CE" (f_theta (x), y))_2 dot norm(s)_2) $ <eq-align>

Mechanizm ma w zamyśle kierować atak PGD w kierunku sinka.

*Utrzymanie sinka (sink preservation).* Chcemy, aby model wciąż błędnie klasyfikował,
gdy sink jest nałożony na obraz, tak by pozostawał on „dziurą” w
zabezpieczeniach. To składnik ujemny, utrzymujący $cal(L)_"CE" (f_theta (x + s), y)$ na
wysokim poziomie:

$ L_"sink" = - cal(L)_"CE" (f_theta (x + s), y) $ <eq-sink>

*Trening ortogonalny (orthogonal adversarial training).* Klasyczny trening adwersarialny (Mądry i in. @madry2018) uodparnia model we _wszystkich_ kierunkach, w tym w kierunku
sinka, co jest sprzeczne ze składnikiem (2). Zamiast tego rzutujemy perturbację PGD na
podprzestrzeń ortogonalną do $s$, więc odporność trenowana jest w każdym kierunku _poza_
sinkiem:

$ L_"robust" = cal(L)_"CE" (f_theta (x + delta^perp), y), quad delta^perp = delta_"PGD" - "proj"_s (delta_"PGD") $ <eq-robust>

Pełna funkcja celu łączy te składniki za pomocą trzech hiperparametrów równoważących
$alpha, lambda_s, lambda_r$:

$ L_"total" = cal(L)_"CE" (f_theta (x), y) + alpha L_"align" - lambda_s cal(L)_"CE" (f_theta (x + s), y) + lambda_r cal(L)_"CE" (f_theta (x + delta^perp), y) $ <eq-total>

== Metryki detekcji

Nie oczekujemy, by atak wyrysował wyraźny krzyż (plus) widoczny gołym okiem; potrzebujemy, by jego perturbacja $delta$ trafiała w znany wzorzec w mierzalnym stopniu, znacznie powyżej poziomu losowego.

Sink zapisujemy jako wektor $s in RR^D$ w przestrzeni obrazu (sam wzorzec potraktowany jako wektor). Jego nośnik (_ang. support_) $S$ to zbiór niezerowych pikseli wzorca, a $|S|$ — ich
liczba. Choć wzorzec obejmuje wiele pikseli, jako jeden ustalony wektor wyznacza w przestrzeni obrazu tylko jeden kierunek - inaczej mówiąc, jeden wektor rozpina jednowymiarową przestrzeń. Tę prostą (wszystkie skalowania $c dot s$) nazywamy osią sinka. Śledzimy trzy uzupełniające się wielkości:

- *`support_cos`* - kosinus między $delta$ a wzorcem $s$, liczony tylko na pikselach nośnika $S$ i z zachowaniem znaku: czy $delta$ odtwarza dokładny kształt i znak wzorca? To jedyna z trzech metryk czuła na znak. Poziom losowy $approx 0$.
- *`mass_frac`* - jaki ułamek energii ($L_2$) perturbacji $delta$ trafia we właściwe piksele, czyli na nośnik $S$ — bez względu na ich wartości i znaki. Losowa perturbacja trafia tam ułamkiem $(|S|)/D$.
- *`energy_frac`* - jaki ułamek energii $delta$ układa się wzdłuż dokładnej osi sinka, czyli $cos^2(delta, s)$. Na jedną z $D$ osi losowo przypada $1/D$. Ponieważ to kwadrat kosinusa, metryka jest bezznakowa — rośnie tak samo, czy $delta$ idzie w stronę sinka, czy dokładnie przeciwnie.

Różnica między dwiema ostatnimi metrykami jest sednem całej detekcji: `mass_frac` pyta tylko, czy energia trafia w zbiór $|S|$ pikseli, a `energy_frac` — czy układa się wzdłuż
jednego konkretnego wektora. Dlatego dla gęstego sinka, którego nośnik obejmuje niemal cały obraz ($(|S|)/D approx 1$), `mass_frac` przestaje cokolwiek mówić, a rozstrzyga
`energy_frac`.

Wzorzec uznajemy za _narysowany_ wtedy i tylko wtedy, gdy `support_cos` jest wyraźnie
dodatni i `mass_frac` przekracza poziom losowy, a model zachowuje przy tym akceptowalną
dokładność na nieatakowanych obrazach. 

_Koncentracja energii_ to słabszy warunek: atak kieruje nieproporcjonalnie dużo
perturbacji wzdłuż osi sinka (`energy_frac` $>>$ poziom losowy), lecz bez kontroli nad
znakiem - perturbacja może iść w kierunku sinka lub dokładnie przeciwnym. Wzorca nie
widać gołym okiem, ale detektor rzutujący perturbację na oś sinka i mierzący energię
jest w stanie wykryć anomalię.

// ====================================================================
= Kod i środowisko
// ====================================================================

Krótko opisujemy zbudowane przez nas oprogramowanie. Całość kodu jest modularna i była wykorzystywana w blisko dwudziestu eksperymentach.

Rdzeniem jest importowalny pakiet Pythona `adversarial_sinks`, oparty na PyTorch i
PyTorch Lightning. Jego centralnym elementem jest pojedynczy _potok_ (pipeline), który przyjmuje wzorzec
sinka i funkcję straty oraz przeprowadza eksperyment od początku do końca: trening
$arrow.r$ atak $arrow.r$ metryki $arrow.r$ raport. Wokół niego:

- *`losses.py`* - każdy wypróbowany mechanizm jako wymienna klasa straty
  (`AdversarialSinkLoss`, `CrossTrapLoss`, `BadNetPoisonLoss`, `SinkConfinementLoss`);
  potok jest niezależny od wyboru straty.
- *`attacks.py`* - FGSM oraz PGD ($L_2$ i $L_infinity$) przez Foolbox, z rzutowaniem
  dokładnie respektującym budżet.
- *`sink_patterns.py`* - biblioteka wzorców (pełny krzyż, `small_cross`,
  `corner_square`, `constellation`, szachownice) oraz gęste kierunki „void”; wszystkie
  zebrane i jednoznacznie nazwane na @fig-pattern-gallery.
- *`metrics.py`* - trzy metryki detekcji i statystyki per-próbka.
- sieć CNN z parametrem `base_channels` kontrolującym liczbę filtrów (a tym samym pojemność
  sieci), z normalizacją wejścia przeniesioną _do wnętrza_ sieci, tak by każda strata
  i każdy atak działały w tej samej przestrzeni pikseli $[0,1]$.

// [FIG: pattern-gallery] Reference gallery of all sink patterns, unambiguously named. Source: analysis/pattern_gallery.py -> reports/_figs/pattern_gallery.png
#figure(
	image("figures/pattern_gallery.png", width: 100%),
	caption: [
		*Wzorce sinka używane w raporcie.* Każdy szablon narysowany na płótnie $32 times 32$
		(czerwony $= +1$, niebieski $= -1$, biały $= 0$), wraz z nazwą opisową, nazwą w kodzie
		i rozmiarem nośnika $|S|$. Zwróćmy uwagę, że „pełny krzyż” to _plus_ ($+$), a nie litera X.
		Górny wiersz - wzorce lokalne i rzadkie (kwadrat w rogu, mały krzyż, konstelacja, szachownica
		w łatce); dolny - wzorce gęste (pełny krzyż, pełna szachownica, kierunek wysokiej
		częstotliwości i kierunek losowy). $|S|$ to liczba niezerowych pikseli we wszystkich trzech
		kanałach; wyznacza ona poziom losowy $|S| \/ D$ danego wzorca w metrykach.
	],
) <fig-pattern-gallery>

Dwa praktyczne ograniczenia ukształtowały całość. Po pierwsze, cały trening odbywał się wyłącznie
na CPU (bez CUDA), a składnik dopasowania wymaga gradientu drugiego rzędu, co kosztuje
$approx 2.9$ s na pakiet. Eksperymenty mają więc ograniczony rozmiar: wczesne podejścia
trenowaliśmy od zera przez kilkaset pakietów, a późniejsze - gdy dysponowaliśmy już w pełni
zbieżnym klasyfikatorem - korzystały z _dostrajania z ciepłego startu_ (warm-start): cztery epoki
po sześćdziesiąt pakietów przy współczynniku uczenia $0.01$. Wszystkie przebiegi są wznawialne
dzięki znacznikom zapisywanym na dysku. Sinka ewaluujemy zawsze w ten sam sposób: atakiem L2 PGD
o $35$–$40$ krokach, dla budżetów $epsilon in {0.5, 1.0, 2.0, 3.0}$, a trzy metryki detekcji
uśredniamy po kilkuset obrazach testowych (od jednego do kilkunastu pakietów po $128$ próbek,
zależnie od tego, jak mocno chcieliśmy ograniczyć wariancję wyniku).

// [FIG: toy-env] Orientation figure for the toy environment. Source: analysis/toy_env.py -> reports/_toy/toy_env.png
#figure(
	image("figures/toy_env.png", width: 96%),
	caption: [
		Środowisko _toy_. Po lewej: zadanie - każde wejście to punkt na płaszczyźnie,
		a wyjście jedna z dwóch klas; $2000$ punktów tworzy dwa przeplatające się półksiężyce
		o nieliniowej granicy decyzyjnej (czarna linia). Po prawej: pole gradientu wejścia (szare
		strzałki), kilka trajektorii L2-PGD (czarne, od białego kółka do czarnego „✕”) oraz
		oś sinka $s$ (zielona). PGD podąża za lokalnym gradientem; _oś sinka_ to
		jednowymiarowy kierunek, z którym chcemy ten ruch zestroić. 
		W środowisku toy widoczne jest wszystko czego nie sposób zobaczyć na CIFAR.
	],
) <fig-toy-env>

Po drugie, zbudowaliśmy osobne, w pełni zbieżne środowisko _toy_ (patrz: @fig-toy-env), które trenuje się w kilka sekund
i pozwala narysować cały krajobraz strat, pole gradientu, granicę decyzyjną oraz trajektorie ataku
na żywo. Zadanie jest celowo minimalne: _wejściem_ jest pojedynczy punkt na płaszczyźnie (para
współrzędnych, $x in RR^2$), a _wyjściem_ - jedna z dwóch klas. $2000$ punktów treningowych układa
się w dwa przeplatające się, zakrzywione pasma - po jednym na klasę - tak że granica między klasami
jest nieliniowa (klasyczny zbiór testowy _two-moons_). Ponieważ wejście jest dwuwymiarowe, mamy wgląd w każdy element: każdy punkt płaszczyzny,
wartość straty, kierunek gradientu i drogę ataku. Klasyfikatorem jest niewielka sieć MLP
(dwie warstwy ukryte po $64$ neurony).
Odpowiednikiem sinka jest tu po prostu ustalona strzałka (kierunek jednostkowy) w przestrzeni
wejścia, a nie wzorzec wizualny; atakiem ewaluacyjnym jest L2 PGD o budżecie $epsilon = 1$ i $40$
krokach, a sukcesem byłoby ułożenie się perturbacji ataku wzdłuż tej strzałki. Aby zbadać rolę
wymiarowości, to samo zadanie osadzaliśmy w przestrzeni o większym wymiarze $D$ (od $2$ do $1000$):
dwie współrzędne wciąż niosą informację o klasie, a pozostałe $D - 2$ to czysty szum nieistotny dla
etykiety. Pozwala to umieścić sink albo w podprzestrzeni, której klasyfikator _używa_ do decyzji
(„signal”), albo w takiej, na którą jest _ślepy_ - w ogóle nie korzysta z niej przy klasyfikacji
(„void”). To narzędzie okazało się bardzo istotne podczas diagnozy hipotez.

Wszystkie prace nad sinkiem poprzedziła kontrola poprawności: sprawdziliśmy, że ataki
zachowują się prawidłowo (PGD jest monotoniczne względem $epsilon$, dokładnie respektuje
budżet i jest znacznie silniejsze niż losowy szum; model jest odporny na losowy szum) oraz
że podręcznikowy backdoor BadNets @gu2017badnets trenuje się poprawnie w naszym
środowisku (@fig-badnet) - będzie on przydatny w drugiej fazie eksperymentów.

// [FIG: badnet-demo] Sanity check that data poisoning works at all in our pipeline.
// Source: diagnostics/badnet_demo.py -> reports/_demos/badnet_demo.png
#figure(
	image("figures/badnet_demo.png", width: 100%),
	caption: [
		Kontrola poprawności backdoora BadNets. Model wytrenowany ze standardowym
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

Pracę przedstawiamy chronologicznie. Zaczęliśmy
od pierwotnego celu - _zmusić atak do narysowania wybranego sinka_. Wyczerpaliśmy wszystkie sposoby,
by go osiągnąć. Z tych porażek wyłoniło się słabsze, ale _jedyne
działające_ podejście: nie zmuszać ataku do rysowania wzorca, lecz tylko _skupić jego energię
w znanej podprzestrzeni_.

== Faza 1: testowanie pierwotnego mechanizmu

Pierwszym krokiem było sprawdzenie, czy nasz pomysł w ogóle działa - czy zaproponowana funkcja
straty potrafi wysterować atak ku sinkowi. We wszystkich przebiegach tej fazy sinkiem był
pełny krzyż w kształcie plusa (+) (@fig-pattern-gallery) nakładany na obraz. Model trenowano
kompletną funkcją straty $L_"total"$ (wszystkie trzy składniki naraz, przy różnych wartościach siły
dopasowania $alpha$), a skuteczność sterowania oceniano atakiem L2 PGD. Zanim jednak mogliśmy
cokolwiek ocenić, trzeba było doprowadzić samą funkcję straty do działania: trzy strukturalne
błędy po cichu ją neutralizowały:

- *Niezgodność przestrzeni normalizacji.* Zbiór danych zwracał obrazy znormalizowane
  (odjęta średnia, podzielone przez odchylenie standardowe), podczas gdy składniki
  $"clip"(0,1)$ zakładały przestrzeń $[0,1]$. Przycinanie odbywało się w złej przestrzeni,
  co zaburzało obliczanie perturbacji.

- *Błąd znaku w składniku sinka.* Składnik $L_"sink"$ powinien utrzymywać wysoką stratę
  klasyfikacji na obrazach z nałożonym sinkiem (model ma się mylić gdy sink jest obecny).
  Błąd znaku odwracał ten efekt - model był trenowany do _poprawnej_ klasyfikacji obrazów
  z sinkiem, czyli uczył się odporności na sink zamiast podatności.

- *Nieograniczony składnik ujemny.* Człon $-cal(L)_"CE"$ może rosnąć do $-infinity$
  gdy strata entropii krzyżowej rośnie bez ograniczeń, co destabilizowało trening.
  Rozwiązaniem było ograniczenie (margin clamp) - składnik przestaje działać gdy strata
  jest już wystarczająco wysoka.

Gdy mechanizm wreszcie działał, ujawnił się kolejny problem. Przy $alpha = 1.0$ składnik
$L_"align"$ utrzymywał się na poziomie $approx 0.99$ (przy skali $0$–$2$, gdzie $1$ to
prostopadłość) - kosinus między gradientem straty a kierunkiem sinka był więc bliski zera,
a oba kierunki niemal prostopadłe. Zwiększanie $alpha$ zmniejszało ten kąt, ale tylko kosztem
pogorszenia klasyfikacji. Gradient wejścia nie mógł jednocześnie wskazywać kierunku sinka
i kodować informacji o klasie. Ta sprzeczność przewijała się przez cały projekt.

Zanim ostatecznie porzuciliśmy dopasowanie gradientu, spróbowaliśmy jeszcze jednego
podejścia. Zamiast trenować składnik $L_"align"$ od zera - gdzie na początku dominuje
entropia krzyżowa i dopasowanie nigdy nie rusza z miejsca - wystartowaliśmy od gotowego,
wytrenowanego klasyfikatora i wprowadziliśmy dopasowanie jako _osobną fazę dostrajania_.
Pozostałe składniki straty wyłączyliśmy ($lambda_s = lambda_r = 0$), zostawiając tylko
$cal(L)_"CE" + alpha L_"align"$, by dopasowanie miało swobodę przy dużych $alpha$.
Dostrajanie od modelu o dokładności $0.69$ również zawiodło. Przy $alpha = 4$ model
zachował dokładność ($0.71$), ale `support_cos` pozostał $approx 0$. Przy $alpha = 16$
dokładność spadła do $0.52$ przy niewielkim, ujemnym `support_cos`. Przy $alpha = 64$
perturbacja wreszcie skupiła energię, ale wyłącznie kosztem załamania modelu do poziomu
losowego ($0.11$) i to skierowana _przeciwnie_ do krzyża (`support_cos` $approx -0.13$).
Żadne ustawienie nie dało jednocześnie dokładności i sterowania (@fig-phase1-tension). Pozostała jedna
wątpliwość - czy baza o dokładności $0.69$ nie była po prostu zbyt słabo wytrenowana -
wątpliwość tą roztrzyga przegląd zależności pojemności sieci w fazie 4.

// [FIG: phase1-tension] The alignment-vs-classification tension, made visible. Source: analysis/phase1_tension.py -> reports/_figs/phase1_tension.png
#figure(
	image("figures/phase1_tension.png", width: 80%),
	caption: [
		Napięcie dopasowanie–klasyfikacja. Dostrajanie składnikiem $L_"align"$ z
		wytrenowanego klasyfikatora od bazy $0.69$ na pełnym krzyżu (+), przy rosnącym $alpha$. Wraz ze wzrostem
		$alpha$ dokładność na czystych przykładach (niebieska) ostatecznie załamuje się do poziomu
		niemal losowego ($0.11$ przy $alpha = 64$), a `support_cos` (czerwona, metryka sterowania)
		_nigdy_ nie przekracza zera - jedynie schodzi w wartości ujemne. Żadne ustawienie nie daje
		naraz dobrej dokładności i dodatniego sterowania: gradient sieci względem wejścia nie może
		jednocześnie kodować klasy i wskazywać ustalonego kierunku.
	],
) <fig-phase1-tension>

== Faza 2: osadzanie sinka jako triggera (CrossTrap i BadNets)

Faza 1 pokazała, że składnika dopasowania nie da się pogodzić z klasyfikacją, więc
w fazie 2 zrezygnowaliśmy z naginania gradientu wprost i spróbowaliśmy obejścia: zamiast
budować gradient wskazujący sink, uczynić sam model _podatnym_ na krzyż - tak, by atak PGD,
szukając najtańszego sposobu oszukania modelu, sam go odnalazł. `CrossTrapLoss` trenował model tak, by nałożenie krzyża na dowolny obraz zawsze powodowało
błędną klasyfikację do tej samej, z góry wybranej klasy - niezależnie od treści obrazu.
Jednocześnie trening ortogonalny uodparniał model na wszystkie inne kierunki perturbacji. 

Po tak przebiegającym treningu model osiągał jedynie $approx 10%$ dokładności na czystych przykładach.
Diagnostyczny przegląd bez ataku pokazał, że to problem strukturalny, a nie kwestia
strojenia hiperparametrów. Optymalizator minimalizuje łączną stratę i ma tu dwa zadania:
nauczyć się poprawnie klasyfikować obrazy (trudne) oraz spełnić warunek pułapki (łatwe,
bo wystarczy zawsze odpowiadać tą samą klasą). Optymalizator wybrał skrót i całkowicie
porzucił klasyfikację na rzecz łatwiejszego celu.

`BadNetPoisonLoss` to w istocie klasyczny atak BadNets @gu2017badnets przeniesiony do
naszego scenariusza. Zamiast osobnego składnika straty po prostu _zatruwamy_ niewielki ułamek
każdego pakietu - nakładamy na obraz trigger i zmieniamy jego etykietę na docelową - podczas gdy
czysta większość pakietu chroni dokładność. Triggerem był tym razem mały kwadrat $4 times 4$
w rogu obrazu (zamiast krzyża), przełączający etykietę na klasę _samolot_. Optymalizator nie miał już łatwego skrótu, bo klasyfikacja stanowiła większość
zadania. Trening przebiegł poprawnie i model osiągnął $0.64$ dokładności na czystych
przykładach. Jednak PGD nadal nie narysował triggera: `mass_frac` utrzymywał się na
poziomie losowym lub nawet poniżej niego przy każdym budżecie ataku. Atak aktywnie
unikał pikseli triggera.

Ta porażka ujawniła najważniejszy mechanistyczny wniosek projektu - i jest on inny niż
w fazie 1. PGD jest atakiem _lokalnym_: w każdym kroku podąża za gradientem straty
w bieżącym punkcie, startując od czystego obrazu. Backdoor to natomiast odpowiedź
_nieliniowa_ - reguła „jeśli widzę trigger, zmień klasę” - która w punkcie czystego obrazu
nie zostawia żadnego gradientu prowadzącego ku triggerowi. Model jest więc na trigger
podatny, lecz atak nie ma jak go znaleźć: idzie tam, gdzie gradient jest największy, czyli
w piksele obiektu, a nie w pusty róg z triggerem, gdzie gradient jest niemal zerowy (trening
ortogonalny też tego nie zmienia - spłaszcza inne kierunki, ale żadnego nie tworzy ku sinkowi).

To _druga_ ściana, nie ta sama co w fazie 1. Tam nie udało się _zbudować_ gradientu
wskazującego sink, bo dopasowanie przegrywało z klasyfikacją; tu gradient miał powstać _sam_
z podatności modelu, lecz nieliniowy backdoor go nie tworzy. W obu przypadkach brakuje tego
samego: lokalnego gradientu ku sinkowi w punkcie, od którego atak startuje. Dlatego sterowanie
atakiem _ku miejscu_ na obrazie i sterowanie _kierunkiem_ gradientu okazują się dwiema stronami
tej samej przeszkody.

== Faza 3: ograniczanie lokalizacji zamiast kształtu

Skoro nie udało się narzucić atakowi ani konkretnego kształtu, ani kierunku, obniżyliśmy
poprzeczkę. Do wykrycia manipulacji nie potrzeba rozpoznawalnego wzorca - wystarczy, by energia
zaburzenia $delta$ koncentrowała się na z góry znanym _obszarze_ pikseli, który detektor może
sprawdzić. Trzeba przy tym pamiętać, że atak nie „wędruje” po obrazie - optymalizuje wektor
$delta$ wzdłuż gradientu straty, więc jego energia ląduje na tych pikselach, względem których
strata jest najczulsza. Stąd pomysł podpowiedziany przez fazę 2: spłaszczyć stratę (uodpornić
model) wszędzie _poza_ jednym obszarem, a w nim zostawić podatność - wtedy duży gradient, a więc
i energia $delta$, pozostaje tylko tam. Tak działał `SinkConfinementLoss`: trenował odporność na
perturbacje wszędzie poza wybranym obszarem, a w środku osadzał backdoor, by obszar pozostał
czuły na atak.

To podejście również zawiodło. `mass_frac` utrzymywał się poniżej poziomu losowego,
a `support_cos` $approx 0$. Trening ortogonalny uodparniał model poza obszarem, ale nie
tworzył żadnego przyciągania do jego środka. PGD nadal unikał narożnika.

W ten sposób wyczerpaliśmy wszystkie podejścia z rodziny „sterowania atakiem ku
konkretnemu wzorcowi lub miejscu”: dopasowanie gradientu, CrossTrap, BadNets
i maskowane ograniczanie.

== Faza 4: wykluczenie czynników zakłócających za pomocą środowiska toy i badania wpływu pojemności

Przed stwierdzeniem, że pomysł jest niewykonalny, musieliśmy wykluczyć dwa alternatywne wyjaśnienia
porażki. Pierwsze: może modele były zbyt słabo wytrenowane i osiągały za niską dokładność
($50$–$70%$), przez co wyniki były po prostu niewiarygodne. Drugie: może sieci neuronowej
brakowało pojemności, by nauczyć się wymaganego zachowania. Oba wyjaśnienia okazały się
błędne, a ich wykluczenie czyni wynik negatywny wiarygodnym.

Używana sieć CNN (ResNet) miała już
$approx 1.9$ mln parametrów, więc pojemność nigdy nie była ograniczeniem. Problemem
było zbyt krótkie trenowanie. Model z 64 filtrami w pierwszej warstwie konwolucyjnej wytrenowany do pełnej zbieżności
osiągnął dokładność $0.923$, a model z dwukrotnie większą liczbą filtrów w pierwszej
warstwie (128) osiągnął $0.921$. Wróciliśmy tu na chwilę do składnika $L_"align"$ z fazy 1 -
wyłącznie po to, by sprawdzić, czy to nie pojemność lub niedotrenowanie były winne. Dostrajanie
wyłącznie nim na każdym z tych w pełni
wytrenowanych modeli nadal dawało `support_cos` $approx 0$ ($0.002$–$0.013$) i
`energy_frac` na poziomie losowym. Ani pełne wytrenowanie, ani czterokrotnie większa
liczba filtrów nie umożliwiły sterowania kierunkiem ataku. Potwierdza to że problem
ma charakter strukturalny, a nie wynika z niewystarczającego treningu.

// [FIG: cifar-capacity] The confound-killer. Source: analysis/cifar_capacity.py -> reports/_figs/cifar_capacity.png
#figure(
	image("figures/cifar_capacity.png", width: 85%),
	caption: [
		Pojemność i zbieżność nie są ograniczeniem. Dokładność na czystych przykładach dla
		różnych konfiguracji modelu: wczesne, niedotrenowane przebiegi o szerokości 64
		($approx 0.69$) leżą znacznie poniżej tej samej architektury wytrenowanej do
		zbieżności ($0.923$), a podwojenie szerokości do $7.7$ mln parametrów nie pomaga
		($0.921$). Co istotne, dostrajanie za pomocą dopasowania gradientu na tych w pełni zbieżnych,
		pojemnych bazach _nadal_ nie steruje atakiem (`support_cos` $approx 0$), więc
		niemożność narysowania sinka jest strukturalna - nie tłumaczą jej słabe modele ani
		zbyt mało epok.
	],
) <fig-capacity>

Środowisko toy pozwoliło następnie zlokalizować przeszkodę dokładnie. Można było
podejrzewać, że eksperymenty na CIFAR nie działały po prostu dlatego, że obraz ma $3072$
wymiary, a w tak wielkiej przestrzeni trudno skupić gradient na jednym, z góry wybranym
kierunku - sink to wszak tylko jeden kierunek spośród tysięcy. Żeby to sprawdzić,
testowaliśmy modele o różnej liczbie wymiarów wejścia, od $2$ do $1000$. Okazało się,
że jakość dopasowania gradientu do sinka nie malała wraz z wymiarem - była płaska lub
nieznacznie rosnąca (@fig-toy-subspace). Duża wymiarowość CIFAR nie jest więc przyczyną
porażki.

// [FIG: toy-subspace] Dimensionality is not the obstacle. Source: analysis/toy_subspace.py -> reports/_toy/toy_subspace.png
#figure(
	image("figures/toy_subspace.png", width: 70%),
	caption: [
		Jakość dopasowania nie maleje z wymiarem. Najlepszy osiągalny $cos(delta, s)$ w funkcji
		wymiaru wejścia $D$, dla sinka umieszczonego w podprzestrzeni istotnej dla etykiety
		(„signal”) i nieistotnej („void”), w w pełni zbieżnych sieciach toy. Krzywe są płaskie
		lub rosnące, a nie malejące: to nie wysoka wymiarowość blokuje sterowanie. Podprzestrzeń
		„void” lepiej przy tym skaluje się z wymiarem - początkowo trudniejsza od „signal”,
		przewyższa ją przy większych $D$. To zalążek wyniku, który ostatecznie przenosi się na CIFAR.
	],
) <fig-toy-subspace>

== Faza 5: w środowisku toy koncentracja energii działa, lecz bez kontroli znaku

Skromniejszy cel - koncentrację energii zamiast rozpoznawalnego rysunku - postawiliśmy już
w fazie 3, lecz confinement na CIFAR zawiódł. Środowisko toy pozwoliło zrozumieć, dlaczego,
i wskazało jedyny reżim, w którym koncentracja jest naprawdę osiągalna. Kluczowa okazała się
subtelna różnica między dwoma pomysłami, które łatwo pomylić. Wmuszanie energii w wybrany
_obszar pikseli_ (jak w fazie 3) wciąż wymaga zbudowania tam dużego gradientu i przegrywa
z klasyfikacją. Czym innym jest skierowanie energii w wybrany _kierunek_ przestrzeni wejścia,
którego klasyfikator i tak nie używa: tu nie trzeba niczego budować ani z niczym walczyć, bo
ulokowanie energii w nieużywanym wymiarze nic nie kosztuje dokładności. Ten drugi wariant
środowisko toy realizuje dobrze i za darmo. Narzędziem znów jest składnik $L_"align"$, porzucony
w fazach 1–2 jako nieprzydatny do _budowania_ wzorca - tutaj pełni jednak inną rolę: nie nagina
gradientu wbrew klasyfikacji, a jedynie kieruje energię w wymiar, o który klasyfikator i tak
nie dba. Model dopasowany składnikiem
$L_"align"$ utrzymywał $10$–$40%$ całej energii ataku na osi sinka przy pełnej dokładności
klasyfikacji ($1.00$), a wzbogacenie względem poziomu losowego rosło z wymiarem: $36$ razy
przy $D=200$ i aż $187$ razy przy $D=1000$.

// [FIG: toy-win] The headline positive result in the toy. Source: analysis/toy_win.py -> reports/_toy/toy_win.png
#figure(
	image("figures/toy_win.png", width: 98%),
	caption: [
		Zmuszenie ataku do wejścia w znaną podprzestrzeń jest darmowe, odporne i rośnie z
		wymiarem. (A) Udział energii ataku na wybranej osi sinka w funkcji budżetu ataku
		$epsilon$ ($D = 200$): sieć dopasowana (dokładność $1.00$) utrzymuje $approx 0.1$–$0.4$
		całej energii ataku na pojedynczej osi w całym zakresie budżetu, znacznie powyżej linii
		losowej $1\/D = 0.005$ i wyraźnie powyżej bazy uczonej samym CE. (B) Ten sam udział
		energii _nie_ maleje, gdy wymiar wejścia $D$ rośnie od $10$ do $1000$. (C) Wzbogacenie
		względem poziomu losowego _rośnie_ więc z wymiarem - $1$#times przy $D=10$, $2$#times
		przy $50$, $36$#times przy $200$, $187$#times przy $1000$ - wszystko przy dokładności
		$0.86$–$1.00$. Koncentracja energii to realny, odporny, darmowy efekt, gdy istnieją
		naprawdę nieużywane wymiary.
	],
) <fig-toy-win>

// [FIG: toy-boundary] Concentration yes, signed drawing no. Source: analysis/toy_win_boundary.py -> reports/_toy/toy_win_boundary.png
#figure(
	image("figures/toy_win_boundary.png", width: 90%),
	caption: [
		Granica: energia się koncentruje, ale znak jest niekontrolowany. Dla tej samej
		zbieżnej sieci toy, która daje @fig-toy-win, energia na podprzestrzeni sinka pozostaje
		wysoka, lecz znakowane dopasowanie $cos(delta, s)$ spada od $+0.42$ do $-0.32$ wraz ze
		wzrostem budżetu ataku - perturbacja coraz bardziej wskazuje _przeciw_ zamierzonemu
		sinkowi. Osiągalnym efektem jest więc bezznakowa koncentracja energii (detektor wciąż
		może ją zasygnalizować), podczas gdy czysty, dominujący, poprawnie znakowany rysunek
		jest fundamentalnie poza zasięgiem.
	],
) <fig-toy-boundary>

Ta sama sieć równie wyraźnie pokazuje granicę osiągalnego efektu. Energia ataku na osi
sinka pozostawała wysoka, ale cosinus między perturbacją a sinkiem spadał od $+0.42$ do
$-0.32$ wraz ze wzrostem budżetu. Oznaczało to, że przy większym budżecie atak zaczynał
iść w kierunku przeciwnym do sinka. Atak nigdy nie kontrolował znaku - nie było wiadomo
czy narysuje wzorzec czy jego negatyw. Jest to potwierdzenie strukturalnej granicy, a
nie artefakt słabego modelu czy małej liczby wymiarów.

== Faza 6: czy efekt przenosi się na CIFAR

Środowisko toy wskazywało, że koncentracja energii powinna być osiągalna. Sprawdziliśmy
czy ten efekt przenosi się na CIFAR, przeprowadzając dwa eksperymenty na w pełni
wytrenowanym modelu osiągającym dokładność $0.92$.

W pierwszym eksperymencie sprawdziliśmy sześć różnych wzorców wizualnych: pełny krzyż,
mały krzyż, konstelację, kwadrat w rogu oraz dwie szachownice. Dla każdego z nich
zastosowaliśmy najlepszy wariant dostrajania składnikiem $L_"align"$. Żaden wzorzec nie
skoncentrował energii na CIFAR: `support_cos` mieścił się w przedziale
$[-0.012, +0.013]$, a `mass_frac` i `energy_frac` utrzymywały się na poziomie losowym,
niezależnie od tego czy wzorzec był centralny, peryferyjny, rzadki czy znakowany.
Idea sinka wizualnego nie przeniosła się na CIFAR.

// [FIG: pattern-table] No visual pattern is drawn on CIFAR. Source: analysis/cifar_pattern_table.py -> reports/_figs/pattern_table.md
#figure(
	table(
		columns: 6,
		align: (left, right, right, right, right, left),
		stroke: 0.5pt + gray,
		table.header([*wzorzec*], [*nośnik*], [*losowo*], [*dokł.*], [*najl. `mass_frac`*], [*werdykt*]),
		[krzyż (pełny)], [720], [0.234], [0.611], [0.279], [nie narysowany],
		[krzyż (pełny), align FT], [720], [0.234], [0.713], [0.289], [nie narysowany],
		[small\_cross 8×8], [84], [0.027], [0.107], [0.035], [model collapse],
		[corner\_square 4×4, BadNet], [48], [0.016], [0.642], [0.019], [nie narysowany],
		[corner\_square 4×4, +L2 AT], [48], [0.016], [0.466], [0.011], [nie narysowany],
		[corner\_square 4×4, maska AT], [48], [0.016], [0.532], [0.011], [nie narysowany],
	),
	caption: [
		Złożoność wzorca a sterowalność na CIFAR-10. Dla każdego wzorca i mechanizmu najlepszy
		`mass_frac`, jaki atak nakłada na nośnik wzorca, pozostaje na poziomie losowym $|S|\/D$
		lub poniżej, a `support_cos` (niepokazany) nigdy nie przekracza zera. Żadne rozmieszczenie - gęste czy rzadkie, centralne czy w rogu - nie zostaje narysowane; przypadki
		`corner_square` spadają nawet _poniżej_ poziomu losowego, gdyż atak unika narożnika.
	],
) <fig-pattern-table>

// [FIG: cifar-landscape] No well toward the sink on CIFAR. Source: analysis/cifar_landscape.py -> reports/_figs/cifar_landscape.png
#figure(
	image("figures/cifar_landscape.png", width: 92%),
	caption: [
		Krajobraz strat CIFAR nie ma doliny w stronę sinka. Dwuwymiarowy przekrój straty
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
	caption: [
		Co atak rysuje zamiast sinka. Kolumny pokazują, dla kilku wejść, czysty obraz,
		zamierzony szablon sinka oraz rzeczywistą perturbację PGD. Perturbacja jest zorganizowana
		wokół istotnych pikseli _obiektu_ - szum krawędzi i tekstur - i nie przypomina szablonu
		($cos approx 0$). Atak wydaje budżet tam, gdzie lokalny gradient jest największy, czyli na
		obiekcie, nigdy na wzorcu projektanta.
	],
) <fig-cifar-draws>


Potwierdziliśmy ten wynik bezpośrednio, oglądając samą funkcję straty wokół czystego obrazu.
Atak idzie tam, gdzie strata rośnie najszybciej, więc pytanie "czy sink przyciąga atak"
sprowadza się do tego, czy strata rośnie, gdy przesuwamy obraz w stronę sinka. Żeby to
zobaczyć, bierzemy dwuwymiarowy przekrój przestrzeni wejścia przez czysty obraz, rozpięty
na dwóch kierunkach: osi sinka $s$ oraz kierunku gradientu wejścia $nabla_x cal(L)$ - tym,
którym faktycznie podąża PGD. Gdyby sink był pułapką, wzdłuż jego osi widzielibyśmy dolinę
narastającej straty, ściągającą trajektorię ataku. Takiej doliny nie ma: strata jest płaska
wzdłuż osi sinka, a rośnie wyłącznie wzdłuż osi gradientu, i trajektoria PGD nigdy nie skręca
ku sinkowi (@fig-cifar-landscape). Zestawienie szablonu sinka z rzeczywistą
perturbacją PGD pokazuje, że atak ignoruje wzorzec i koncentruje się na pikselach
obiektu (@fig-cifar-draws).


Dla pewności, że ten negatywny wynik nie zależy od wyboru ataku, powtórzyliśmy go z FGSM.
Wynik był ten sam co dla PGD - `support_cos` $approx 0$ i `mass_frac` na poziomie losowym -
mimo że PGD jest znacznie silniejszym atakiem (oszukuje model na każdym obrazie, FGSM nie
zawsze). Jeden pozorny wyjątek, FGSM $L_2$ z `mass_frac` $0.356$ powyżej losowego $0.234$,
także nie jest rysowaniem wzorca. W CIFAR obiekt jest zwykle wykadrowany centralnie, więc to
_środkowe piksele najmocniej wpływają na stratę_ - ich zmiana najbardziej przesuwa decyzję
modelu.
FGSM $L_2$ kieruje energię proporcjonalnie do gradientu straty, więc odkłada jej najwięcej
właśnie w centrum; pełny krzyż przebiega przez środek, jego nośnik pokrywa się z tym obszarem
i _przypadkiem_ zbiera część tej energii, zamiast odtwarzać kształt. Potwierdza to `support_cos`
bliski zera (@fig-fgsm-table).

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
	caption: [
		FGSM i PGD są zgodne: brak rysowania, na zbieżnej sieci $0.92$. Dla obu ataków i obu norm
		`support_cos` $approx 0$, a `mass_frac` jest na poziomie losowym ($0.234$ dla krzyża). PGD
		jest znacznie silniejszy jako atak (dokładność odpornościowa $arrow.r 0$), lecz nie
		bardziej sterowalny. Podwyższona masa FGSM $L_2$ odzwierciedla istotność pikseli
		centralnych pokrywających się z krzyżem, a nie odtworzenie jego kształtu.
	],
) <fig-fgsm-table>

Drugi eksperyment przyniósł drugi z głównych wyników projektu - jedyny przypadek, w którym
koncentracja energii faktycznie przeniosła się z toy na CIFAR. Tym razem porzuciliśmy żądanie
rozpoznawalnego wzorca i umieściliśmy sink w kierunku, na który klasyfikator jest
naprawdę ślepy - czyli takim, który nie niesie żadnej informacji o klasie obrazu.
Wybraliśmy gęsty kierunek wysokoczęstotliwościowy: szachownicę gdzie sąsiednie piksele
naprzemiennie przyjmują wartości $+1$ i $-1$. Naturalne obrazy niemal nie zawierają
takich wzorców, więc klasyfikator ich nie wykorzystuje do rozpoznawania. Jako punkt
odniesienia testowaliśmy też kierunek losowy. Dla obu kierunków zbadaliśmy, jak siła
składnika $L_"align"$ (parametr $alpha$) wpływa na koncentrację energii.

Koncentracja energii wreszcie przeniosła się na CIFAR, ale tylko dla kierunku
wysokoczęstotliwościowego i tylko przy odpowiednim $alpha$. Model bez składnika
$L_"align"$ ($alpha = 0$) już naturalnie kierował nieco więcej energii ataku na ten
kierunek - $1.5$#times powyżej poziomu losowego. Zwiększanie $alpha$ podnosiło ten
efekt do szczytu $44$#times przy $alpha = 6$, a przy $alpha = 8$–$12$ utrzymywało się
na poziomie $23$–$28$#times. Dla kierunku losowego $alpha$ nie dawało żadnego efektu -
`energy_frac` pozostawał na poziomie losowym niezależnie od wartości $alpha$. Oznacza
to, że koncentracja działa tylko wtedy, gdy sink leży w kierunku na który klasyfikator
jest naprawdę ślepy.

Kosztem jest dokładność, a granica jest uderzająco niemonotoniczna. Wraz ze wzrostem $alpha$ model
najpierw się _załamuje_ ($alpha = 2 arrow.r 0.38$ dokładności, powtarzalnie dla trzech różnych _random seed_),
następnie wraca do formy przez $alpha = 4$–$12$ (szczyt $0.69$), po czym znów się załamuje
($alpha = 32 arrow.r 0.35$). Nie ma taniego optimum o wysokiej dokładności: każde dopasowanie na
tyle silne, by skoncentrować energię, degraduje model z $0.92$, a trening stabilizuje się
ponownie dopiero przy $alpha approx 8$–$12$. Nie mamy hipotezy, która mogła by wyjaśnić taką zależność. Powtarzalność dla trzech ziaren losowości (_random seed_) wyklucza
przypadek, ale mechanizm tego zjawiska pozostaje dla niejasny.

// [FIG: cifar-void] The CIFAR frontier - the second headline result. Source: analysis/cifar_void_tradeoff.py -> reports/_figs/cifar_void_tradeoff.png
#figure(
	image("figures/cifar_void_tradeoff.png", width: 98%),
	caption: [
		Koncentracja energii przenosi się na CIFAR-10 tylko dla kierunku ślepego dla etykiety i
		jest opłacana dokładnością. Po lewej: koncentracja energii (`energy_frac` względem poziomu
		losowego) w funkcji siły dopasowania $alpha$. Sink wysokoczęstotliwościowy (niebieski) rośnie
		od $1.5$#times przy $alpha=0$ do szczytu $44$#times przy $alpha=6$, utrzymując $23$–$28$#times
		przy $alpha=8$–$12$; kierunek losowy (czerwony) nigdy nie opuszcza linii losowej. Po prawej:
		te same punkty względem dokładności, odsłaniające kompromis i jego niemonotoniczność -
		dokładność spada przy $alpha=2$ ($0.38$), wraca do $0.69$ blisko $alpha=12$, po czym załamuje
		się przy $alpha=32$ ($0.35$). Użyteczny obszar pracy to $alpha approx 8$–$12$:
		$approx 23$–$28$#times poziomu losowego przy dokładności $0.67$–$0.69$.
	],
) <fig-cifar-void>

Mechanizm jest też stabilny względem różnego budżetu ataku: metryki koncentracji utrzymują się
przy zmianie $epsilon$, więc efekt nie jest artefaktem jednego, starannie dobranego budżetu
(@fig-cifar-eps).

// [FIG: cifar-eps] Sensitivity to the perturbation budget. Source: analysis/cifar_eps_curves.py -> reports/_figs/cifar_eps_curves.png
#figure(
	image("figures/cifar_eps_curves.png", width: 92%),
	caption: [
		Stabilność metryk względem budżetu ataku $epsilon$. `support_cos`, `mass_frac` i
		`energy_frac` w funkcji budżetu $L_2$, dla bazy i sieci dopasowanej. Krzywe są gładkie i
		monotoniczne, bez efektów progowych: ten (niewielki) sygnał obecny na CIFAR jest spójny w
		różnych budżetach, a nie pojawia się tylko przy jednym starannie dobranym $epsilon$.
	],
) <fig-cifar-eps>

// ====================================================================
= Werdykt
// ====================================================================

Projekt zakończył się wynikiem _częściowo negatywnym_: pierwotnego celu - zmuszenia ataku do
narysowania rozpoznawalnego sinka - nie udało się osiągnąć, lecz jego słabsza wersja, koncentracja
energii na z góry znanym kierunku, okazała się osiągalna pod ściśle określonymi warunkami. Wyniki
układają się w trzy główne wnioski.

+ *Rozpoznawalnego wizualnie sinka nie da się narysować na CIFAR.*#footnote[Dokumentacja wstepna przewidywała testy na zbiorze CIFAR-100; pozostaliśmy przy CIFAR-10 i środowisku toy. Skoro efekt zawodzi na łatwiejszym zbiorze, trudniejszy go nie uratuje.] W pięciu mechanizmach i sześciu
  wzorcach, na w pełni zbieżnej sieci $0.92$ przy szerokości do 2#times, żaden wzorzec nie został
  odtworzony (`support_cos` $approx 0$, masa na poziomie losowym). Wykluczono zarówno zbyt małą
  pojemność sieci, jak i zbyt niską wymiarowość jako możliwe przyczyny.

+ *Koncentracja energii ataku na wybrany kierunek jest możliwa, ale tylko pod pewnymi warunkami.*
  Gdy wybrany kierunek jest taki, że klasyfikator nie używa go do rozróżniania klas, atak PGD
  skierował $23$–$28$#times więcej energii na ten kierunek niż wynikałoby z przypadku. Osiągnięto to
  kosztem dokładności klasyfikacji ($0.92 arrow.r approx 0.68$), a zależność od siły składnika
  $L_"align"$ była niemonotoniczna. Dla kierunku wybranego losowo efekt nie wystąpił.

+ *Eksperymenty na środowisku toy potwierdziły mechanizm.* W prostej sieci na danych 2D, gdzie
  istniały prawdziwie nieużywane wymiary, koncentracja wyniosła $36$#times–$187$#times poziomu losowego
  niemal bez strat dokładności i była stabilna przy różnych budżetach ataku. Pokazało to, że efekt
  koncentracji jest realny - jednak nawet w tym idealnym przypadku znak perturbacji pozostał
  niekontrolowany: atak mógł skupić energię na danym kierunku, ale nie zagwarantował, że pójdzie
  w wybraną stronę.

Sprzeczność tę wyjaśnia jedno spostrzeżenie: _gradient sieci względem wejścia może albo kodować klasę,
albo wskazywać ustalony kierunek, ale nie jedno i drugie naraz_. Jeśli kierunek jest naprawdę
nieużywany do klasyfikacji, można skupić na nim energię ataku. Jeśli jednak kierunek niesie
informację o klasie, gradient musi ją kodować i nie może jednocześnie wskazywać stałego wzorca.

// ====================================================================
= Podsumowanie i kierunki przyszłych prac
// ====================================================================

Postawiliśmy sobie za cel sprawienie, by model zdradził atakującego, zmuszając ataki gradientowe
white-box do narysowania ustalonego symbolu wizualnego. Uczciwy wynik jest taki: silna wersja tego
celu jest nieosiągalna z zasadniczych powodów, podczas gdy użyteczna wersja słabsza - zmuszenie
ataku do wejścia w znaną, ślepą dla etykiety podprzestrzeń, jest osiągalna i została pokazana
zarówno w środowisku toy, jak i na CIFAR-10. Wkładem jest ostra granica między tymi dwoma.

Poniższe przyszłe kierunki traktujemy jako luźne pomysły warte sprawdzenia.

+ *Detektor.* Skoro osiągalna jest koncentracja energii, a nie rozpoznawalny
  rysunek, to naturalnym zastosowaniem jest automatyczna
  detekcja: rzutować perturbację wejścia na znany kierunek sinka i alarmować, gdy trafia tam
  za dużo energii. Opiera się to wprost na efekcie, który udało się uzyskać, więc wydaje się
  najbliższym praktycznym krokiem.

+ *Kształtowanie gradientu poza danymi treningowymi.* Wymóg wysokiej dokładności wiąże model tylko
  na prawdziwych obrazach, tymczasem PGD prowadzi atak daleko poza nie. Stąd inny, duży kierunek: utrzymać
  zachowanie modelu na prawdziwych obrazach (np. składnikiem dywergencji KL względem zamrożonego klasyfikatora,
  co chroni dokładność), a dopasowanie $L_"align"$ stosować tylko w punktach, do których prowadzi
  atak - tak, by oba cele nie rywalizowały o ten sam gradient. To pomysł na tyle obszerny, że jego
  rzetelne sprawdzenie wymaga znacznie dłuższych eksperymentów.

+ *Sink jako „uniwersalny” kierunek ataku.* W fazie 2 twarde wymuszanie konkretnej etykiety po
  nałożeniu sinka prowadziło do załamania modelu. Łagodniejszym wariantem byłoby trenować sink nie jako
  przełącznik klasy, lecz jako jeden ustalony kierunek, który _ogólnie_ podnosi stratę na wielu
  obrazach naraz - czyli uniwersalną perturbację adwersarialną. Atak miałby wtedy naturalną zachętę,
  by się z nim pokrywać, bez twardego wymuszania. Pokrewny pomysł to wąskie gardło
  architektury: ograniczyć podatność modelu do niskowymiarowej podprzestrzeni, która z konstrukcji
  zawiera sink.

+ *Ujęcie przez cechy odporne.* Fakt, że tylko kierunek ślepy dla etykiety koncentruje energię,
  łączy się wprost ze spojrzeniem na przykłady adwersarialne przez cechy odporne i nieodporne; 
  scharakteryzowanie, które podprzestrzenie są „darmowe” dla danego zbioru, pozwoliłoby
  z góry przewidzieć osiągalną koncentrację.

#v(4em)

#bibliography("bib.yaml", full: true)

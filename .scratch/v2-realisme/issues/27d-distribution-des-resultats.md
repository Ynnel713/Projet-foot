# 27d: Distribution des résultats : nuls, surprises et écarts de niveau

**Chantier :** `v2-realisme` (suggestions du propriétaire du 14/11/2026, axe « incertitude » : deux matchs ne se ressemblent jamais, sans scénario). **Priorité :** P1 (avant `v2-collectif/22c`). **Catégorie :** validation.

**Constat vérifié (14/11/2026) :** le moteur est stochastique (D-V06, D-V13) et rien n'est scripté, mais aucun indicateur ne vérifie la **quantité** d'incertitude : part des matchs nuls, fréquence des victoires de l'équipe la plus faible, distribution des scores, matchs retournés. Les repères du banc portent sur les volumes (tirs, buts, passes), pas sur l'issue.

**What to build:** une série du banc qui joue des affiches à écarts de niveau choisis (équipes égales, écart moyen, gros écart, mesuré par la note moyenne du onze) et rapporte : victoires, nuls, défaites, distribution des scores, part des matchs où l'équipe menée d'un but à la 70e ne perd pas. Repères réels à sourcer (part des nuls dans les grands championnats, victoire du favori selon l'écart de cote ou de classement), ou « non trouvé ». Le plan d'expérience précise si le moteur V2 modélise l'avantage du terrain ; sinon le repère réel choisi l'exclut (matchs à huis clos, ou écart domicile-extérieur neutralisé). Trop peu d'incertitude (le favori gagne presque toujours) ou trop (les écarts de niveau ne comptent pas) sont deux défauts. Aucun réglage ici : les écarts vont à la calibration (22c).

**Attributs :** aucun.

**Blocked by:** 01e (séries longues et intervalles).

**Bloque :** `v2-collectif/22c`.

**Status:** livré (22/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 40** |

Révisée le 22/11/2026, repères tirés des cotes ajoutés sur proposition du propriétaire : **2 h 25** (+ 45 min, extraction et tests des repères du marché), confiance moyenne. Le seuil des 2 h est dépassé mais la partie cotes est séparable ; pas de temps machine en plus.

Confiance : moyenne. Hypothèses : le banc (`scripts/measure_v2.py`) joue aujourd'hui des affiches fixées par ses propres règles, pas une affiche choisie : une option à ajouter ; l'écart de niveau se mesure par une note d'équipe dont la méthode est à proposer (par exemple la moyenne du onze sur les attributs clés de chaque poste).
Temps machine, non compté : au moins 100 matchs par niveau d'écart (environ 1 h 30 en session cloud, à confirmer).

## Tests

- **Statistiques (séries de matchs) :** trois niveaux d'écart, 100 matchs chacun : résultats et intervalles publiés dans `docs/INDICATEURS_V2.md`

## Acceptance criteria

- [x] Repères réels (sourcés ou « non trouvé ») et plan d'expérience validés par le propriétaire avant le code (22/11/2026 ; repères du marché ajoutés le même jour)
- [x] Intervalles de confiance publiés (Wilson à 95 %, `docs/INDICATEURS_V2.md` section 63) ; un écart n'est signalé que s'il dépasse l'intervalle
- [x] Aucun réglage du moteur dans ce ticket
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (test, et deux matchs de la série rejoués identiques)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (22/11/2026 : 3 499 passés, 0 ignoré, 14 désélectionnés, soit 3 488 du `10g` plus 11 tests ajoutés)

## Réalisation (22/11/2026)

**Livré.** `scripts/v2_resultats.py` (série par niveau d'écart, rapport du point de vue du favori, repères du marché avec `--cotes`, un processus neuf par match, résultats écrits au fil de l'eau) ; `tests/test_v2_resultats.py` (11 tests) ; cotes de la Ligue 1 2026/27 copiées dans `.scratch/v2-realisme/mesures/27d-cotes-F1-2627.csv` ; séries `27d-egal.json`, `27d-moyen.json`, `27d-gros.json` au même endroit. Hôtes `www.football-data.co.uk` et `football-data.co.uk` ajoutés à l'environnement `projet-foot` (accord du propriétaire).

**Mesures** (`docs/INDICATEURS_V2.md` section 63, 100 matchs par niveau ; moteur / marché, favori-nul-outsider) :
- égal : 41 / 21 / 38 % contre 35 / 27 / 39 % : aucun écart significatif ;
- moyen : 58 / 17 / 25 % contre 50 / 25 / 26 % : aucun écart significatif ;
- **gros : 81 / 7 / 12 % contre 62 / 20 / 17 %** : favori trop dominant et nuls trop rares, hors des intervalles (le favori marque 4,17 buts par match) ;
- nuls conformes partout au tirage de Poisson au nombre de buts mesuré (3,9 à 5,3 buts par match) : le déficit vient du volume de buts ;
- équipe menée d'un but à la 70e qui ne perd pas : 21 / 22 / 15 %, repère réel non trouvé.

**Transmis au `v2-collectif/22c`.** Remesurer après la baisse du nombre de buts ; viser le favori du gros écart vers 62 % sans perdre le gradient ; relancer la série juste avant et après la calibration (les chiffres d'aujourd'hui ne servent pas de base).

**Découvert en passant.** Fuite mémoire du moteur : `v2engine.movement._lerp` en `lru_cache(maxsize=None)` sur des notes réelles continues (environ 200 Mo par match dans un même processus) ; contournée dans le script, correction proposée au propriétaire comme tâche séparée.

**Écarts au plan.** Première série perdue par manque de mémoire (cause ci-dessus) ; à 2,7 buts par match, le Poisson donne 25,8 % de nuls et non environ 28 % comme annoncé lors de la proposition.

## Comments

**Clôture du 22/11/2026, passage 1.** Expert : APPROVED (empreinte calculée par erreur sur le code et le suivi documentaire ; refusée au commit quand le statut a changé). QC : VALIDÉ. Décision : VALIDÉ, non utilisable.

**Passage 2 (22/11/2026).** Empreinte sur le seul code (`scripts/v2_resultats.py`, `tests/test_v2_resultats.py`), code inchangé. Expert : APPROVED. QC : VALIDÉ (passage 1, même code). Décision de clôture : VALIDÉ. Aucune anomalie bloquante. Points facultatifs de l'expert, non appliqués : A1 (la 70e minute suppose des périodes de 45 min, faux seulement avec `--duree` d'essai), A2 (`Infinity` écrit dans le JSON pour la borne du gros écart), A3 (section 63 : les empreintes citées sont celles des séries entières, le rejeu porte sur deux matchs), A4 (attendu de la suite dans `CLAUDE.md` obsolète, hors périmètre). Observation du QC : même point que A4.

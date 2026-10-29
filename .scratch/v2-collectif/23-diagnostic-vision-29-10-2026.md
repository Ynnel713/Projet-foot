# Ticket 23, deuxième passe : diagnostic de l'effet de la Vision (29/10/2026)

Rapport au propriétaire. Rien n'est commité ; aucun fichier de code, de test, du ticket ni du système QC n'a été modifié. Toutes les mesures ont tourné hors dépôt (scripts dans le scratchpad de la session), avec les vraies fonctions du moteur remplacées dans le processus seulement.

**Verdict : prêt pour décision.** Le défaut est confirmé par le calcul et en match. La correction est simple, mais elle choisit une règle de jeu (le sens et l'ampleur de l'effet de la Vision) et des constantes produit qu'aucun document de référence ne fixe : elle vous revient.

## 1. Diagnostic

### Faits vérifiés (code, calcul, mesure)

**Comment marche le filtre.** Avant de passer, le porteur écarte un coéquipier qu'il voit « au-delà de la ligne de plus de `marge` mètres » (`v2engine/decision.py:90-104`, `is_clearly_offside`). Il juge sur une ligne **perçue** : la vraie ligne ± une erreur tirée au hasard, de 0,05 m à Vision 99 et de 0,25 m à Vision 0 (`perceived_defence_line`, `line_read_error_m`). L'arbitre, lui, siffle dès qu'un coéquipier est à plus de **0,3 m** au-delà de la vraie ligne (`OFFSIDE_TOLERANCE_M`, `offside.py:57`).

**Constantes en cause** (`v2engine/offside.py`) :
- `PASS_OFFSIDE_MARGIN_M = 0,5` (l.65) ;
- `PASS_MARGIN_REFERENCE_VISION = 63,4` (l.73) ;
- `PASS_MARGIN_MIN_M, PASS_MARGIN_MAX_M = 0,1, 1,5` (l.77) ;
- `_LINE_READ_ERROR_M = (0,05, 0,25)` (l.84).

**Effet de la formule.** `pass_margin_m(V) = 0,5 × V / 63,4`, bornée : 0,78 m à Vision 99, 0,5 m à 63,4, 0,1 m à 11.

**Pourquoi c'est inversé.** La marge n'est pas une prudence, c'est une **tolérance**, autrement dit un angle mort (le commentaire `offside.py:59-61` le dit lui-même). Plus elle est grande, plus le passeur sert des joueurs que l'arbitre va siffler. Elle grandit avec la Vision, donc **le meilleur passeur est celui qui provoque le plus de hors-jeu**. À Vision 99, tout coéquipier situé entre 0,3 et 0,78 m au-delà est servi puis sifflé. Une meilleure lecture de la ligne ne compense pas une marge plus large.

**Pas d'anticipation possible.** La décision et le départ du ballon ont lieu au même pas de temps (`match.py:198-236`), et le hors-jeu est jugé sur les positions réelles à cet instant. L'argument du ticket (l.34 : « il lit l'appel et le coupe ») n'a donc aucun support dans le moteur : un joueur au-delà de la ligne au départ est hors-jeu, quel que soit le passeur.

**Mesure en match** (20 matchs, graines 20260923 à 20260942, code actuel C0). On retrouve exactement le chiffre du ticket, **3,65 hors-jeu par match**, ce qui valide le banc de mesure. Passes jouées vers un joueur réellement hors-jeu, pour 1 000 passes, selon la Vision du passeur :

| Vision du passeur | Passes vers un hors-jeu, pour 1 000 passes | Nombre de passes |
|---|---|---|
| moins de 50 | 0 | 932 |
| 50 à 69 | 1,55 | 19 391 |
| 70 et plus | 5,52 | 10 863 |

Les meilleurs passeurs font **3,6 fois plus** d'erreurs que les moyens.

**Tests qui passent à tort** (`tests/test_v2engine_offside.py`) :
- l.220 `test_the_margin_grows_with_the_passer_vision` : il fige le sens inversé.
- l.228 `test_a_great_passer_dares_a_mate_just_beyond_the_line_that_a_poor_one_refuses` : un receveur à 0,7 m au-delà est servi à Vision 99. L'arbitre le siffle. Le test valide donc une erreur.
- l.255 `test_the_offside_filter_uses_the_passer_own_margin`, commentaire faux à la l.275 (« alors que la vraie ligne l'autoriserait »). Avec la vraie ligne à 82 m, une marge de 1,0 m et le receveur à 83,5 m, la vraie ligne refuse aussi (83,5 > 83). Le câblage reste testé par la première assertion, mais la seconde ne prouve pas ce qu'elle annonce.

**Statut et chiffres du ticket** (`.scratch/v2-collectif/issues/23-hors-jeu.md`) :
- l.9 indique « livré (28/10/2026) », alors que la deuxième passe n'a jamais été validée.
- l.14, l.20 et l.26 donnent les chiffres de la première passe sans le dire.
- l.20 annonce « 143 tests V2 », alors que le sous-ensemble `-k v2` passe aujourd'hui avec 181 tests (exécuté le 29/10/2026, mission 3 de l'audit).

### Hypothèses (plausibles, non démontrées)

- La Vision moyenne de 63,4 n'est pas pondérée et inclut les gardiens (remarque m2 du reviewer). Cela déplace un peu le point d'ancrage, pas le sens du défaut.
- Les comptes par tranche de Vision sont petits : environ 60 événements pour C0 à 70 et plus, et moins de 10 pour les tranches rares. L'ordre est net pour C0, mais les écarts fins entre options en match restent du bruit. La preuve solide est le banc discriminant (section 3).
- Le tirage de perception consomme le flux aléatoire du match (limite déjà notée au ticket, l.44). Les écarts de tirs et de buts entre options ne sont donc **pas attribuables**. Seuls le compte de hors-jeu et les passes vers un hors-jeu, par tranche, sont directement liés au filtre.

### Décisions de conception (à vous)

- Le sens de l'effet de la Vision et le rôle de la marge (angle mort humain, ou aucun) ne sont écrits nulle part. Les lignes A12 et Vision de `docs/CARTE_ATTRIBUTS_V2.md` font partie de la modification non commitée, donc non validée. `TRD_V2`, `PLAN_V2`, l'ADR 0001 et `INDICATEURS_V2` sont muets.
- Votre formule d'origine, `0,5 × (1 − Vision/100)` (ticket l.38), allait **dans le bon sens** pour les hors-jeu. Le développeur l'a inversée en la jugeant « trop prudente ». Mais, appliquée telle quelle, elle a son propre défaut : sous 0,3 m, le bon passeur refuse des passes **légales** (49 % des coéquipiers en jeu près de la ligne refusés à Vision 99, voir la colonne P0 plus bas). Elle n'est donc pas à reprendre telle quelle non plus.

## 2. Solutions comparées

Deux mesures pour chaque option :
- **Banc discriminant** (section 3) : situation identique, seule la Vision varie.
- **Match** : 20 matchs, mêmes graines.

« sifflé » est la part des passes jouées vers un joueur réellement hors-jeu. « refus » est la part des passes légales refusées.

| Option | Règle | Vision 11 (sifflé / refus) | Vision 63,4 (sifflé / refus) | Vision 99 (sifflé / refus) | Hors-jeu par match | Passes vers un hors-jeu pour 1 000 passes (<50 / 50-69 / ≥70) |
|---|---|---|---|---|---|---|
| **C0 actuel** | marge 0,5·V/63,4 (0,1 à 0,78 m) | 0,001 / 0,339 | 0,216 / 0 | **0,529** / 0 | 3,65 | 0 / 1,55 / **5,52** |
| P0 votre formule littérale | 0,5·(1−V/100) | 0,161 / 0,013 | 0 / 0,202 | 0 / **0,492** | non mesuré | non mesuré |
| S1 seuil fixe | 0,5 m pour tous, Vision = erreur de lecture | ≈0,22 / ≈0 | ≈0,22 / ≈0 | ≈0,22 / ≈0 | 3,4 | 6,51 / 2,22 / 3,46 |
| **S2 angle mort décroissant** | 0,3 + 0,2·(100−V)/36,6 : 0,79 m à V11, 0,5 m à V63,4, 0,3 m (la tolérance) à V100 | 0,537 / 0 | 0,214 / 0 | 0,014 / 0,022 | 3,1 | 6,39 / 2,42 / 2,48 |
| S3 règle pure | marge = tolérance 0,3 m, la Vision ne joue que sur la lecture | 0,059 / 0,094 | 0,031 / 0,055 | 0,011 / 0,027 | **1,7** | 1,0 / 0,51 / 0,64 |

Critères du banc :
- K1 : erreurs non croissantes avec la Vision.
- K2 : le meilleur passeur ne fait pas plus d'erreurs que le moins bon.
- K3 : erreurs encore possibles chez les bons.
- K4 : avec une lecture parfaite, le passeur suit exactement la règle de l'arbitre.

| | K1 | K2 | K3 | K4 |
|---|---|---|---|---|
| C0 | **non** (en U : 0,34 / 0,17 / 0,12 / 0,22 / 0,36 / 0,53) | **non** | oui | non |
| P0 | **non** (0,18 / 0,13 / 0,13 / 0,20 / 0,34 / 0,49) | **non** | oui | non |
| S1 | oui (plat) | oui | oui | non |
| S2 | oui | oui | oui | non (par conception : l'angle mort existe toujours, sauf à Vision 100) |
| S3 | oui | oui | oui | **oui** |

### Lecture en clair

- **S1, seuil fixe.** Avantages : le plus simple, et c'est la valeur que vous aviez validée en première passe. Limites : la Vision ne change presque rien (seule l'erreur de lecture varie, de 0,05 à 0,25 m), et tout le monde sert de la même façon jusqu'à 0,5 m, donc tout le monde est sifflé de la même façon. Côté jeu : un grand passeur ne se distingue pas d'un passeur moyen sur ce point.
- **S2, angle mort qui se resserre avec la Vision.** Avantages : il garde votre intention d'origine (« mieux on voit, moins on se trompe ») et le point validé (0,5 m pour le passeur moyen). Le meilleur passeur ne descend jamais sous la tolérance de l'arbitre, donc il ne refuse pas de passe légale par prudence. La fréquence reste dans l'ordre réel (3,1 par match contre 3,2 à 3,5). Limites : il faut valider deux constantes de plus (le plancher de 0,3 m, la pente) et le modèle d'angle mort reste une simplification. Côté jeu : les passeurs faibles provoquent des hors-jeu, les grands presque jamais.
- **S3, l'arbitre décide, la Vision lit.** Avantages : le modèle le plus propre, un seul levier par effet. Le hors-jeu sifflé ne dépend que de la règle, et la seule erreur humaine est la lecture de la ligne. Limites : le hors-jeu tombe à 1,7 par match, la moitié du réel. Pour revenir à 3,5, il faudrait agrandir l'erreur de lecture : c'est une nouvelle constante produit, à caler au ticket 22. Côté jeu : très peu de hors-jeu sur passe ; ils viendraient presque tous de la lecture.

### Recommandation : S2

Trois raisons :
1. C'est la seule option qui corrige le sens **sans** faire chuter la fréquence de hors-jeu, et elle n'exige pas de recalibrer l'erreur de lecture avant le ticket 22.
2. Elle respecte les deux choses que vous aviez déjà décidées : 0,5 m pour un passeur moyen (première passe), et un passeur qui voit mieux se trompe moins (votre formule).
3. Le changement est minimal : une seule fonction (`pass_margin_m`) et ses bornes.

S3 est la meilleure option si vous préférez un modèle pur et acceptez 1,7 hors-jeu par match jusqu'à la calibration. Ce choix vous revient.

## 3. Tests discriminants

### Exécutés (hors dépôt, dépôt inchangé)

- **Banc discriminant** : `discriminant.py` et `p0.py` dans le scratchpad.
  - Le vrai `evaluate_options`, un seul coéquipier, toujours vu (la portée de la Vision n'intervient pas), 400 tirages par point, graine 20260923.
  - Le coéquipier est placé de −0,30 à +1,20 m de la vraie ligne, et seule la Vision du porteur varie.
  - Résultats et critères K1 à K4 : tableaux ci-dessus.
- **Banc en match** : `mesure_options.py`, 4 options × 20 matchs.
  - C0 reproduit 3,65 hors-jeu par match, le chiffre du ticket.
  - L'empreinte globale du dépôt a changé pendant la mesure, mais les seuls fichiers modifiés sont des documents du ticket 25 (lignes « Blocked by » des tickets 06 à 12, `docs/PLAN_V2.md`), modifiés en dehors de cette session. Aucun fichier de `v2engine/` ni de `tests/` n'a bougé, et mes scripts n'écrivent que dans le scratchpad.
- **Tests existants** : `test_v2engine_offside`, `test_v2engine_decision`, `test_v2_indicators` et `test_v2engine_rayon_attributs` donnent 75 passés.
- **Non exécutée dans cette mission** : la suite complète.

### Proposés, à écrire après votre décision (`tests/test_v2engine_offside.py`)

Chaque test fixe la situation et ne fait varier qu'un attribut.

1. **Marge.** Remplacer `test_the_margin_grows_with_the_passer_vision` par un test qui vérifie que la marge ne croît jamais avec la Vision, ne descend jamais sous `OFFSIDE_TOLERANCE_M` et vaut 0,5 m à Vision 63,4 (pour S2).
2. **Joueur à 0,4 m au-delà.** Remplacer `test_a_great_passer_dares…` par : avec une lecture parfaite, un coéquipier à 0,4 m au-delà (donc sifflé) est servi à Vision 11 et refusé à Vision 99, et un coéquipier à 0,2 m au-delà (donc légal) est servi aux deux.
3. **Meilleur passeur non pénalisé.** Avec une lecture parfaite, aucun coéquipier légal n'est refusé, quelle que soit la Vision.
4. **Banc discriminant réduit**, sous forme de test (graine fixe, 100 tirages par point) : critères K1, K2 et K3 sur les Visions 11, 63,4 et 99.
5. **L'arbitre ne lit pas la Vision.** `offside_at_pass` donne le même jugement quelle que soit la Vision du passeur (même position, deux Visions).
6. **Câblage (l.255).** Garder la première assertion (receveur à 83,5 m, ligne perçue à 85 m). Pour la seconde, utiliser un receveur à **82,8 m** avec une ligne perçue à 80 m : la vraie ligne l'autoriserait (82,8 < 83), la ligne perçue le refuse. Le commentaire devient vrai.
7. **Test l.199** : A1 à 0,4 m au-delà, servi, porteur à Vision 60 par défaut. Il reste vrai avec S2 (marge de 0,52 m) mais devient faux avec S3. À adapter en conséquence si S3 est choisi.

Aucun de ces tests ne doit figer une valeur de fréquence de hors-jeu : ce sont des indicateurs, pas des objectifs (ticket l.19).

Remplacer les tests des points 1 et 2 revient à réécrire des tests qui figent un défaut. La règle « ne supprimer aucun test pour le faire passer » impose votre accord explicite.

## 4. Corrections proposées au ticket (non appliquées)

| Ligne | Actuel | Proposé |
|---|---|---|
| 9 | `**Status:** livré (28/10/2026)` | `**Status:** implémenté (28/10/2026) — en attente de /valider-ticket-simulafoot (deuxième passe : effet de la Vision inversé relevé le 29/10/2026, correction en attente de décision du propriétaire)` |
| 14 | « Mesuré sur 20 matchs : **3,5 par match, 1,75 par équipe** » | « Mesuré sur 20 matchs, **première passe** (e64780b) : 3,5 par match, 1,75 par équipe ; deuxième passe : 3,65 et 1,83, au-dessus de la fourchette, valeurs à remesurer après correction » |
| 20 | « 143 tests V2 verts, 173 avec l'API » | « première passe : 143 tests V2 verts, 173 avec l'API ; deuxième passe : 181 tests du sous-ensemble `-k v2` passés le 29/10/2026, suite complète à repasser après correction » |
| 26 | « **Mesure sur 20 matchs (ticket 05 → ticket 23 …)** » | même texte, avec « (première passe) » ajouté au titre |
| 34 | « Un bon passeur ose servir un coéquipier juste au-delà de la ligne (il lit l'appel et le coupe) » | à barrer ou marquer « contesté (29/10/2026) » : décision et départ ont lieu au même pas de temps, le coéquipier au-delà est sifflé |
| fin | — | nouvelle section `## Comments`, entrée du 29/10/2026 : « Audit : expert REJECTED (A1 bloquant : effet de la Vision inversé ; A2 constantes non validées), reviewer : test l.275 mal commenté, statut faux, chiffres périmés. Diagnostic confirmé par mesure (voir `.scratch/v2-collectif/23-diagnostic-vision-29-10-2026.md`). Ticket non validé. » |

Dépendent de l'option choisie : la docstring de `offside.py` (l.26-41, qui reprend 3,65 et 1,83), le commentaire l.59-61, la ligne A12/Vision de `docs/CARTE_ATTRIBUTS_V2.md` et les paragraphes l.127-129 de `docs/INDICATEURS_V2.md`.

## 5. Fichiers à modifier après décision

- `v2engine/offside.py` : `pass_margin_m`, ses bornes et sa docstring. Ce fichier n'est pas dans la liste des fichiers interdits de `CLAUDE.md`.
- `tests/test_v2engine_offside.py` : tests 1 à 7 ci-dessus.
- Le ticket 23 : section 4.
- `docs/CARTE_ATTRIBUTS_V2.md` (ligne Vision/A12) et `docs/INDICATEURS_V2.md` : nouveaux chiffres.
- Puis `Plan architecte Simulafoot.md` et `docs/TRD_MAJ.md`, selon `CLAUDE.md`.

`v2engine/decision.py` n'a pas à changer : il lit déjà `pass_margin_m` et la ligne perçue.

## 6. Décisions demandées

1. **Option** : S2 (recommandée), S3, S1, ou une autre.
2. **Constantes**, selon l'option :
   - S2 : plancher = tolérance 0,3 m, 0,5 m à Vision 63,4, environ 0,79 m à Vision 11, environ 0,85 m à Vision 0. Les bornes de 0,1 et 1,5 m disparaissent.
   - S3 : aucune nouvelle constante, mais l'amplitude de l'erreur de lecture (0,05 à 0,25 m) devient le seul réglage de fréquence.
3. **Accord** pour réécrire les deux tests qui figent l'inversion (l.220 et l.228).

## 7. Critères d'acceptation avant la nouvelle revue (expert, reviewer, QC)

1. **Banc discriminant** (même situation, graine 20260923, 400 tirages par point) :
   - erreurs totales (sifflé + refus) non croissantes avec la Vision sur 11, 30, 50, 63,4, 80 et 99, avec une tolérance de bruit de 0,01 ;
   - erreurs à Vision 99 ≤ erreurs à Vision 11 ;
   - erreurs strictement positives à 63,4 et à 99.
2. **Meilleur passeur non pénalisé** : refus de passes légales ≤ 0,03 à partir de Vision 63,4.
3. **Règle d'arbitrage inchangée** : tolérance 0,3 m, `is_offside_position` et `offside_at_pass` intacts, et le test 5 passe.
4. **En match** (20 matchs, mêmes graines) :
   - hors-jeu par match et par équipe rapportés ;
   - passes vers un hors-jeu, pour 1 000 passes, pas plus élevées à Vision 70 et plus qu'à 50-69 (écart de bruit toléré : +1,0) ;
   - les chiffres réels restent des indicateurs, pas des cibles.
5. **Suite complète** : `PYTHONHASHSEED=0 uv run pytest tests -q -p no:cacheprovider`, avec le compte comparé à celui relevé juste avant la correction. Aucun test supprimé ni désélectionné, hors réécritures accordées au point 3 de la section 6.
6. **Déterminisme** : mêmes empreintes sur deux exécutions.
7. **Documentation** : ticket, CARTE et INDICATEURS cohérents avec le code, et chiffres datés et attribués à leur passe.
8. **Clôture** : `/valider-ticket-simulafoot`, avec l'expert sur le nouveau diff (le rapport REJECTED précédent est fourni comme historique), le contrôle qualité, la décision journalisée, puis la revue `simulafoot-reviewer`.

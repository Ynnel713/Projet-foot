# 18k: Le tir manqué coûte le ballon dans la décision

**Chantier :** `v2-realisme`. **Priorité :** P0 (le volume et le mélange des tirs en dépendent ; à faire avant `v2-collectif/22c`). **Catégorie :** décision.

**Origine :** ticket 18e (12/11/2026, diagnostic de 50 matchs, `.scratch/v2-realisme/mesures/18e-zones-avant.txt`), et réserve A2 du ticket `v2-collectif/28a` (05/11/2026), reprise jusqu'ici au `v2-collectif/22a`. Par zone, la conversion est réaliste (surface 17,7 %, hors surface 4,4 % ; réel 14,7 et 4,2 %, Opta Premier League 2024-25). Le mélange ne l'est pas : 14,1 tirs hors surface par équipe et par match contre environ 4,2 dans le réel, dont 6,9 de 25 à 30 m à 0,021 d'xG ; 21,4 % des tirs dans la surface contre 68,3 %. Résultat : 18 tirs par équipe (repère 8 à 15), conversion 7,2 % (10 à 12), buts dans la surface 52 % (88 à 89).

**Constat vérifié :** `decision.evaluate_options` donne au tir la valeur `shooting.occasion_quality` (chance de but) sans contrepartie : la passe et la conduite paient la perte du ballon (`option_value`, `loss_cost`), le tir manqué ne paie rien (sortie de but, corner, ballon contré ou repoussé chez l'adversaire). Un tir à 2 % bat donc toute option de conservation dont la valeur nette est sous 0,02.

**What to build :** Donner au tir, dans la décision, la même monnaie que les autres options : chance de but, plus la valeur de ce qui suit un tir non marqué (ballon rendu à l'adversaire : sortie de but, arrêt capté ; ballon disputé : contré, repoussé ; corner), pondérée par les issues du tir (`shooting._flight_shares`). Pas de constante de pénalité arbitraire : les issues et leur valeur viennent du moteur (issues mesurées, `danger` et `loss_cost` existants).

**Hors de ce ticket :** calibration finale des tirs (`v2-collectif/22c`) ; penaltys (fautes dans la surface, `21b`, `21c`).

**Attributs :** aucun nouveau (Finishing, Long Shots, Decisions déjà en jeu).

**Blocked by :** 18e.

**Bloque :** `v2-collectif/22c`.

**Status :** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 30 min |
| Développement | 40 min |
| Tests | 30 min |
| Intégration et vérifications | 40 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : moyenne (mécanisme local ; la valeur d'un ballon rendu est déjà calculée pour la passe). À examiner pour découpage avant le code (au-delà de 2 h). Temps machine, hors total : diagnostic des zones (`18e-zones.py`, 50 matchs), série de 50 matchs, suite complète.

## Acceptance criteria

- [ ] Valeur du tir dans la décision : chance de but et suite d'un tir non marqué, avec les issues du moteur ; constantes éventuelles proposées et validées avant le code
- [ ] Scène : tir à 28 m à 0,02 d'xG contre conservation sûre : la conservation l'emporte ; tir à 8 m face au but : le tir l'emporte
- [ ] Tirs par zone avant/après sur 50 matchs (`18e-zones.py`) : tirs hors surface par équipe, part des tirs dans la surface (réel 68,3 %), conversion par zone inchangée à 2 points près
- [ ] Tirs par équipe, conversion, buts dans la surface comparés aux repères R1 et R2 ; conversion projetée au 18e avec le mélange réel 13,5 %, au-dessus de R2 : surveiller la conversion dans la surface (17,7 % hors penaltys au 18e), sans la régler ici (22c)
- [ ] Déterminisme à graine fixée ; suite complète comparée à l'attendu de `CLAUDE.md`

## Comments

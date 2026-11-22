# 02: Moyenne FM des joueurs sans Moyenne joueur

**Status:** livré (22/11/2026), validé expert + QC

**Blocked by:** —

**What to build:** `scripts/compute_moyenne_fm.py` saute aujourd'hui les lignes sans `Moyenne joueur`, or le chargeur V1 exige `Moyenne FM`. Une ligne sans `Moyenne joueur` mais avec des attributs FM reçoit la note interpolée sur la courbe (moyenne FM brute -> Moyenne FM) des joueurs existants de sa famille de table, bornée aux notes extrêmes de la famille, au pas de 0,5. Les notes des joueurs qui ont une `Moyenne joueur` sont calculées exactement comme avant.

**Estimation (travail effectif) :** analyse 10 min, développement 30 min, tests 25 min, vérifications 15 min ; total 1 h 20 ; confiance élevée.

## Critères d'acceptation
- [x] Sur le classeur actuel : Moyenne FM identique pour les 7 473 lignes avant/après (0 différence).
- [x] Ligne nouvelle : note dans [min, max] de sa famille, monotone avec la moyenne brute, au pas de 0,5.
- [x] Ligne sans Moyenne joueur ni attributs : laissée vide et signalée.
- [x] Tests unitaires de l'interpolation ; suite complète passée (3 516 passés, 14 désélectionnés, 12 min 48, arbre des tickets 01 et 02).

## Journal

22/11/2026 — implémenté.
- `scripts/compute_moyenne_fm.py` : `curve_note` (nouvelle) ; le recalage par rangs ne prend que les lignes avec Moyenne joueur ; les autres lignes avec attributs sont placées sur la courbe de leur famille (courbe calculée une fois par famille).
- Mesure sur le classeur réel, ancienne et nouvelle version lancées sur deux copies : 7 473 lignes, **0 différence** de Moyenne FM (et 0 avec le classeur commité).
- Essai de bout en bout sur une copie : clones sans Moyenne joueur de Mbappé, Haaland et Rodri -> 91, 90, 90 (notes des originaux) ; ligne sans Moyenne joueur ni attributs -> laissée vide, signalée (« ! 1 joueurs ... ligne 7478 »).
- Test : `test_curve_note_places_new_players_on_existing_curve` (`tests/test_players.py`).

## Comments

22/11/2026 — expert : APPROVED (empreinte fb37c5de). QC : VALIDÉ. Clôture journalisée : VALIDÉ.
- Remarques facultatives non traitées : une ligne non calculable garde une éventuelle Moyenne FM d'une exécution précédente (A2) ; famille sans note de référence (A3, théorique).
- Durée : estimée 80 min, réelle environ 55 min (− 31 %) : analyse 5, développement 20, tests 15, vérifications 15. Écart > 30 % : la mesure avant/après (deux copies du classeur) et l'essai de bout en bout ont été plus simples que prévu, une seule passe d'expert. Temps machine hors total : suite complète partagée avec le ticket 01.

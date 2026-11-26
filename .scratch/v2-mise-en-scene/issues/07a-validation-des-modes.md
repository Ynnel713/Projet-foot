# 07a: Validation des modes de visionnage (premier passage)

**Chantier :** `v2-mise-en-scene` (audit du mode « moments clés », 26/11/2026). **Catégorie :** validation (banc seulement, moteur et modes inchangés).

**What to build:** `scripts/measure_moments.py`, sur 50 matchs (graine d'audit), lit les moments servis par l'API publique et rapporte, par mode :
1. **Durée** à ×1 par match (médiane, 10e et 90e centiles) : Moments clés autour de 5 à 7 minutes, Résumé entre 10 et 15 minutes.
2. **Couverture du Tier 1** : chaque but, penalty et grosse occasion de la trace figure dans Moments clés et dans Résumé (100 %).
3. **Pas de doublon** : 0 chevauchement, 0 paire d'ancres à moins de 5 s, 0 action comptée deux fois (but et son tir, occasion et son tir, faute et son penalty).
4. **Pas de magie** : chaque ancre est un événement réel de la trace (identifiant du journal ou entrée de `shots`, `chances`, `goals`) ; chaque début de moment est un changement de possession, une remise en jeu, la borne de construction ou une coupure entre deux moments (règle du point 4 du `01c`) ; aucune fenêtre hors de la trace ni à cheval sur deux périodes.
5. **Contexte** : chaque moment précédé de son carton de contexte, construction au moins égale au minimum du `01c`.
6. **Déterminisme** : empreintes des listes de moments identiques sur deux exécutions à graine fixée.
7. **Suspense** : aucun élément affiché pendant la lecture ne donne la durée totale du mode, le temps restant ou le nombre de moments (entrées des composants des `01f` et `01g`, captures).
8. **Résumés courts** : chaque match dont le Résumé fait moins de 10 minutes est listé (« ce match n'a produit que X moments, résumé à Y min »).

**Second passage obligatoire après la calibration** (décision du propriétaire, 26/11/2026) : les poids du `01b` et les budgets de `02` et `03` sont fixés sur le moteur d'avant `v2-collectif/22a` à `22c` et bougeront. Le même script est relancé au ticket `07b`, bloqué par `22c`. Ce ticket ne se clôt pas sans que `07b` existe dans la roadmap.

**Attributs :** aucun.

**Constantes à proposer :** aucune (critères repris des tickets 01c, 02 et 03).

**Blocked by:** 02, 03.

**Bloque :** 07b.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : l'API sert tout ce qu'il faut (01e) ; un écart trouvé ouvre un ticket et n'est pas réglé ici.
Temps machine, non compté : 50 matchs (environ 2 h 30), deux fois pour le déterminisme sur un sous-ensemble de 3 matchs.

## Acceptance criteria

- [ ] Rapport par mode : durée, couverture du Tier 1, doublons, ancres réelles, contexte, déterminisme
- [ ] Couverture du Tier 1 : 100 % ; doublons : 0 ; ancres hors trace : 0
- [ ] Suspense : 0 affichage de durée totale, temps restant ou nombre de moments ; Résumés de moins de 10 minutes listés avec leur nombre de moments
- [ ] Durées comparées aux cibles ; tout écart renvoyé à un ticket, jamais réglé ici
- [ ] `07b` présent dans la roadmap, bloqué par `v2-collectif/22c`
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

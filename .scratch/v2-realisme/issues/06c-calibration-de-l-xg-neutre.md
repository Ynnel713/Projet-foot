# 06c: Contrôle de calibration de l'xG neutre sur 500 matchs

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (l'xG neutre doit prédire les buts des tireurs moyens). **Catégorie :** validation.

**Constat vérifié :** la formule de l'xG (`shooting._XG_LOGIT`) est ajustée sur une table cible ; aucune vérification sur les tirs du moteur.

**What to build:** Sur 500 matchs (01e), courbe de calibration : taux de buts observé par tranche d'xG neutre, pour les tireurs de note moyenne. Écarts rapportés et cause identifiée (exécution, gardien, contre) ; aucun réglage dans ce ticket.

**Attributs :** aucun

**Blocked by:** 06b (Indicateurs : occasion, exécution, gardien, par attribut); 01e (Banc : séries de 500 à 2 000 matchs, parallélisées, avec intervalles de confiance); 05e (La valeur du tir dans la décision suit la résolution physique).

**Bloque :** rien.

**Status:** livré (09/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 25** |

Confiance : élevée. Hypothèses : 500 matchs disponibles en temps machine.
Temps machine, non compté : suite complète (environ 40 min) ; série de 500 matchs.

**Estimation révisée (09/11/2026, avant le code)** : 1 h 55 (+ 30 min pour les réserves A1 et A2 du 06b et la revérification de l'étalement), confiance moyenne. Temps machine, hors total : 500 matchs (environ 4 h sur 7 processus), profils Finishing et Long Shots (environ 25 min), déterminisme (environ 15 min), suite complète (environ 20 min).

**Ordre (décision du propriétaire, 09/11/2026, « Ok avec ta recommandation »)** : fait avant le 05e, comme diagnostic ; la courbe sera relancée telle quelle après le recalage du 05e.

## Critères chiffrés (posés le 09/11/2026, avant le code)

- **Courbe** : 500 matchs indépendants de ceux du 06b (indices 1000 à 1499) ; par tranche d'xG neutre (bornes 0 ; 0,03 ; 0,06 ; 0,1 ; 0,2 ; 0,35 ; 0,5), pour tous les tireurs et pour les tireurs moyens (note de tir dans [55 ; 70[, autour de la note neutre 60) : effectif, xG moyen, taux de buts observé avec intervalle à 95 % (Wilson), buts moins xG par match avec intervalle à 95 % (banc 01e). Tranche jugée calibrée si son intervalle de buts moins xG contient 0.
- **Étages** : buts moins xG = contre + exécution + gardien, exactement (test unitaire, à 1e-9 près). Contre : chance neutre hors contre (xG / (1 − chance de contre prévue)) sur les tirs non contrés, buts des tirs contrés, moins l'xG. Exécution : xG après frappe moins chance hors contre. Gardien : buts moins xG après frappe.
- **Réserve A1 du 06b** : le gain d'exécution se compare à la chance hors contre ; profils Finishing et Long Shots relancés (20 matchs chacun) ; écart 99 − 11 publié avec son erreur type.
- **Réserve A2 du 06b** : xG après frappe moins buts ventilé par tranche d'écart à la portée du gardien (bornes −0,3 ; −0,15 ; 0 ; 0,15 ; 0,3 m).
- **Étalement 0,15 m** : xG après frappe moins buts par match sur les 500 matchs, intervalle à 95 % publié ; aucun réglage dans ce ticket.
- **Jeu inchangé** : aucun fichier du moteur modifié ; déterminisme : deux exécutions de 10 matchs identiques hors temps de calcul.

## Tests

- **Statistiques (séries de matchs) :** 500 matchs : courbe de calibration avec intervalles

## Mesures (09/11/2026, `.scratch/v2-realisme/mesures/06c-*`, détail : `docs/INDICATEURS_V2.md`, §20)

- **Courbe** (500 matchs, 1000 à 1499, `06c-serie.*`) : trop plate. Tireurs moyens (11 128 tirs) : taux réel 1,3 à 2,3 fois l'xG sous 0,2, calibré entre 0,2 et 0,35, la moitié environ au-dessus de 0,35 (0,38 pour un xG moyen de 0,78). Total + 0,33 [+ 0,23 ; + 0,43] buts par match.
- **Étages** (tireurs moyens, par match) : contre − 0,05, exécution + 0,40, gardien − 0,03. L'écart vient de la résolution physique, que la formule d'évaluation ne suit pas : entrée du 05e. Contre sous-prévu au-dessus de 0,5 d'xG.
- **Réserve A1 du 06b** : exécution comparée à la chance hors contre ; profils relancés (`06c-fin*`, `06c-ls*`, mêmes tirs qu'au 06b) : 99 − 11 = + 0,148 ± 0,039 (Finishing), + 0,032 ± 0,007 (Long Shots) ; niveaux baissés d'environ 0,02, écart inchangé.
- **Réserve A2 du 06b** : arrêt déterministe (taux de buts 0 en deçà de la portée, 1 au-delà) ; xG après frappe moins buts de + 0,30 à − 0,27 par match selon la tranche d'écart : le « gain du gardien » est le lissage de l'xG après frappe.
- **Étalement 0,15 m** (graine indépendante) : − 0,066 [− 0,132 ; − 0,001] par match ; 0,20 m : + 0,039 [− 0,032 ; + 0,111] ; zéro vers 0,18 m. Non réglé (aucun réglage dans ce ticket), à proposer avec le 05e.
- **Déterminisme** (10 matchs, 1000 à 1009, deux lots de 5 joués deux fois) : `06c-det1`/`06c-det2` (1000 à 1004), 784 indicateurs identiques ; `06c-det1b`/`06c-det2b` (1005 à 1009, ajoutés après la réserve A1 de l'expert), 797 indicateurs identiques ; seul le temps de calcul diffère.
- **Suite complète** (`06c-suite.txt`) : 2 625 passés, 14 désélectionnés = 2 610 + 1 test du 06c + 14 tests d'une autre session non commités dans le même dossier (`tests/test_v2engine_trace.py` : 2, `tests/test_extract_kit_colors.py` et `tests/test_kits_extracted.py` : 12) ; attendu pour l'arbre du ticket : 2 611.
- **Facultatifs du 06b** : A4 sans objet (`shot_notes` est déjà remis à zéro à chaque match par `_reset_match`) ; A3 et A5 non traités.
- **Durée** : estimée 1 h 55, réelle environ 2 h 05 (+ 9 %, non chronométrée). Temps machine : série 440 min (le banc en affichait 240).

## Acceptance criteria

- [x] Courbe publiée avec intervalles de confiance
- [x] Écarts expliqués par étage
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

- 09/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS (empreinte 2d1f1f4c) ; QC VALIDÉ. Réserve A1 : déterminisme vérifié sur 5 matchs au lieu des 10 du critère. Corrigée sans toucher au code : matchs 1005 à 1009 joués deux fois, identiques (`06c-det1b`, `06c-det2b`).
- 09/11/2026, passage 2, clôture : expert APPROVED (même empreinte, A1 levée) ; QC VALIDÉ (observation identique, non bloquante) ; clôture VALIDÉ (journal `v2-realisme/06c/cloture`). Aucune réserve à accepter.
- Facultatifs non traités : A2, note moyenne du groupe « tireurs moyens » [55 ; 70[ à publier lors de la relance après le 05e ; A3, pas de test dédié pour le 0 des clés « …, par match » absentes dans `bench_series._per_match`.
- À surveiller au 05e (expert) : tranche d'xG [0,35 ; 0,5[ non monotone (45 tirs) ; contre sous-prévu au-dessus de 0,5 ; volume de tirs élevé (47 par match, 3,88 buts).

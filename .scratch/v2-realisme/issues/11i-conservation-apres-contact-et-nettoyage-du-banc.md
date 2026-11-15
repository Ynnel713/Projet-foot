# 11i: Conservation du ballon après un contact (T + 3 s, perte sans faute) et nettoyage du banc

**Chantier :** `v2-realisme` (remarques A1 et A2 de l'expert sur le 11e ; décision du propriétaire du 15/11/2026). **Priorité :** P1. **Catégorie :** mesure.

**Constat vérifié :** l'indicateur du 11e « porteur bousculé : ballon encore à l'équipe 1 s après » est plat (95,6 / 95,6 / 96,2 / 94,8 % selon Balance) : 1 s est trop court (un porteur déséquilibré peut garder le ballon 1 s puis le perdre 2 s plus tard), et il compte comme gardés les fautes subies et les passes en vol (`scripts/v2_indicators.py`, `Collector._close_unsettled_carriers`). Nettoyage (A1) : les porteurs encore suivis en fin de match ne sont pas effacés (`unsettled_carriers` vidé ni par `end_match` ni entre deux matchs ; au plus un cas par match).

**What to build:** Banc seulement, moteur inchangé. (1) Suivre le porteur bousculé **3 s** et tracer s'il y a eu une **perte de balle sans faute** dans la fenêtre : un adversaire récupère le ballon (tacle, interception, conduite perdue) ou le ballon sort sur une remise adverse ; une faute subie n'est pas une perte. Garder l'indicateur à 1 s pour comparaison. Par tranche de Balance, avec le délai jusqu'à sa prochaine action (passe, tir, conduite). (2) Nettoyage technique : vider (sans compter) les porteurs encore suivis à la fin de chaque match.

**Attributs :** aucun (mesure de l'effet de Balance, 12c).

**Blocked by:** aucun.

**Bloque :** rien. À faire avant ou avec le 11h si possible (les deux lisent les contacts).

**Status:** livré (15/11/2026), validé expert (avec réserve acceptée) + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 25 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 10** |

Confiance : élevée. Hypothèses : les pertes sont déjà au journal (`PERTE`) et les remises au ballon (`restart`) ; aucune constante produit (fenêtre de 3 s fixée par le propriétaire le 15/11/2026).
Temps machine, non compté : série de 50 matchs ; suite complète.

## Tests

- **Unitaires :** porteur bousculé puis taclé à 2 s : perte comptée à 3 s, pas à 1 s ; faute subie à 2 s : pas une perte ; ballon sorti sur remise adverse : perte ; fin de match avec un porteur suivi : liste vide, rien compté.
- **Statistiques (séries de matchs) :** 50 matchs : pertes sans faute à 3 s par tranche de Balance

## Acceptance criteria

- [x] Indicateur à 3 s et perte sans faute ajoutés, par tranche de Balance ; indicateur à 1 s conservé
- [x] Porteurs suivis vidés en fin de match (test)
- [x] Rapport sur 50 matchs : effet de Balance visible ou absence constatée avec IC (si absent, piste moteur proposée au propriétaire)
- [x] Indicateurs existants identiques à la série de référence (le banc n'observe que)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**15/11/2026, démarrage.** Estimation annoncée : 1 h 10 (celle du ticket). Critères chiffrés annoncés avant le code : indicateur à 3 s et perte sans faute par tranche de Balance, indicateur à 1 s conservé ; quatre scènes (taclé à 2 s : perte à 3 s, pas à 1 s ; faute subie : pas une perte ; sortie sur remise adverse : perte ; fin de match : rien compté) ; indicateurs existants identiques à la série « après » du 11k ; effet de Balance rapporté avec son intervalle.

**15/11/2026, constat sur le nettoyage (A1 du 11e).** Déjà fait dans le code : `unsettled_carriers` est réinitialisé par `Collector._reset_match`, appelé en fin de `end_match` ; les porteurs encore suivis au coup de sifflet sont donc vidés sans être comptés. Un test le prouve désormais (avec les nouvelles listes du 11i).

**15/11/2026, implémentation (banc seul, moteur inchangé).** `scripts/v2_indicators.py` : `CARRIER_LOSS_WINDOW_S` = 3 s (fenêtre fixée par le propriétaire) ; `on_unsettle` ouvre une fenêtre par porteur bousculé ; `_close_carrier_windows` (à chaque pas) clôt sur perte sans faute (adversaire porteur, ou remise en jeu adverse), sur remise pour son équipe (faute subie : pas une perte) ou à 3 s (non perdu) ; `_carrier_next_action` (en fin de match, depuis le journal des décisions) : délai jusqu'à sa première décision après le contact (passe, tir, conduite), compté si moins de 3 s. Rapport (`scripts/measure_v2.contact_report`) par tranche de Balance : perte sans faute en 3 s (part), délai avant la perte, action dans les 3 s (part), délai avant l'action. Indicateur à 1 s inchangé. Limite : l'instant du contact est celui du pas précédent du banc (0,1 s plus tôt que dans le moteur), les délais sont donc majorés de 0,1 s au plus. Tests : `tests/test_v2_indicators_conservation.py` (8).

**15/11/2026, série de 50 matchs (`docs/INDICATEURS_V2.md` section 48 ; `11i-serie.txt`).** Hors lignes nouvelles et temps de calcul, identique à `11k-apres-serie.txt` (0 ligne de différence : le banc n'observe que ; déterminisme à graine fixée, même moteur). Perte sans faute en 3 s par tranche de Balance : 16,6 % ± 3,6 (moins de 50), 14,4 % ± 1,7, 12,4 % ± 1,1, 17,1 % ± 3,6 (80+) : **aucun effet de Balance** sur la conservation ; délai avant l'action 1,15 → 0,80 s (effet du 12c visible). Lecture du code : `match._unsettle` ne touche jamais au ballon du porteur. **Décision du propriétaire** (piste moteur, absence constatée) : « Créer un ticket moteur (Recommandé) » : ticket **11n**.

**15/11/2026, durée.** Estimation 1 h 10 ; durée réelle environ 1 h 10 (analyse 10, développement 20, tests 15, intégration 25), 0 % : le nettoyage (A1) était déjà assuré par `_reset_match`, compensé par l'analyse de la série et la rédaction du 11n. Durée estimée à l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : série de 50 matchs (38 min), suite complète.

**15/11/2026, suite complète.** 3 184 passés, 0 ignoré, 14 désélectionnés (3 176 + 8) ; `CLAUDE.md` mis à jour. V1 inchangée.

**15/11/2026, passage 1 de l'expert : APPROVED_WITH_RESERVATIONS ; QC VALIDÉ ; clôture VALIDÉ** (journal, `v2-realisme/11i/cloture`, réserve acceptée). A1 [réserve] : un tir de l'équipe du porteur dans la fenêtre (arrêt, sortie de but, but) compte comme une « perte sans faute » (biais faible, égal entre tranches : conclusion inchangée) ; **acceptée par le propriétaire** : « Accepter, corriger au 11n (Recommandé) » (correctif et test reportés dans les critères du 11n). A2 [facultatif] : documentation hors des fichiers revus (suivi documentaire admis par le verrou), sans action.

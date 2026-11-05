# 05e: La valeur du tir dans la décision suit la résolution physique

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (évite de recréer l'écart corrigé au 04a, côté tir). **Catégorie :** décision.

**Constat vérifié :** la décision évalue le tir avec `occasion_quality` (`shooting.py:177`, formule analytique) ; après 05a à 05c, l'issue réelle vient de la trajectoire : les deux peuvent diverger.

**What to build:** Mesurer, sur scènes et en match, le taux de buts réel en fonction des mêmes variables que la formule (distance, angle, gardien, contreurs, pression, exécution), et ajuster la formule d'évaluation pour qu'elle reste un estimateur juste de la résolution (table de correction ou recalage des coefficients).

**Attributs :** aucun

**Blocked by:** 05b (Arrêt : le gardien atteint ou non le ballon); 05c (Contre : le défenseur touche réellement le tir); 06a (xG après frappe : la qualité d'exécution mesurée).

**Bloque :** 05g, 06c.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : faible. Hypothèses : besoin possible de 500 matchs (01e) pour une table fiable.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 500 matchs.

## Tests

- **Unitaires (scène contrôlée) :** grille de 20 positions de tir, 2 000 tirs chacune : écart chance évaluée / taux observé
- **Statistiques (séries de matchs) :** 500 matchs : courbe de calibration de la chance évaluée

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Écart chance évaluée / taux observé sous le seuil validé par tranche
- [ ] Méthode de recalage documentée pour les tickets suivants
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

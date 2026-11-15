# 11i: Conservation du ballon après un contact (T + 3 s, perte sans faute) et nettoyage du banc

**Chantier :** `v2-realisme` (remarques A1 et A2 de l'expert sur le 11e ; décision du propriétaire du 15/11/2026). **Priorité :** P1. **Catégorie :** mesure.

**Constat vérifié :** l'indicateur du 11e « porteur bousculé : ballon encore à l'équipe 1 s après » est plat (95,6 / 95,6 / 96,2 / 94,8 % selon Balance) : 1 s est trop court (un porteur déséquilibré peut garder le ballon 1 s puis le perdre 2 s plus tard), et il compte comme gardés les fautes subies et les passes en vol (`scripts/v2_indicators.py`, `Collector._close_unsettled_carriers`). Nettoyage (A1) : les porteurs encore suivis en fin de match ne sont pas effacés (`unsettled_carriers` vidé ni par `end_match` ni entre deux matchs ; au plus un cas par match).

**What to build:** Banc seulement, moteur inchangé. (1) Suivre le porteur bousculé **3 s** et tracer s'il y a eu une **perte de balle sans faute** dans la fenêtre : un adversaire récupère le ballon (tacle, interception, conduite perdue) ou le ballon sort sur une remise adverse ; une faute subie n'est pas une perte. Garder l'indicateur à 1 s pour comparaison. Par tranche de Balance, avec le délai jusqu'à sa prochaine action (passe, tir, conduite). (2) Nettoyage technique : vider (sans compter) les porteurs encore suivis à la fin de chaque match.

**Attributs :** aucun (mesure de l'effet de Balance, 12c).

**Blocked by:** aucun.

**Bloque :** rien. À faire avant ou avec le 11h si possible (les deux lisent les contacts).

**Status:** à faire

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

- [ ] Indicateur à 3 s et perte sans faute ajoutés, par tranche de Balance ; indicateur à 1 s conservé
- [ ] Porteurs suivis vidés en fin de match (test)
- [ ] Rapport sur 50 matchs : effet de Balance visible ou absence constatée avec IC (si absent, piste moteur proposée au propriétaire)
- [ ] Indicateurs existants identiques à la série de référence (le banc n'observe que)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

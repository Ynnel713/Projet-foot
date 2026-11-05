# 11a: Collision : la vitesse change aussi, pas seulement la position

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (deux joueurs qui se heurtent doivent ralentir). **Catégorie :** physique.

**Constat vérifié :** `match._resolve_player_collisions` (`match.py:114`) corrige les positions à moitié chacun, sans toucher les vitesses.

**What to build:** Lors d'un chevauchement, retirer aux deux joueurs la composante de vitesse dirigée l'un vers l'autre (choc mou), en plus de la correction de position.

**Attributs :** aucun

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 11b.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : élevée. Hypothèses : pas encore de masse (11b).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** deux joueurs face à face à 5 m/s : vitesses de rapprochement nulles après contact

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Vitesse de rapprochement annulée au contact (scène)
- [ ] Aucune régression des duels (suite V2)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

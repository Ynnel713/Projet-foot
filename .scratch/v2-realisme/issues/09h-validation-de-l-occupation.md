# 09h: Validation de l'occupation tactique

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (contrôle avant les styles d'équipe (13)). **Catégorie :** validation.

**Constat vérifié :** voir 09a ; aucune vue d'ensemble.

**What to build:** Rapport sur 50 matchs : occupation des couloirs, demi-espaces, écarts entre lignes, défense préventive, attaquant resté haut ; comparaison à la référence du 09a.

**Attributs :** aucun

**Blocked by:** 09b (Occuper la largeur en possession); 09c (Occuper les demi-espaces selon le rôle); 09d (Formations asymétriques); 09e (Distances entre les lignes en possession); 09g (Défense préventive : un défenseur de plus que les attaquants restés haut); 09i (Appels en arc et appels temporisés) (ajouté le 10/11/2026, audit de la roadmap).

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 15** |

Confiance : élevée. Hypothèses : lecture de la trace.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : rapport publié

## Acceptance criteria

- [ ] Rapport publié ; écarts au réel listés sans réglage
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

# 15f: Validation du jeu aérien

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (contrôle global). **Catégorie :** validation.

**Constat vérifié :** aucun indicateur aérien.

**What to build:** Indicateurs : duels aériens par match et par poste, gagnés selon l'écart de taille et de Jumping Reach, têtes cadrées, seconds ballons. Rapport sur 50 matchs.

**Attributs :** aucun

**Blocked by:** 15b (Duel aérien : taille, Jumping Reach, Strength au contact); 15c (Qualité de la tête : Heading); 15d (Dégagement défensif de la tête); 15e (Seconds ballons après un duel aérien).

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

- [ ] Rapport publié
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

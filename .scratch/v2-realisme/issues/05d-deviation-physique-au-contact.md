# 05d: Déviation du ballon au contact d'un corps

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (contres, parades et ballons repoussés doivent partir de façon plausible). **Catégorie :** physique.

**Constat vérifié :** après un contre, le ballon repart avec une déviation tirée entre -60 et +60° à la moitié de la vitesse (`match.SHOT_DEFLECTION_DEG`) ; après une parade, selon des angles tirés (`shooting.parry_velocity`) ; après un contrôle raté, ±20 à 60° (`possession.missed_control_velocity`).

**What to build:** Une fonction commune de déviation au contact : la direction de sortie dépend du point d'impact sur le corps (décalage latéral par rapport à l'axe du ballon) et d'un coefficient de restitution ; une part aléatoire bornée reste. Utilisée par le contre (05c) ; la parade et le contrôle raté peuvent l'adopter plus tard sans changer leurs tickets.

**Attributs :** aucun

**Blocked by:** 05c (Contre : le défenseur touche réellement le tir).

**Bloque :** 05g, 15e.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : restitution et dispersion proposées ; pas de rotation du ballon (14c).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** contact dans l'axe : ballon renvoyé vers le tireur ; contact excentré : déviation du côté de l'impact

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Fonction unique, testée en scène
- [ ] Contres : répartition des directions de sortie rapportée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

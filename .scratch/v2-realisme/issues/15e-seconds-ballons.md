# 15e: Seconds ballons après un duel aérien

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (beaucoup d'actions naissent du ballon qui retombe). **Catégorie :** placement.

**Constat vérifié :** voir 15a ; aucun placement pour le second ballon.

**What to build:** Les joueurs non sélectionnés (15a) se placent autour de la zone probable de retombée ; un ballon dévié par le duel part selon la déviation physique (05d).

**Attributs :** aucun

**Blocked by:** 15a (Qui attaque la trajectoire aérienne); 05d (Déviation du ballon au contact d'un corps).

**Bloque :** 15f.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 40** |

Confiance : moyenne. Hypothèses : zone de retombée estimée par la direction du duel.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** duel au milieu : un joueur de chaque équipe dans la zone de retombée

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Seconds ballons gagnés rapportés
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

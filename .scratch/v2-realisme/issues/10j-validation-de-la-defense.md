# 10j: Validation de la défense collective

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (contrôle avant les styles d'équipe). **Catégorie :** validation.

**Constat vérifié :** indicateurs défensifs existants (couverture du presseur, compacité, supériorité locale) sans zones ni responsabilités.

**What to build:** Ajouter : sorties des centraux hors zone, attaquants libres dans la surface, axe devant la surface occupé, largeur selon le côté du ballon. Rapport sur 50 matchs.

**Attributs :** aucun

**Blocked by:** 10a (Choix du presseur selon la zone et la responsabilité); 10b (Le défenseur central ne quitte sa ligne que couvert); 10c (Couverture de la profondeur derrière la ligne); 10d (Protection de l'axe : le milieu récupérateur fait écran); 10e (Coulissement : côté ballon serré, côté opposé resserré vers l'axe); 10g (Marquage dans la surface : homme ou zone); 10h (Défendre le centre en retrait); 10i (Compensation d'un trou au milieu).

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : élevée. Hypothèses : lecture de la trace.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : rapport publié

## Acceptance criteria

- [ ] Indicateurs définis et ajoutés
- [ ] Rapport publié
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
- [ ] Table de passe du 18g remesurée (coupe par adversaire, passe imprécise non perdue) et indicateur de calibration de la passe sous 5 points par tranche (50 matchs) : ce ticket change le mouvement (ajouté le 12/11/2026, revue du réalisme)

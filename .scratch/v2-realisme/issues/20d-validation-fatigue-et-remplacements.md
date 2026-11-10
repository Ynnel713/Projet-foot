# 20d: Validation de la fatigue et des remplacements : profils comparés

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P1 (la fatigue doit se voir sans rendre les joueurs inutilisables). **Catégorie :** validation.

**Constat vérifié :** aucun test ne compare aujourd'hui un joueur frais et fatigué, un titulaire fatigué et un remplaçant frais, ni un joueur très sollicité et un joueur qui économise ses efforts.

**What to build:** Rapport et tests A/B, sans réglage : (1) même joueur frais et très fatigué ; (2) deux niveaux, même fraîcheur ; (3) titulaire fatigué à la 75e contre joueur frais moins bien noté placé en scène (fabrique 01f), sans attendre la mécanique du remplacement (`v2-coach-et-gestion-de-match/05a`, qui reprendra la mesure en match) : duel de vitesse, course en profondeur, geste technique ; (4) même Stamina, joueur très sollicité contre joueur économe ; (5) équipe qui presse contre bloc bas, si 13b est livré. Physique, technique et décisions séparées. Chaînes d'événements (19b) d'au moins un but « fatigue défensive → retard → appel → occasion ».

**Attributs :** aucun

**Blocked by:** 19b, 19d, 20a, 20b, 20c, 12f.

**Bloque :** `v2-collectif/22a`.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : lecture de la trace et scènes de la fabrique (01f).
Temps machine, non compté : suite complète (environ 40 min) ; 100 matchs (comparaisons appariées, 01e).

## Tests

- **Comportementaux (profils comparés) :** les cinq comparaisons, intervalles de confiance à 95 %
- **Statistiques (séries de matchs) :** 100 matchs : écarts frais / fatigué par famille (physique, technique, décisions)

## Acceptance criteria

- [ ] Chaque comparaison dans le sens attendu, intervalles publiés
- [ ] Le remplaçant frais gagne plus souvent le duel de vitesse face au titulaire fatigué que face au même titulaire frais, sans devenir meilleur sur les gestes où sa note est plus basse
- [ ] Vitesse maximale en fin de match au-dessus d'un plancher validé : aucun joueur inutilisable
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

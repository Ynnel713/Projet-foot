# 03e: Gardien : fermer l'angle dans un face-à-face

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (les face-à-face sont les plus grosses occasions d'un match). **Catégorie :** décision.

**Constat vérifié :** aucun comportement de face-à-face : le gardien reste à sa place ; `keeper_position_factor` réduit pourtant la chance si le gardien avance sur l'axe du tir.

**What to build:** Quand un attaquant adverse a le ballon dans la surface ou en approche sans défenseur entre lui et le but, le gardien avance sur la bissectrice pour réduire l'angle, à une vitesse qui le laisse s'arrêter au moment probable du tir (pas de plongeon dans ce ticket).

**Hors de ce ticket :** plongeon dans les pieds (Bravery, ticket 17b) ; dribble du gardien (`v2-attributs-restants/10b`). le ticket `v2-attributs-restants/03b` ajoutera les tendances et notes du gardien (Rushing Out, Eccentricity, One on Ones…) sur ces mécanismes neutres ; aucun attribut de gardien ici.

**Attributs :** aucun

**Blocked by:** 03b (Gardien : placement sur la bissectrice ballon-poteaux).

**Bloque :** 03g, 17b.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : la condition « sans défenseur entre lui et le but » réutilise `shooting._covered_share`.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** attaquant seul à 16 m dans l'axe : le gardien avance ; un défenseur sur l'axe : il reste
- **Statistiques (séries de matchs) :** 50 matchs : chance moyenne des tirs de face-à-face avant / après

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] État « face-à-face » tracé
- [ ] Le gardien est arrêté (vitesse sous un seuil) au moment du tir dans la majorité des cas, mesuré
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

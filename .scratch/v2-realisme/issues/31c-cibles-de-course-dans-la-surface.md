# 31c: Cibles de course dans la surface

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026 : « il n'y a pas beaucoup de centres pour le moment dans le moteur et j'aimerais corriger ça avant de continuer le chantier des têtes »). **Priorité :** P1. **Catégorie :** placement.

**What to build:** chaque attaquant déclenché (`31b`) reçoit une zone distincte, selon le côté du ballon : premier poteau (côté du centreur), second poteau (côté opposé, dans le dos du défenseur), point de penalty ; une quatrième cible à la lisière (centre en retrait, second ballon) pour le milieu qui arrive. Une zone par joueur (pas deux sur le même point), attribution stable tant que le déclenchement dure (pas d'échanges incessants, comme la stabilité des désignés du `15a2`), zones reprises de la géométrie défensive du `10f` pour que l'attaque et la défense parlent des mêmes zones. Hors-jeu : la cible est ramenée en deçà de la ligne de l'avant-dernier défenseur tant que le centre n'est pas parti.

**Constantes à proposer avant le code :** position de chaque zone (par rapport au but et au côté du ballon), rayon, ordre d'attribution (proximité, poste), marge de hors-jeu.

**Attributs :** aucun ici (le choix de la meilleure zone selon Off the Ball est au `31d`).

**Blocked by:** `31b`. **Bloque :** `31d`, `31f`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs (environ 45 min), suite complète (environ 23 min).

## Acceptance criteria

- [ ] Constantes validées avant le code
- [ ] Scène : centre possible côté droit avec trois attaquants : un au premier poteau, un au second, un au point de penalty ; jamais deux sur la même zone ; aucun hors-jeu au départ du centre dans la scène
- [ ] Série : répartition des zones occupées au moment du centre ; centres réussis et premier contact (tête, pied) relevés
- [ ] Déterminisme à graine fixée ; suite complète au compte attendu ; durée réelle relevée

## Comments

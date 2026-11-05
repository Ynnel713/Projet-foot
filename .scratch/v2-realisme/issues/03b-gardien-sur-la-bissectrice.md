# 03b: Gardien : placement sur la bissectrice ballon-poteaux

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (la position du gardien entre déjà dans la chance de chaque tir (`keeper_position_factor`)). **Catégorie :** placement.

**Constat vérifié :** la place du gardien est fixe (coup d'envoi, axe, 5 m devant sa ligne) quelle que soit la position du ballon ; `shooting.keeper_position_factor` (`shooting.py:121`) compare pourtant sa position réelle à une position de référence sur l'axe du tir.

**What to build:** Dans l'état « placement », le gardien vise un point de la bissectrice de l'angle ballon-poteaux, à une distance de sa ligne qui dépend de la distance du ballon (court quand le ballon est proche, plus avancé quand il est loin, borné par sa surface). Il s'y déplace avec `movement.step` (inertie existante).

**Hors de ce ticket :** hauteur liée à la ligne défensive (03c). le ticket `v2-attributs-restants/03b` ajoutera les tendances et notes du gardien (Rushing Out, Eccentricity, One on Ones…) sur ces mécanismes neutres ; aucun attribut de gardien ici.

**Attributs :** aucun

**Blocked by:** 03a (Gardien : sous-système propre, fin du presseur générique).

**Bloque :** 03c, 03e, 03f, 03g, 05b.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : distance à la ligne en fonction de la distance du ballon : courbe simple à valider.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** ballon immobile en 5 points (axe, angle fermé à gauche et à droite, loin, près) : gardien à moins de 0,5 m du point visé après 3 s
- **Statistiques (séries de matchs) :** 20 matchs : écart moyen du gardien à la bissectrice au moment des tirs

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Écart à la bissectrice au moment des tirs inférieur au seuil validé dans 90 % des cas (20 matchs)
- [ ] Chance moyenne des tirs (`shot_probability`) avant / après rapportée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

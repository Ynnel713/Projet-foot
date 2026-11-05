# 03c: Gardien : hauteur selon le ballon et la ligne défensive (couverture de la profondeur)

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (l'espace dans le dos d'une ligne haute doit être couvert). **Catégorie :** placement.

**Constat vérifié :** la ligne défensive peut monter jusqu'à 35 m et plus (`bloc.py:59`, ticket 05) tandis que le gardien reste à 5 m de sa ligne : l'espace entre les deux n'est couvert par personne.

**What to build:** Quand le ballon est loin et la ligne haute, le point de placement du 03b avance vers l'espace derrière la ligne, sans dépasser une distance maximale de sa ligne (valeur validée). La hauteur suit celle de la ligne avec retard nul (pas d'attribut).

**Hors de ce ticket :** aller chercher le ballon en profondeur (03d). le ticket `v2-attributs-restants/03b` ajoutera les tendances et notes du gardien (Rushing Out, Eccentricity, One on Ones…) sur ces mécanismes neutres ; aucun attribut de gardien ici.

**Attributs :** aucun

**Blocked by:** 03b (Gardien : placement sur la bissectrice ballon-poteaux).

**Bloque :** 03d, 03g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : la hauteur de ligne est lue dans `Bloc.lines`.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** ligne à 40 m de son but, ballon au milieu : gardien plus avancé qu'avec une ligne à 20 m
- **Statistiques (séries de matchs) :** 20 matchs : distance moyenne gardien-ligne selon la hauteur de ligne

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Hauteur du gardien croissante avec la hauteur de la ligne, bornée
- [ ] Aucune perte de la bissectrice quand le ballon approche (tests du 03b toujours verts)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

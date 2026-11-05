# 10e: Coulissement : côté ballon serré, côté opposé resserré vers l'axe

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un bloc coulisse plus qu'il ne se décale en entier). **Catégorie :** placement.

**Constat vérifié :** `BLOCK_SHIFT = (0.5, 0.3)` (`bloc.py:50`) : le bloc entier se décale de 30 % du décalage du ballon en largeur, sans déformation ; aucune source pour cette valeur.

**What to build:** Sans ballon, les joueurs côté ballon suivent davantage le ballon en largeur et ceux du côté opposé rentrent vers l'axe (deux parts validées), ce qui compresse le bloc côté ballon.

**Attributs :** aucun

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 10j.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : valeurs à sourcer ; mesure de la largeur du bloc existante.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** ballon sur la touche droite : latéral gauche plus près de l'axe qu'avant ; latéral droit plus près du ballon
- **Statistiques (séries de matchs) :** 50 matchs : largeur du bloc sans ballon selon la position du ballon

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Largeur sans ballon plus faible quand le ballon est sur un côté (mesuré)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

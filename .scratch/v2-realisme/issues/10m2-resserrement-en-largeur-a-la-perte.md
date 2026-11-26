# 10m2: Resserrement du bloc en largeur à la perte

**Chantier :** `v2-realisme` (découpé de 10m le 26/11/2026, demande du propriétaire). **Priorité :** P1. **Catégorie :** placement.

**Constat vérifié :** voir 10m. Rien ne resserre le bloc en largeur à la perte. Le coulissement (10e) ne vaut qu'en défense placée.

**What to build:** À la perte, la place de référence du bloc se resserre vers l'axe, avec la même part que le coulissement de 10e, jusqu'à la défense placée où 10e prend le relais sans saut de cible. La part de resserrement est un paramètre d'équipe, lisible plus tard par le style (13c, 13j).

**Attributs :** aucun nouveau.

**Lien avec l'existant :** second morceau de 10m ; réutilise la part de 10e, sans seconde mécanique.

**Blocked by:** 10e (Coulissement) ; 10m1 (Repli en hauteur et remontée de la ligne).

**Bloque :** 10n, `v2-collectif/22b`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 25 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h 05** |

Confiance : élevée. Hypothèses : 10e livré expose sa part de coulissement ; 10m1 a déjà ouvert la cible de transition dans `bloc.py`.
Temps machine, non compté : suite complète (environ 10 min en session cloud) ; 50 matchs avant/après.

## Tests

- **Unitaires (scène contrôlée) :** perte avec un bloc large : 3 s après, largeur du bloc plus faible qu'à la perte ; passage en défense placée sans saut de la place de référence (moins de 2 m d'un tick à l'autre)
- **Statistiques (séries de matchs) :** 50 matchs : largeur du bloc 3 s après la perte ; hors-jeu et tirs de contre inchangés ou meilleurs

## Acceptance criteria

- [ ] Part de resserrement validée par le propriétaire avant le code
- [ ] Largeur du bloc 3 s après la perte inférieure à celle du moment de la perte (intervalle de confiance)
- [ ] Hors-jeu toujours au moins 1,5 par match (estimation ponctuelle, intervalle rapporté)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

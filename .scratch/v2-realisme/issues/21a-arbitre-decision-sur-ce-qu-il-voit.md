# 21a: L'arbitre décide sur ce qu'il voit : fait réel et décision séparés

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P1 (fondation de l'arbitrage et de la VAR : la VAR corrige un écart entre le fait et la décision ; sans écart, elle n'a rien à faire). **Catégorie :** arbitrage.

**Constat vérifié :** le moteur siffle ce qui s'est réellement passé : une faute tirée est toujours sifflée (`duel.attempt_tackle`, `match._foul`), le hors-jeu est jugé sur les positions réelles à 0,3 m près (`offside.py`) ; aucun arbitre ni assistant n'a de position ni d'angle de vue.

**What to build:** Un arbitre et deux assistants placés sur le terrain (l'arbitre suit l'action en diagonale, les assistants restent à hauteur de l'avant-dernier défenseur). Chaque fait arbitrable (faute, hors-jeu, sortie) devient une décision : vu ou non, jugé juste ou non, selon la distance, l'angle et les joueurs qui masquent la vue. La trace garde le fait réel et la décision ; c'est la décision qui s'applique au jeu, comme dans un vrai match.

**Attributs :** aucun

**Blocked by:** 19b.

**Bloque :** 21d, 21f, 21g ; `v2-mise-en-scene/06` ; recommandé avant `v2-attributs-restants/09a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : arbitre placé par une règle simple ; taux d'erreur sourcés (études sur les décisions arbitrales) ou « non trouvé ».
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** faute à 5 m face à l'arbitre contre faute dans son dos masquée : sifflée plus souvent
- **Unitaires (scène contrôlée) :** hors-jeu de 0,4 m : jugé juste plus souvent par un assistant aligné que décalé
- **Statistiques (séries de matchs) :** 50 matchs : part des fautes non sifflées et des hors-jeu mal jugés

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Fait et décision tracés séparément pour chaque faute et chaque hors-jeu
- [ ] Taux d'erreur dans des fourchettes sourcées ou validées
- [ ] Arbitre et assistants visibles dans la trace (positions)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

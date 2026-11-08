# 04e: Le ballon n'est plus collé au porteur

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (sans touche de balle, aucune conduite ne se dispute physiquement). **Catégorie :** physique.

**Constat vérifié :** `match.py:383` : `ball.position = holder.position` à chaque pas ; le ballon n'a ni avance ni touche.

**What to build:** Pendant une conduite, le ballon avance devant le porteur par touches : à chaque touche il part à une distance qui dépend de la vitesse et de Dribbling (touche plus courte pour un bon dribbleur), puis le porteur le rejoint. Le ballon a une position propre, visible à l'écran.

**Hors de ce ticket :** interception entre deux touches (04f).

**Attributs :** Dribbling (longueur de touche)

**Blocked by:** 04d (Vitesse de conduite selon Dribbling et la pression).

**Bloque :** 04f.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : faible. Hypothèses : interactions nombreuses avec les contrôles, les tacles et le rendu (`api/routers/v2.py`) ; à redécouper si l'analyse le montre.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** conduite rectiligne à 6 m/s : ballon devant le porteur, à une distance bornée
- **Intégration :** rendu : le ballon apparaît devant le joueur

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Le ballon a une position propre pendant la conduite
- [ ] Aucune régression sur passes, contrôles et tacles (suite V2)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
- [ ] Reprise 04d A2 : vitesse moyenne balle au pied par tranche de Dribbling (Pace égal) ajoutée au banc (`v2_indicators.py` ou `--profil Dribbling`), relevée avant et après le ticket
- [ ] Reprise 04d A1 : série de 50 matchs (tirs de près par équipe, distance au but des tirs, buts) comparée à la fourchette de `docs/INDICATEURS_V2.md` ; `CONTACT_SLOWDOWN` (0,15) proposé au propriétaire pour recalage (0,08 à 0,10) si les tirs de près en sortent

## Reprises du 04d (réserves de l'expert acceptées le 08/11/2026)

- **A1** : le joueur moyen ralentit d'environ 10 % en pratique (80 % des intervalles de conduite ont une gêne ≥ 0,5, adversaire à moins de 2,5 m), alors que le 04d visait à ne pas le déplacer. Sur 20 matchs : tirs de près par équipe 4,98 → 4,30, buts 2,95 → 2,55 (dans le bruit). La touche de balle du 04e change la conduite : la mesure à 50 matchs se fait ici, avant tout calage de constante.
- **A2** : le critère « Dribbling 99 contre 11, même Pace : vitesse moyenne balle au pied plus élevée » du 04d n'est vérifié que par un test de scène ; aucun indicateur du banc ne le mesure en match.
- Facultatif (A3) : renforcer deux tests du 04d (`test_high_dribbling_covers_more_ground_than_low_at_the_same_pace` a une assertion tautologique ; `test_a_slower_carry_reaches_less_free_space` accepte `slow is None`).

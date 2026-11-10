# 23b: Erreur d'exécution continue du centre

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`, recommandation « ticket dédié », acceptée par le propriétaire le 10/11/2026). **Priorité :** P1. **Catégorie :** moteur.

**Constat vérifié (10/11/2026) :** le moteur V2 n'a pas encore de centre exécuté : Crossing n'est lu nulle part dans `v2engine/`, et un tir est classé « centre » seulement si la passe précédente est arrivée en l'air (`match.py`). Le centre est créé par `v2-attributs-restants/01` (périmètre réduit au centre le 05/11/2026). Ce ticket fixe dès le départ comment il est exécuté, pour qu'il ne naisse pas en tout ou rien comme la passe avant le `23a`.

**What to build:** Le centre reprend la loi d'écart du `23a` et y ajoute la hauteur : le point de chute (direction et longueur) et la hauteur au point de chute sont tirés autour du centre idéal, avec un écart d'autant plus large que Crossing est bas face à la difficulté du centre (distance, pression et Composure, centre en pleine course, pied et angle de frappe). C'est ce qui fait naître naturellement le centre au troisième poteau, le centre trop près du gardien et le centre contré par le premier défenseur. La note passe par la façade (`19a`) ; aucun effet de fatigue ici (`20a`). Les types de centres (enroulé, tendu, en retrait, au ras du sol) restent au `v2-attributs-restants/11`, qui choisira le geste ; ce ticket règle seulement l'exécution, commune à tous. Tirages dans le flux nommé `PASSE`.

**Attributs :** Crossing, Composure.

**Blocked by:** 23a (loi d'écart de la passe) ; `v2-attributs-restants/01` (le centre existe).

**Bloque :** `v2-attributs-restants/11`. Le `15f` (validation du jeu aérien) gagne à voir des centres imparfaits, sans en dépendre.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : la loi d'écart du `23a` est réutilisable telle quelle, seule la hauteur s'ajoute ; le centre du `v2-attributs-restants/01` porte une hauteur de ballon (`v2-hauteur-ballon/02`) ; écarts proposés à valider, chiffre réel cherché (part des centres qui trouvent un coéquipier), « non trouvé » sinon.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs avant / après.

## Tests

- **Unitaires (scène contrôlée, `tests/scenes.py`) :** centre depuis le couloir et depuis la ligne de fond, Crossing 11 / 55 / 99, avec et sans pression, 5 000 tirages : écart du point de chute et de la hauteur croissant quand la note baisse
- **Garde (`19c`) :** Crossing 11 peut réussir un centre difficile, Crossing 99 peut en rater un facile
- **Match (50 matchs) :** centres par match, part qui atteint un coéquipier, part contrée, part captée par le gardien, avant / après

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Même loi d'écart que la passe (`23a`), plus la hauteur ; aucun « réussi ou dévié au hasard »
- [ ] Écart du point de chute et de la hauteur croissant quand Crossing baisse et quand la difficulté monte (scène, 5 000 tirages)
- [ ] Garde du `19c` tenue pour le centre
- [ ] Part des centres qui atteignent un coéquipier mesurée sur 50 matchs et comparée au repère réel (ou « non trouvé »), sans recalage compensatoire
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

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

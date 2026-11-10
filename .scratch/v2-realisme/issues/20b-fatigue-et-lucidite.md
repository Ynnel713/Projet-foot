# 20b: La fatigue dégrade la lucidité : décisions et réaction

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P1 (en fin de match, on choisit moins bien et on réagit plus tard). **Catégorie :** décision.

**Constat vérifié :** l'erreur de perception du meilleur choix (Decisions, ticket 33) et le délai de réaction (Anticipation, `anticipation.py`) sont fixes tout le match ; Concentration n'est lue nulle part dans `v2engine/`.

**What to build:** Quand la réserve baisse, le délai de réaction s'allonge et l'erreur de perception du meilleur choix grandit, selon une pente continue, sans seuil. Concentration amortit cet effet (règle R3 de la carte : un modulateur n'agit que dans sa condition, ici la fatigue). Effet sur l'erreur et le délai, jamais sur l'option envisagée.

**Attributs :** Concentration (vigilance dans la durée).

**Lien avec l'existant :** `v2-collectif/21` garde le score, la minute et les trous de vigilance après un but ; la partie « la fatigue modifie les choix » de 21 est reprise ici.

**Blocked by:** 19a, 12e.

**Bloque :** 20d ; `v2-collectif/21` ; `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : mêmes leviers que le ticket 33 et `anticipation.py`, aucune courbe nouvelle hors Concentration.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Comportementaux (profils comparés) :** Concentration 99 contre 11, réserve basse : part des choix à moins de 10 % du meilleur ; réserve pleine : aucun écart (R3)
- **Statistiques (séries de matchs) :** 50 matchs : part des meilleurs choix et délai de réaction par tranche de 15 minutes

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Lucidité en baisse mesurée avec la réserve, amortie par Concentration
- [ ] Aucun effet de Concentration à réserve pleine
- [ ] Toute note lue passe par la façade de la condition (`v2-realisme/19a`), jamais par `player_attribute` directement
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

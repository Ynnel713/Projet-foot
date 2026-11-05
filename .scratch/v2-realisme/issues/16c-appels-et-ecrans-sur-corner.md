# 16c: Corner : appels et écrans

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (se libérer du marquage au moment du centre). **Catégorie :** décision.

**Constat vérifié :** voir 16a.

**What to build:** Au signal du tireur, les attaquants font un appel vers leur zone cible ; un joueur peut faire écran à un défenseur individuel (contact du 11b, faute possible).

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/02b` : appels.

**Blocked by:** 16b (Corner : défense en zone, individuelle ou mixte); 11b (Collision asymétrique : Strength).

**Bloque :** 16g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : faible. Hypothèses : écran : risque de faute à proposer.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** écran réussi : le défenseur individuel arrive en retard au point de contact

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Appels et écrans tracés
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

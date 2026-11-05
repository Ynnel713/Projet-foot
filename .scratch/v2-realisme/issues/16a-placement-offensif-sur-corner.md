# 16a: Corner : placement offensif

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (un corner se prépare : joueurs grands dans la surface, couverture derrière). **Catégorie :** placement.

**Constat vérifié :** les remises en jeu replacent chacun dans son bloc à distance réglementaire (`restart.place`) ; aucun placement propre au corner.

**What to build:** Sur un corner, l'équipe qui attaque place ses joueurs les plus aptes au jeu aérien (15b) dans la surface selon des zones de départ, garde deux joueurs en couverture et un joueur au point de retrait.

**Attributs :** aucun

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/02b` : placement offensif.

**Blocked by:** 15a (Qui attaque la trajectoire aérienne).

**Bloque :** 16b, 16d.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Hypothèses : nombre de joueurs montés réglable (prérequis du coach/04).
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** corner : les plus grands dans la surface, deux joueurs en couverture

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Placement tracé et affiché
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

# 07e: Se réorienter avant une passe, un tir ou une conduite

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** exécution.

**Constat vérifié :** une passe ou un tir part immédiatement dans n'importe quelle direction à la décision (`match._step_ball`, branches tir et passe).

**What to build:** Une passe, un tir ou une conduite dans une direction éloignée du cap demande une rotation préalable (07a) : l'action part après ce délai ; la valeur de l'option (décision) tient compte de ce délai pour la pression subie pendant la rotation.

**Attributs :** aucun

**Blocked by:** 07a (Orientation du corps : état propre et rotation bornée).

**Bloque :** 07g, `v2-collectif/31`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : le délai s'ajoute au temps de décision existant, sans le remplacer.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** passe dans le dos du porteur : partie après le délai de rotation ; dans l'axe du corps : immédiate
- **Statistiques (séries de matchs) :** 50 matchs : passes par minute et tirs avant / après

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Délai de rotation appliqué et tracé
- [ ] Décision et exécution utilisent le même délai (test)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

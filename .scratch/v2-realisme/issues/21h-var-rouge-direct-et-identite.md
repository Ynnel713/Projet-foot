# 21h: VAR : rouge direct et erreur d'identité

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P2. **Catégorie :** arbitrage.

**Constat vérifié :** voir 21g ; les cartons arrivent avec `v2-attributs-restants/09a`.

**What to build:** La VAR examine un rouge direct non sifflé ou sifflé à tort (gravité 21b), jamais un second jaune ; elle corrige une erreur d'identité. Même séquence tracée que 21g.

**Attributs :** aucun

**Blocked by:** 21g, 21b, `v2-attributs-restants/09a`.

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : réutilise la séquence du 21g.
Temps machine, non compté : suite complète (environ 40 min) ; 200 matchs.

## Tests

- **Unitaires (scène contrôlée) :** tacle d'excès d'engagement jugé jaune : rouge après révision ; second jaune : jamais révisé

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Distinction rouge direct / second jaune vérifiée
- [ ] Erreur d'identité corrigée en scène
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

# 15d: Dégagement défensif de la tête

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (le défenseur doit éloigner le ballon, pas le remettre dans l'axe). **Catégorie :** décision.

**Constat vérifié :** voir 15b.

**What to build:** Un défenseur qui gagne un duel aérien dans sa surface dégage vers l'extérieur et loin, selon Heading (précision) et sa décision (Decisions : dégager ou remettre à un partenaire).

**Attributs :** Heading (exécution), Decisions (choix)

**Blocked by:** 15c (Qualité de la tête : Heading).

**Bloque :** 15f.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 35** |

Confiance : moyenne. Hypothèses : réutilise la passe aérienne.
Temps machine, non compté : suite complète (environ 40 min).

## Tests

- **Unitaires (scène contrôlée) :** centre dans la surface gagné par un défenseur : ballon dégagé hors de l'axe

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Direction des dégagements rapportée
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

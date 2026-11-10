# 21g: VAR : buts et penalties

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P2 (elle n'intervient que sur une erreur claire, dans son champ réel). **Catégorie :** arbitrage.

**Constat vérifié :** aucune VAR dans la V2 ; le temps additionnel en garde seulement une part de fond (`added_time.BACKGROUND_S`). Les tickets `but-refuse` et `var-intervention-favorable` concernent la V1.

**What to build:** Après chaque but, et chaque penalty sifflé ou non, la VAR remonte la phase d'attaque (chaîne 19b) : hors-jeu, faute, main de l'attaquant, ballon sorti. Elle n'intervient que si le fait réel diffère de la décision : directement pour un fait objectif (hors-jeu), après consultation de l'écran pour un fait d'appréciation (seuil « clair et évident » à proposer). Séquence tracée : vérification silencieuse, interruption, consultation, décision, reprise ; temps perdu compté dans le temps additionnel ; événements lisibles par l'écran.

**Attributs :** aucun

**Blocked by:** 21a, 21d, 21f, 19b ; `v2-attributs-restants/09a`.

**Bloque :** 21h. Alimente `v2-mise-en-scene/02` (moments VAR) sans le bloquer.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 55 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h 10** |

Confiance : moyenne. Hypothèses : la VAR voit le fait réel ; seul le seuil d'appréciation est une constante nouvelle.
Temps machine, non compté : suite complète (environ 40 min) ; 200 matchs.

## Tests

- **Unitaires (scène contrôlée) :** but après un hors-jeu non vu : annulé ; but après un contact léger jugé non fautif : confirmé
- **Statistiques (séries de matchs) :** 200 matchs : vérifications, interventions et décisions changées par match

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Champ d'intervention respecté (buts, penalties) ; aucune intervention sur une faute ordinaire
- [ ] Interventions par match dans une fourchette sourcée ou « non trouvé »
- [ ] Séquence tracée et temps perdu compté
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

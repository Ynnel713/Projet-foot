# 09i: Appels en arc et appels temporisés

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P1 (l'attaquant longe la ligne puis plonge au bon moment). **Catégorie :** décision.

**Constat vérifié :** l'attaquant règle son appel sur la ligne par `offside.clamp_to_onside` (cible ramenée en jeu) et un délai de départ (02g, Off the Ball) ; la course vers l'espace est droite : pas d'appel en arc ni de course qui attend que le porteur soit prêt.

**What to build:** Course en deux temps : arc parallèle à la ligne tant que le porteur n'est pas prêt à passer (lu sur son orientation, 07e, et son temps avant la passe), puis plongée au moment où il peut jouer. Off the Ball règle le timing (rayon existant) ; le changement de rythme vient de l'accélération déjà modélisée.

**Attributs :** Off the Ball (rayon existant).

**Blocked by:** 07e, 08e, 02g.

**Bloque :** 09h.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : porteur prêt = orienté vers le but et sans contrôle en cours.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Comportementaux (profils comparés) :** Off the Ball 99 contre 11 : part des appels lancés au moment de la passe, hors-jeu par appel
- **Statistiques (séries de matchs) :** 50 matchs : hors-jeu par match, appels en arc par match

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Appel en arc visible dans la trace (intention et trajectoire)
- [ ] Hors-jeu par appel en baisse à Off the Ball élevé
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

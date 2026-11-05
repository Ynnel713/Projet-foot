# 14a: Freinage du ballon au sol : roulement et air

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (le freinage exponentiel freine trop les ballons rapides et pas assez les lents). **Catégorie :** physique.

**Constat vérifié :** `BALL_FRICTION_PER_S = 0.6` (`possession.py:19`) : la vitesse est multipliée par 0,6 chaque seconde, soit une décélération proportionnelle à la vitesse (environ 10 m/s² à 20 m/s, 1 m/s² à 2 m/s), signalée « pas un vrai coefficient calibré » dans `match.py`.

**What to build:** Remplacer par un freinage de roulement constant plus une traînée proportionnelle au carré de la vitesse (coefficients sourcés), avec la même interface pour les calculs de passe (`possession._launch_speed`, `pass_aim`) et d'interception.

**Attributs :** aucun

**Lien avec l'existant :** à coordonner avec `v2-hauteur-ballon/02a` (à faire) : 02a ajoute la hauteur, ce ticket le freinage au sol.

**Blocked by:** 01c (Repères de calibration : sources, définitions, compatibilité avec le banc).

**Bloque :** 14b, 14d.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 05** |

Confiance : moyenne. Hypothèses : les formules inverses des passes (vitesse de départ) doivent être refaites.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** passe de 20 m : temps de trajet et vitesse d'arrivée dans la fourchette sourcée
- **Statistiques (séries de matchs) :** 50 matchs : passes et interceptions avant / après

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Coefficients sourcés
- [ ] Calculs de passe cohérents avec le nouveau freinage (tests)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

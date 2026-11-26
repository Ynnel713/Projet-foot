# 14a: Freinage du ballon au sol : roulement et air

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (le freinage exponentiel freine trop les ballons rapides et pas assez les lents). **Catégorie :** physique.

**Constat vérifié :** `BALL_FRICTION_PER_S = 0.6` (`possession.py:19`) : la vitesse est multipliée par 0,6 chaque seconde, soit une décélération proportionnelle à la vitesse (environ 10 m/s² à 20 m/s, 1 m/s² à 2 m/s), signalée « pas un vrai coefficient calibré » dans `match.py`.

**What to build:** Remplacer par un freinage de roulement constant plus une traînée proportionnelle au carré de la vitesse (coefficients sourcés), avec la même interface pour les calculs de passe (`possession._launch_speed`, `pass_aim`) et d'interception.

**Attributs :** aucun

**Lien avec l'existant :** à coordonner avec `v2-hauteur-ballon/02a` (à faire) : 02a ajoute la hauteur, ce ticket le freinage au sol.

**Exigence ajoutée le 26/11/2026 (audit Magnus, `docs/AUDIT_MAGNUS_V2.md`, section 5) :** 14a livre **le** solveur de trajectoire du ballon que réutilisera Magnus (14b1) : un module unique (pas du ballon + prédicteur qui rend la trajectoire échantillonnée), utilisé par `_step_ball` et par **tous** les sites qui prédisent aujourd'hui par formule fermée (`anticipation.meeting_point`, `loose_ball_target`, `occasion._ball_path`, `possession._launch_speed`, `max_pass_reach_m`, `pass_aim`, `decision.lost_carry_outcome`, `shooting._flight_time_s`, `_flight_distance_m`). Prédiction = pas de match au pas près (règle déjà tenue par `_flight_time_s`). Sans cela, Magnus referait ce ticket. Effet sur l'estimation : + 40 min environ (2 h 05 → 2 h 45, **provisoire, à confirmer après le découpage**, pas avant). Découpage à faire avant le code : 14a1 (module et prédicteur, loi exponentielle inchangée) puis 14a2 (nouvelle loi de freinage, mesure 50 matchs).

**Piège relevé le 26/11/2026 (calcul dans l'audit Magnus) :** les prédictions actuelles ne sont **pas** cohérentes entre elles. `meeting_point`, `loose_ball_target`, `occasion._ball_path` et `pass_aim` utilisent la formule continue `v·(f^t − 1)/ln f` ; la boucle de match avance par pas de 0,1 s (`v·dt`, puis `v·f^dt`) et va **2,58 % plus loin** à tout instant (20 m/s : 16,06 m contre 15,66 m après 1 s) ; `shooting._flight_time_s` reproduit la boucle, lui. Un prédicteur unique qui suit la boucle change donc ces quatre sites. Conséquence pour le découpage : **14a1 doit donner des empreintes identiques aux références actuelles** (sinon 14a2 ne s'isole pas) : il déplace les calculs dans le module en gardant chaque site sur sa formule actuelle (continue ou au pas), sans rien unifier ; l'alignement prédiction = pas de match, changement de jeu à part entière, va au 14a2 avec la nouvelle loi, ou dans un 14a3 si la mesure de 14a2 doit l'isoler.

**Blocked by:** 01c (Repères de calibration : sources, définitions, compatibilité avec le banc).

**Bloque :** 14b (tous ses morceaux, 14b1 d'abord : même modèle aérodynamique, même solveur), 14d.

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
- [ ] Un seul solveur de trajectoire : plus aucune formule fermée du freinage hors de ce module (recherche dans le code jointe au rapport) ; prédicteur et pas de match identiques au pas près en scène (exigence du 26/11/2026)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

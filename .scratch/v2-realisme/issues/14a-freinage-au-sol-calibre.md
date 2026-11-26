# 14a: Freinage du ballon au sol : roulement et air

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P2 (le freinage exponentiel freine trop les ballons rapides et pas assez les lents). **Catégorie :** physique.

**Constat vérifié :** `BALL_FRICTION_PER_S = 0.6` (`possession.py:19`) : la vitesse est multipliée par 0,6 chaque seconde, soit une décélération proportionnelle à la vitesse (environ 10 m/s² à 20 m/s, 1 m/s² à 2 m/s), signalée « pas un vrai coefficient calibré » dans `match.py`.

**What to build:** Remplacer par un freinage de roulement constant plus une traînée proportionnelle au carré de la vitesse (coefficients sourcés), avec la même interface pour les calculs de passe (`possession._launch_speed`, `pass_aim`) et d'interception.

**Attributs :** aucun

**Lien avec l'existant :** à coordonner avec `v2-hauteur-ballon/02a` (à faire) : 02a ajoute la hauteur, ce ticket le freinage au sol.

**Blocked by:** 01c (Repères de calibration : sources, définitions, compatibilité avec le banc).

**Bloque :** 14b, 14d.

**Status:** découpé (26/11/2026, décision du propriétaire) en `14a1-loi-de-freinage-regroupee.md` (interface, sans changement de jeu) et `14a2-roulement-et-trainee.md` (nouvelle loi, constantes validées le 26/11/2026). Ticket chapeau : ne pas l'implémenter tel quel.

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

## Comments

**26/11/2026, préparation du `v2-hauteur-ballon/02a1` (décisions du propriétaire)** :
- **Traînée** : `a = ½·ρ·Cd·A·v² / m`, ρ = 1,225 kg/m³, A = π·0,11² m², m = 0,43 kg, soit environ 0,0135·v² avec Cd = 0,25 (8,5 m/s² à 25 m/s). **Crise de traînée** à prendre en compte : Cd ≈ 0,25 au-dessus d'environ 15 m/s, ≈ 0,45 en dessous ; valeurs et vitesse de transition à sourcer et à faire valider.
- **Roulement** : décélération constante sur gazon proposée par le propriétaire entre 1,0 et 1,5 m/s² (à sourcer) ; aujourd'hui, une passe à 15 m/s s'arrête à 29 m, elle irait à 75 à 110 m.
- **Pas de double comptage** : la nouvelle loi **remplace** `BALL_FRICTION_PER_S` (au sol et en vol), elle ne s'y ajoute pas. Elle sert aussi au vol du 02a1 (durée de vol, point de chute), qui devra alors résoudre la trajectoire numériquement.
- **Périmètre** : toutes les lectures de la loi de freinage (22 lignes citent `BALL_FRICTION_PER_S`, imports et définition compris) : vitesse de passe (`decision.py:550`, `possession`), point de rencontre (`meeting_point`, `loose_ball_target`), cerveau, défense, gardien, pas du ballon.
- **Estimation à revoir** : 2 h 05 sous-estime ce périmètre. Découpage proposé à l'ouverture : **regrouper** la loi derrière une seule interface (position et instant prévus), sans changement de jeu (empreintes identiques), puis **changer** la loi (changement de jeu voulu, série complète, constantes validées).
- **Place** : après `v2-hauteur-ballon/02a2`, avant la calibration `v2-collectif/22a` (dépendance ajoutée au 22a le 26/11/2026).

**26/11/2026, constats du `v2-hauteur-ballon/02a1` (réserve A2 de l'expert)** : avec le freinage exponentiel, la durée de vol déduite de la distance (`hauteur.flight_time_s`) diverge pour les ballons longs. D'où le plafond provisoire `MAX_FLIGHT_S` = 4,5 s (sommet 24,8 m). Mesure sur 10 matchs (graines 0 à 9) : 17 % des vols plafonnés, dont plus de la moitié de ballons qui n'arrivent pas (cible médiane 46 m, vitesse médiane 22,5 m/s) et qui partent pourtant au vol maximal ; 5 % des frappes dépassent 35 m/s de vitesse totale √(vh² + vz²) (maximum 37,2), au-delà de la fourchette réelle de 18 à 35 m/s. À l'ouverture de ce ticket : la nouvelle loi doit donner une durée de vol finie pour toute passe jouable, supprimer `MAX_FLIGHT_S` (ou le justifier par une source), et borner la vitesse totale de frappe ; vérification à l'écran au `02b`.

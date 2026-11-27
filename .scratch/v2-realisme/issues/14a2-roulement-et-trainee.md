# 14a2: Freinage du ballon : roulement et traînée quadratique avec crise de traînée

**Découpé du ticket 14a le 26/11/2026** (décision du propriétaire). Contexte, constat et constats du `02a1` : `14a-freinage-au-sol-calibre.md`.

**Chantier :** `v2-realisme`. **Priorité :** P2. **Catégorie :** physique (changement de jeu voulu).

**What to build:** remplacer, dans `v2engine/freinage.py` seulement (interface du `14a1`), le freinage exponentiel par :
- **au sol** : `a = a_roul + k·v²` ;
- **en l'air** (`z > 0`) : `a = k·v²` (pas de roulement) ;
- `k = ½·ρ·Cd·A / m`, traînée **horizontale seulement** (la verticale reste balistique, `hauteur`, décision du 26/11/2026) ;
- **crise de traînée en palier** : `Cd` = 0,45 sous 15 m/s, 0,25 au-dessus ; solutions exactes par morceaux (pas d'intégration numérique pour les inverses).
Puis : supprimer `hauteur.MAX_FLIGHT_S` (durée de vol finie pour toute passe jouable avec la traînée seule), borner la vitesse totale de frappe √(vh² + vz²) à 35 m/s, réécrire les tests qui codent la loi exponentielle.

**Constantes (validées par le propriétaire le 26/11/2026)** :

| Constante | Valeur | Source |
|---|---|---|
| Roulement sur gazon `a_roul` | 1,2 m/s² | FIFA, classement des pelouses naturelles : roulé de 4,0 à 10,0 m depuis la rampe (meilleure bande) ; avec ~3,5 m/s en sortie de rampe (calcul, non sourcé), 0,6 à 1,5 m/s² ; fourchette du propriétaire 1,0 à 1,5 |
| Masse `m` | 0,43 kg | Lois du jeu (410 à 450 g) |
| Rayon | 0,11 m | Lois du jeu (circonférence 68 à 70 cm) ; `match.BALL_RADIUS_M` |
| ρ air | 1,225 kg/m³ | atmosphère standard au niveau de la mer |
| `Cd` sous-critique | 0,45 (sous 15 m/s) | Asai et al. 2007 (Sports Engineering) : crise entre Re 2,2 et 3,0·10⁵, soit 15 à 20 m/s pour D = 0,22 m |
| `Cd` sur-critique | 0,25 (dès 15 m/s) | Goff & Carré 2009 (Am. J. Phys.) : 0,25 à 0,3 sur de vraies frappes ; 0,12 à 0,16 en soufflerie sans rotation (Asai) |

Ordres de grandeur : `k` = 0,0244 (Cd 0,45) et 0,0135 (Cd 0,25) ; passe au sol à 15 m/s : arrêt vers 35 m (29 m aujourd'hui).

**Blocked by:** 14a1. **Bloque :** 14b, 14d ; `v2-collectif/22a`.

**Status:** découpé (26/11/2026, décision du propriétaire) en `14a2a-roulement-et-trainee-au-sol.md` (nouvelle loi, même loi partout, prédicteurs alignés) et `14a2b-vol-sans-roulement-et-plafonds.md` (loi en l'air, `MAX_FLIGHT_S`, borne de vitesse). Ticket chapeau.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 60 min |
| Tests unitaires et comportementaux | 40 min |
| Intégration et vérifications (série de 50 matchs, tolérance) | 40 min |
| **Total (travail effectif)** | **2 h 40** |

Confiance : moyenne. Au-delà du seuil de 2 h : à réexaminer pour découpage à l'ouverture (par exemple vol et `MAX_FLIGHT_S` à part). Temps machine, non compté : série de 50 matchs avant/après (environ 50 min), suite complète.

## Acceptance criteria

- [ ] Loi changée dans `freinage.py` seulement ; tests de cohérence du 14a1 verts sans modification
- [ ] Passe de 20 m : temps de trajet et vitesse d'arrivée dans la fourchette sourcée (test)
- [ ] Durée de vol finie pour toute passe jouable ; `MAX_FLIGHT_S` supprimé ; vitesse totale de frappe ≤ 35 m/s
- [ ] 50 matchs avant/après : passes, interceptions, buts, écarts au-delà du bruit documentés et soumis au propriétaire
- [ ] Déterminisme à graine fixée ; suite complète ; V1 inchangée
- [ ] Durée réelle relevée (rapport et `docs/agents/suivi-estimations.md`)

## Comments

**26/11/2026, reprises du 14a1 (expert)** : passer par l'interface les tests qui recalculent la loi exponentielle à la main (réserve facultative A1 du 14a1) ; fusionner `freinage.shot_travel_time_s` avec `travel_time_s` ; vérifier que `travel_time_s`, `distance_after` et `stepped_travel_time_s` restent les inverses exacts du pas du moteur.

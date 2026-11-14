# 12b: Perte de vitesse en virage

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (un changement de direction coûte de la vitesse, plus ou moins selon Agility). **Catégorie :** physique.

**Constat vérifié :** un changement de direction passe par le freinage commun (`movement.step`, branche « freine ») ; aucune limite liée au rayon de courbe.

**What to build:** La vitesse maximale dans un virage est limitée par une accélération latérale maximale qui dépend d'Agility ; un virage serré oblige à ralentir.

**Attributs :** Agility (changement de direction)

**Lien avec l'existant :** découpe (validée le 05/11/2026) de `v2-attributs-restants/07b` : changement de direction.

**Blocked by:** 12a (Freinage individualisé : Agility).

**Bloque :** 12g.

**Status:** livré (14/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : limite d'accélération latérale : valeur à sourcer.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** virage à 90° à pleine vitesse : vitesse minimale dans le virage sous la vitesse de départ
- **Comportementaux (profils comparés) :** Agility 99 contre 11 : perte plus faible

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (délégation du 13/11/2026 : « je valide automatiquement toutes tes recommandations »)
- [x] Perte de vitesse en virage mesurée en scène (virage à 90° depuis 9,44 m/s, Pace 80 : vitesse minimale 5,70 / 5,82 / 5,91 m/s à Agility 11 / 55 / 99 ; sans 12b : 5,90 / 5,96 / 6,01)
- [x] Km par joueur rapportés (12,40 km par joueur de champ, + 0,11 km, IC + 0,01 ; + 0,21, sur 30 matchs appariés)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour (Agility déjà permise dans `movement`, prévue pour 12b ; carte mise à jour)
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`12b-det1`, `12b-det2`)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` (2 948 = 2 938 + 10)

## Comments

**13/11/2026, lien avec le 07b (double comptage à éviter).** Depuis `v2-realisme/07b`, la vitesse max dépend de l'angle entre la direction voulue et le cap (`movement.direction_speed_factor` : 100 % jusqu'à 45°, 80 % à 90°, 65 % à 180°), et le cap tourne à `turn_rate_rad_s(Agility)`. Un crochet coûte donc déjà de la vitesse tant que le corps n'a pas tourné, avec Agility par la vitesse de rotation (07f). La limite d'accélération latérale de ce ticket s'ajoute au freinage et au plafond du 07b : vérifier en scène qu'un virage à 90° ne cumule pas les deux pertes au-delà du réel, ou réduire l'une quand l'autre joue.

**14/11/2026, constantes proposées et validées par délégation du propriétaire** (« je valide automatiquement toutes tes recommandations », 13/11/2026). Accélération latérale maximale selon Agility, linéaire : 4,5 m/s² à 11, 5,5 à 55, 6,5 à 99 ; aucune borne sous 2 m/s (pivot sur un appui). Ordre de grandeur réel : course en courbe sur le rond central (rayon 9,15 m) vers 7 m/s, environ 5,4 m/s² (tests de « curve sprint ») ; valeur par niveau non trouvée. Estimation annoncée au démarrage : 1 h 55 (celle du ticket).

**14/11/2026, implémentation.** `movement.limit_turn` borne, après la montée en vitesse ou le freinage, la part de la variation de vitesse perpendiculaire à la vitesse du début du pas à `lateral_max_mps2(Agility) · dt` ; la part le long de la course est gardée. Agility lue une fois par pas (freinage 12a, virage 12b, rotation 07f). Double comptage avec le 07b (réserve du ticket) : le 07b plafonne la vitesse selon l'angle entre la course voulue et le cap ; le 12b borne la courbure de la trajectoire, quel que soit le cap ; mesuré en scène, le cumul ne fait pas tomber un virage à 90° sous 2 m/s (5,8 m/s au plus bas à Agility 55).

**Constat de scène, à savoir.** À pleine vitesse, le freinage (12a, 7 m/s² répartis entre l'axe et le travers) borne déjà l'accélération latérale sous 5,5 m/s² : le 12b n'y retire que 0,1 à 0,2 m/s de vitesse minimale. Il agit surtout sur les crochets serrés à vitesse moyenne (3 à 5 m/s), où la demande latérale atteindrait 6 à 7 m/s² sans lui (test `test_the_cap_binds_on_a_sharp_cut_at_moderate_speed`). Tests : `tests/test_v2engine_virage_agility.py` (courbe, borne de `limit_turn`, virage à 90° à trois pas, Agility 99 contre 11, pas d'arrêt dans le virage, borne qui agit sur un crochet).

**14/11/2026, mesure, suite et déterminisme.** Série appariée de 30 matchs (graines 50 à 79, `bench_series`, `.scratch/v2-realisme/mesures/12b-serie.txt`) contre l'état du 12a (`12b-comparaison-12a.txt`) : km par joueur de champ 12,40, **+ 0,11 km (+ 0,01 ; + 0,21)**, les virages plus larges allongent un peu les courses ; pertes de balle + 6,3 par match (+ 0,1 ; + 12,4) ; buts + 0,2, xG − 0,06, tirs − 0,2, course au-dessus de 19,8 km/h, sprints, passes, tacles : non significatifs. 208 indicateurs significatifs sur 2 660 (7,8 % ; 5 % attendus par le hasard, 6 % au 12a) : effet réel mais petit, surtout sur la conduite serrée (intervalles sous forte gêne − 35 par match) et les appels. Suite complète : 2 948 passés, 0 ignoré, 14 désélectionnés (2 938 + 10 ; `12b-suite.txt`) ; `CLAUDE.md` mis à jour. `12b-det1` et `12b-det2` identiques hors temps de calcul. V1 inchangée.

**14/11/2026, durée.** Estimation 1 h 55 ; durée réelle environ 1 h 05 (analyse 15, développement 15, tests 20, intégration 15), − 43 % : le mécanisme s'est réduit à une borne sur la variation de vitesse, sans courbure à anticiper, et le code a été écrit pendant les attentes machine du 07g ; durée estimée à l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : série de 30 matchs, suite complète, déterminisme 2 x 2 matchs.

**14/11/2026, clôture (passage 1).** Expert : APPROVED (empreinte b69c127e). QC : VALIDÉ. Clôture journalisée : VALIDÉ. Aucune anomalie bloquante. Facultatifs de l'expert : A1, borne qui passe d'infinie à `a_lat·dt` au seuil de 2 m/s (rampe sur 1,5 à 2,5 m/s si un défaut se voit à l'écran) ; A2, docstring de `test_the_turn_does_not_stop_the_runner` à préciser (courbe large, pas un crochet) et paramètre `monkeypatch` inutilisé de `_cut` (aussi relevé par le QC) : non faits pour ne pas rouvrir la revue. À surveiller : km par joueur déjà hauts (12,4), + 0,11 ; à l'écran, crochets du porteur moins secs, sans demi-tour sur place au-dessus de 2 m/s.


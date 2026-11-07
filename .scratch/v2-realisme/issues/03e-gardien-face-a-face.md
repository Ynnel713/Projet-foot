# 03e: Gardien : fermer l'angle dans un face-à-face

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (les face-à-face sont les plus grosses occasions d'un match). **Catégorie :** décision.

**Constat vérifié :** aucun comportement de face-à-face : le gardien reste à sa place ; `keeper_position_factor` réduit pourtant la chance si le gardien avance sur l'axe du tir.

**What to build:** Quand un attaquant adverse a le ballon dans la surface ou en approche sans défenseur entre lui et le but, le gardien avance sur la bissectrice pour réduire l'angle, à une vitesse qui le laisse s'arrêter au moment probable du tir (pas de plongeon dans ce ticket).

**Hors de ce ticket :** plongeon dans les pieds (Bravery, ticket 17b) ; dribble du gardien (`v2-attributs-restants/10b`). le ticket `v2-attributs-restants/03b` ajoutera les tendances et notes du gardien (Rushing Out, Eccentricity, One on Ones…) sur ces mécanismes neutres ; aucun attribut de gardien ici.

**Attributs :** aucun

**Blocked by:** 03b (Gardien : placement sur la bissectrice ballon-poteaux).

**Bloque :** 03g, 17b.

**Status:** livré (07/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : la condition « sans défenseur entre lui et le but » réutilise `shooting._covered_share`.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** attaquant seul à 16 m dans l'axe : le gardien avance ; un défenseur sur l'axe : il reste
- **Statistiques (séries de matchs) :** 50 matchs : chance moyenne des tirs de face-à-face avant / après

## Acceptance criteria

- [x] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code (proposées par Claude, validées par délégation, voir Comments ; chiffres réels non trouvés)
- [x] État « face-à-face » tracé (`gardien.FACE_A_FACE`, raison de l'intention « face-à-face : … » ; test ; 32 épisodes par match mesurés)
- [x] Le gardien est arrêté (vitesse sous un seuil) au moment du tir dans la majorité des cas, mesuré (sous 1,5 m/s : 65,2 % → 92,1 % des tirs de face-à-face, 50 matchs)
- [x] Durée réelle relevée
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions (`e4ddfb953aad898d`, 2 matchs, rapport sans la ligne du temps de calcul)
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 510 passés, 14 désélectionnés (07/11/2026, état final) ; attendu 2 500 + 10 tests nouveaux

## Comments

- 07/11/2026 : **Constantes proposées avant le code** (par Claude, validées par délégation du propriétaire, consigne permanente ; chiffres réels non trouvés : seul repère, une consigne d'entraîneur de 1 à 6 m de la ligne sans étude, et la théorie de la bissectrice, Barańska et Eckes 2020, sans valeur en mètres). **Face-à-face** = un adversaire de champ porte le ballon à **25 m ou moins** du but, sans coéquipier du gardien sur sa ligne de tir (`shooting.block_probability` nulle ; un défenseur resté derrière le porteur ne compte pas). **Réaction** : le gardien se place sur la bissectrice à **25 % de la distance du porteur à son but** (4 m pour un tireur à 16 m), **plafond 6 m**, jamais moins que son placement normal ; il avance à **60 % de sa vitesse max** et **se plante** (s'arrête) quand le porteur est à **8 m ou moins de lui**. **Arrêté** = vitesse sous **1,5 m/s** au moment du tir. **Critères chiffrés** : (1) scène du ticket : attaquant seul à 16 m dans l'axe, le gardien passe en `face-à-face` et vise le point à 4,0 m de sa ligne (placement normal : 2,4 m) ; (2) un défenseur sur l'axe : il reste en `placement` ; (3) en scène dynamique (attaquant parti de 35 m, ballon aux pieds), le gardien est sorti de plus de 2,5 m et sa vitesse est sous 1,5 m/s au tir ; (4) 50 matchs : part des tirs de face-à-face où le gardien est arrêté **supérieure à 50 %** (« majorité »), chance moyenne de ces tirs avant / après, nombre de face-à-face par match ; (5) deux exécutions, même empreinte.
- 07/11/2026 : **Correction de constantes, trouvée en scène** (même délégation) : l'arrêt à 8 m du porteur arrivait après le tir (un tir part de 12 à 17 m du but, donc à 7 à 12 m du gardien). Le gardien avance à 60 % de sa vitesse max tant que le porteur est à plus de **16 m** de lui, puis ne fait plus que de **petits pas à 12 % de sa vitesse max** (environ 1 m/s, sous le seuil de 1,5 m/s pour tous les gardiens, Pace de 10 à 99). Cette part est fixe : la règle R5 interdit au module du gardien de lire Pace, et la liste des modules autorisés n'est pas élargie.
- 07/11/2026 : **Réalisé** (`v2engine/gardien.py` : `FACE_*`, `face_to_face(keeper, holder, players)`, `face_depth`, `face_intensity`, état `face-à-face`, `bisector_point(..., depth_m=)` ; `cerveau._keeper` : intention « fermer l'angle » vers le point de la bissectrice à `face_depth`, jamais en deçà du placement normal ; banc : `Collector.on_shot_context` et `on_keeper`, `measure_v2` : face-à-face par match, tirs de face-à-face, chance, vitesse et distance du gardien au tir, part arrêtée). La condition « sans défenseur entre lui et le but » passe par `shooting.block_probability` (API publique) : un défenseur resté derrière le porteur ne compte pas. Un test du 03a (`test_keeper_near_an_opposing_holder_does_not_press`) plaçait un attaquant seul à 15 m : c'est désormais un face-à-face, un défenseur a été ajouté sur la ligne de tir pour garder son sens, et le cas face-à-face y est affirmé.
- 07/11/2026 : **Mesure (50 matchs, graine d'audit, avant = HEAD `9c1b89e` + indicateurs, après = final)** : tirs de face-à-face par match **12,5 → 13,2** ; gardien arrêté au tir (sous 1,5 m/s) **65,2 % → 92,1 %** (avant : il ne bouge pas, donc il est arrêté sans avoir rien fait) ; vitesse du gardien au tir **1,51 → 0,82 m/s** ; distance à sa ligne au tir **3,57 → 4,54 m** (le tireur est à 16,7 m dans les deux séries) ; **chance moyenne du tir 0,108 → 0,104, sans écart significatif** (intervalles à 95 % [0,092 ; 0,124] et [0,092 ; 0,119]) ; épisodes de face-à-face **32,2 par match** ; tirs par équipe 22,7 → 23,8 et buts par match 2,90 → 3,08 (intervalles qui se recouvrent). Fichiers : `mesures/03e-avant.*`, `03e-apres.*`, `03e-suite.txt`.
- 07/11/2026 : **Limites et points à surveiller.** (1) La chance du tir ne bouge pas : `shooting.keeper_position_factor` ne mesure que la part d'angle cachée par un corps de 1,5 m de demi-largeur, et un gardien 1 m plus avancé n'en change presque rien ; le gain du gardien avancé vient du plongeon et de la portée d'arrêt (05b, 17b), pas d'une formule de position. À regarder au 03g et au 06b. (2) 32 épisodes par match pour 13 tirs : l'état clignote quand un défenseur entre ou sort du cône de tir, ou quand le porteur passe ; sans conséquence sur le geste (même point visé), mais l'indicateur surestime les « vrais » face-à-face. (3) Le gardien ne plonge pas dans les pieds et ne tente pas de dribble : hors ticket (17b, `v2-attributs-restants/10b`). (4) 4,5 m de sa ligne au tir pour un tireur à 16,7 m : dans la fourchette de la consigne d'entraîneur (1 à 6 m), seule référence trouvée. (5) Les arrêts par match passent de 14,9 à 15,7 (part de tirs cadrés 31,7 → 32,3 %) : un peu plus de tirs, dans le bruit de la série, à décomposer au 03g comme la hausse notée au 03c.
- Durée : estimée 2 h (120 min ; 20/45/35/20), réelle environ 2 h 35 (155 min ; 25/45/35/50, non chronométrée), écart environ + 29 % (sous 30 %) : une seconde série de mesure et une seconde suite complète à cause de la règle R5 (le module du gardien ne peut pas lire Pace). Temps machine, hors total : deux séries de 50 matchs d'environ 25 min (la seconde ralentie par la suite en parallèle), suite complète 34 min 52 s en parallèle (`03e-suite.txt`).
- 07/11/2026 : **Clôture (/valider-ticket-simulafoot)** : expert `APPROVED_WITH_RESERVATIONS` (empreinte `814595e8…`), contrôle qualité `VALIDÉ`, décision de clôture `VALIDÉ` (journal). **Réserve A1** (acceptée par délégation permanente du propriétaire : « je valide automatiquement toutes tes recommandations et celles des experts », 05/11/2026, non reprise mot à mot dans cette conversation) : la profondeur de face-à-face ignore la hauteur de la ligne défensive du 03c ; derrière une ligne haute battue, un porteur à 18-25 m fait reculer le gardien de 0,6 à 2,2 m par rapport à son placement (aucun écart à la distance de tir, environ 16,7 m). Correctif : `depth_for_ball(reach, line_m)` dans la branche `depth_m` de `bisector_point` et `line` transmise par `_keeper` ; test : ligne à 40 m, porteur seul à 22 m, cible `x` au moins égale à celle de `placement(keeper, ball, 40)` ; **à faire au 03g**. Facultatifs : A2 (indicateur « atteint sa profondeur cible au tir », le critère « arrêté » partait de 65 %), A3 (hystérésis sur le clignotement de l'état). QC : réserve non bloquante identique.

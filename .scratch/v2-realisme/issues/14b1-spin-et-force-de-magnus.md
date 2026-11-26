# 14b1: Spin du ballon et force de Magnus dans le solveur

**Découpé du ticket 14b le 26/11/2026** (audit Magnus : `docs/AUDIT_MAGNUS_V2.md`). **Chantier :** `v2-realisme`. **Priorité :** P2. **Catégorie :** physique.

**Constat vérifié (26/11/2026) :** `BallState` n'a ni rotation ni hauteur ; le pas du ballon (`match.py` l. 921-974) avance en ligne droite et multiplie la vitesse par `0,6^dt` ; aucune occurrence de spin ou de courbe dans `v2engine/`.

**Périmètre :** D-V03 révisée le 26/11/2026 (`docs/TRD_V2.md`, décision du propriétaire) : rotation du ballon et force de Magnus dans le périmètre, vent exclu.

**What to build:**
1. **État** : `BallState.spin`, vecteur ω (rad/s) en 3D (axe vertical : effet latéral ; axe horizontal : effet avant ou arrière, lu par 14c et par la verticale du 02a). Remis à zéro à tout contrôle, contact d'un joueur, arrêt, sortie.
2. **Force** : dans le module de trajectoire livré par 14a, un terme de Magnus `a_M = ρ·A·C_L(S)·|v|² / (2m)`, dirigé selon `ω̂ × v̂`, ajouté à la traînée ; `S = r·|ω| / |v|` (paramètre de spin). Même fonction de pas pour la boucle de match et pour le prédicteur partagé : prédiction = réalité au pas près.
3. **Trace** : rien de nouveau à l'écran ; la piste `BallPoint` relevée à chaque pas suffit à dessiner la courbe (vérifier à l'écran).
4. **Aucune frappe ne met d'effet** dans ce ticket (14b4) : ω = 0 partout, jeu identique.
5. **Constantes figées ici, sourcées** (section ci-dessous) : 14b4 les lit, il ne les choisit pas.
6. **Magnus en vol seulement** (`z > 0`), **validé par le propriétaire le 26/11/2026** (réserve A2 de l'expert). Justification : ce n'est pas la force aérodynamique qui devient faible au sol ; à C_L constant, le rayon de courbure (environ 75 m) ne dépend pas de la vitesse, et une passe roulante qui garderait son effet latéral courberait autant qu'en l'air. C'est le contact avec le sol qui impose au ballon qui roule sa rotation de roulement (axe horizontal, sans effet latéral), et le frottement au sol tue vite l'effet latéral. Au rebond (contact bref), ω est conservé pour le 14c ; une fois le ballon roulant, ω devient la rotation de roulement, effet latéral nul.

**Attributs :** aucun.

**Blocked by:** 14a (Freinage du ballon au sol : roulement et air, qui livre le module de trajectoire et le prédicteur partagé, via 14a1 et 14a2 s'il est découpé) ; `v2-hauteur-ballon/02a` (hauteur `z`, `vz` : composante verticale de Magnus).

**Bloque :** 14b2, 14b3, 14c.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code, fin du sourcing (James et Haake 2008, Asai et al. 2007 à ouvrir) | 40 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 25** |

Confiance : moyenne. Hypothèses : 14a a livré un module de trajectoire unique (pas + prédicteur) et 02a l'état vertical ; sans cela, + 1 h 30 environ (le 14b1 referait le travail de 14a). Au-dessus du seuil de 2 h, examiné : indivisible (état, force et constantes ne se testent qu'ensemble), découpage non retenu. Sourcing déplacé ici depuis 14b4 le 26/11/2026 (demande du propriétaire), première passe faite à la création du ticket (ci-dessous).
Temps machine, non compté : suite complète (environ 10 min) ; deux empreintes à graine fixée.

## Repères sourcés (première passe du 26/11/2026, à figer avant le code)

| Grandeur | Valeur | Source | Statut |
|---|---|---|---|
| Coefficient de portance C_L | 0,23 à 0,29 sur un coup franc direct | Bray et Kerwin 2003, *J. Sports Sci.* 21 (« Modelling the flight of a soccer ball in a direct free kick ») | sourcé |
| C_L selon le spin | monte jusqu'à environ 0,25 vers 50 à 100 rad/s, puis à peu près constant | Goff et Carré 2010, *Eur. J. Phys.* 31 (« Soccer ball lift coefficients via trajectory analysis ») ; NASA Glenn, page « soclift » (C_L moyen 0,25) | sourcé |
| Spin d'un coup franc enroulé fort | environ 63 rad/s, soit 10 tr/s (Beckham 2001, 36 m/s au départ, environ 3 m d'écart latéral) | Goff et Carré, rapporté par Physics World (« Bend it like Beckham ») ; Physics Today (« Power and spin in the beautiful game » : 600 tr/min pour un coup franc fort) | sourcé (secondaire) |
| Spin maximal mesuré | 101 rad/s, mais vitesse du ballon tombée de 26 à 11 m/s | revue « The biomechanics of kicking in soccer: A review » | sourcé (secondaire) |
| Spin d'un centre ou d'une passe brossée ordinaire | — | non trouvé (à chercher ; sinon proposition sous le coup franc fort) | non trouvé |
| Décroissance de ω en vol | plus lente que celle de la vitesse sur 18 m de vol, indépendante du spin initial ; linéaire en ω·v | Tsukada et Sakurai 2008, ISBS ; James et Haake 2008, *Sports Eng.* (non ouverts, résumés seulement) | partiel |
| Coefficient de traînée C_D (pour 14a) | 0,25 à 0,30 | Bray et Kerwin 2003 | sourcé |

**Remarque sur 5 à 10 tr/s (question du propriétaire du 26/11/2026)** : 10 tr/s n'est pas trop haut pour un coup franc fort (63 rad/s mesurés) ; c'est le haut de la fourchette, pas une valeur courante. Pour les centres et passes, aucune valeur sourcée : proposer moins (de l'ordre de 3 à 6 tr/s) et le noter « non trouvé ».

**Mesure de l'écart latéral (réserve A1 de l'expert, 26/11/2026)** : le « 3 m » du coup franc de Beckham vient d'un résumé de presse et ne dit ni sa référence ni sa distance. Ordre de grandeur avec les constantes proposées (C_L = C_D = 0,25, ω constant, sans composante verticale) : `k = ρ·A·C/(2m) ≈ 0,0133 m⁻¹`, courbure constante, rayon ≈ 75 m quelle que soit la vitesse ; sur 27 m, écart ≈ 4,9 m à la **tangente de départ** et ≈ 1,2 m à la **corde** départ → arrivée. Le critère est donc défini ainsi : **scène de référence** 36 m/s au départ, 63 rad/s d'axe vertical, sans effet avant ou arrière, départ au sol à hauteur de frappe, **angle de départ de 16°** (proposé dans la fourchette de 15 à 20° des coups francs directs, à confirmer dans Bray et Kerwin 2003 en même temps que la cible ; avec Magnus en vol seulement, un départ horizontal retomberait en 0,15 s et ne courberait presque pas : point facultatif A1 de l'expert, passage 2) ; **mesure** écart à la droite de départ (tangente) au passage à 27 m de distance parcourue le long du départ ; **cible** fixée avant le code d'après une source primaire (trajectoire reconstruite de Goff et Carré 2010, ou modèle de Bray et Kerwin 2003), et non d'après un résumé de presse ; à défaut, cible = valeur calculée avec les constantes sourcées validées (≈ 4,9 m), notée « cohérence interne, cible réelle non trouvée ». On n'ajuste pas C_L ni C_D hors de leur fourchette sourcée pour atteindre un chiffre.

**Proposition à valider** : C_L(S) linéaire de 0 à 0,25 entre S = 0 et le spin de plateau, puis 0,25 (plateau de Goff et Carré) ; ω constant pendant le vol (au plus 2 à 3 s) tant que la décroissance n'est pas chiffrée, écart noté ; ρ = 1,2 kg/m³, r = 0,11 m, m = 0,43 kg (règlement IFAB : circonférence 68 à 70 cm, masse 410 à 450 g).

## Tests

- **Unitaires (scène contrôlée) :** coup franc de référence (36 m/s, 63 rad/s d'axe vertical, définition ci-dessus) : écart à la tangente de départ à 27 m égal à la cible validée, à ± 20 % ; contrôle analytique : écart ≈ L²/(2R) avec R = 1/k à ± 5 % (C_L, C_D constants, sans vertical) ; sens de la courbe = signe de ω ; ω = 0 : trajectoire identique à celle de 14a au flottant près ; prédicteur et boucle de match sur la même scène : mêmes positions à chaque pas
- **Non-régression :** mêmes empreintes de trace qu'avant le ticket sur deux graines (aucune frappe n'a d'effet)

## Acceptance criteria

- [ ] Constantes de la section « Repères sourcés » figées (valeur, source ou « non trouvé ») et validées par le propriétaire avant le code
- [ ] Mesure de l'écart latéral définie (scène, référence tangente, distance 27 m) et cible fixée d'après une source primaire, ou « non trouvé » avec la cible de cohérence interne, avant le code (réserve A1 de l'expert du 26/11/2026)
- [ ] Écart latéral du coup franc de référence à ± 20 % de cette cible, sans constante sortie de sa fourchette sourcée
- [ ] Magnus en vol seulement (règle validée par le propriétaire le 26/11/2026) : aucune force de Magnus quand `z = 0`, effet latéral nul une fois le ballon roulant, testé en scène
- [ ] Prédicteur et pas du ballon : écart de position nul (au flottant près) sur 3 s de vol avec effet
- [ ] Empreintes de trace identiques à avant le ticket à graine fixée (jeu inchangé tant que 14b4 n'est pas livré)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

Sources : [Bray et Kerwin 2003](https://www.researchgate.net/publication/10861342_Modelling_the_flight_of_a_soccer_ball_in_a_direct_free_kick), [Goff et Carré 2010](https://eprints.whiterose.ac.uk/98053/), [NASA Glenn](https://www.grc.nasa.gov/WWW/k-12/airplane/soclift.html), [Physics World](https://physicsworld.com/?p=1632), [Physics Today](https://physicstoday.aip.org/quick-study/power-and-spin-in-the-beautiful-game), [revue biomécanique](https://numerik.mi.fu-berlin.de/wiki/WS_2020/CoMaI_Dokumente/FTVS-2332-version1-the_biomechanics_of_kicking_in_soccer_a_review.pdf), [James et Haake 2008](https://shura.shu.ac.uk/2132), [Tsukada et Sakurai 2008](https://ojs.ub.uni-konstanz.de/cpa/article/view/1988/1856).

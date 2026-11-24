# 31: Attaquer la surface quand le centre est possible (chapeau)

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026 : « il n'y a pas beaucoup de centres pour le moment dans le moteur et j'aimerais corriger ça avant de continuer le chantier des têtes »). **Priorité :** P1. **Catégorie :** placement.

**Constat vérifié (24/11/2026) :**
- 1,5 centre par équipe et par match (série de 50 matchs du `15c1`, `docs/INDICATEURS_V2.md` § 81) ; repères réels cités de mémoire au `v2-attributs-restants/01`, à confirmer : 15 à 20 centres par équipe, 20 à 25 % réussis, 15 à 20 % des buts sur centre.
- Cause mesurée au `v2-attributs-restants/01` (un match, 23/11/2026) : zone de centre atteinte 84 fois, avec un coéquipier dans la surface 7 fois ; le centre (option `decision.in_cross_zone`, cibles : coéquipiers de champ dans la surface adverse) n'a donc presque jamais de cible.
- Dans le code : au plus 3 appelants dans le dernier tiers (`cerveau.CALLER_CAP`), qui cherchent un espace autour de leur place de référence (`off_ball.choose_space`, rayon 2 à 15 m selon Off the Ball), sans aucune notion de surface ni de centre ; défense préventive fixe (`defense.REST_DEFENDERS` = 2, possession installée seulement ; `09g` à faire) ; zones de la surface définies pour la défense seulement (`10f` : premier poteau, second poteau, point de penalty).

**What to build:** quand un coéquipier peut centrer, des attaquants partent dans la surface vers des zones distinctes, au bon moment, sans dégarnir la défense ; découpé (24/11/2026, demande du propriétaire) en :
- `31a` relevé de départ (mesure, sans changement du moteur) ;
- `31b` déclenchement et nombre d'attaquants dans la surface ;
- `31c` cibles de course dans la surface (premier poteau, second poteau, point de penalty, lisière) ;
- `31d` appels nourris par les attributs (option A du propriétaire, 24/11/2026 : lecture du centre probable : Anticipation ; moment, zone et intensité de l'appel : Off the Ball ; reprise après un effort : Work Rate) ;
- `31e` garde de sécurité derrière le ballon pendant l'attaque de la surface ;
- `31f` validation en match (centres, cibles, tirs et buts sur centre, transitions encaissées).

**Ordre conseillé :** `31a` → `31b` → `31e` (juste après `31b` : dès que des joueurs montent, il faut la garde, sinon la série du `31b` mesure aussi des contres encaissés) → `31c` → `31d` → `31f`. Puis `09b` (largeur), `25i` (dédoublement), `23b` (exécution du centre), `v2-attributs-restants/11` (centres variés), et reprise du jeu de tête (`15c1b`, `15c2`).

**Expertise (à confirmer par les mesures et les sources) :**
- Sur un centre en jeu, une équipe a typiquement deux à trois joueurs dans la surface et un quatrième à la lisière ou en retrait (second ballon, centre en retrait) ; l'attaquant axial attaque le premier poteau ou le point de penalty, l'ailier opposé le second poteau (côté aveugle du défenseur), le milieu offensif arrive tard au point de penalty ou à la lisière.
- Le timing compte plus que la position : arriver lancé quand le ballon part, pas attendre immobile dans la zone (marqué, hors-jeu, pas d'élan pour le duel aérien du `15b1`) ; l'appel part quand le centreur peut centrer (ballon contrôlé dans la zone, tête levée), pas dès que le ballon entre dans le couloir.
- Le hors-jeu se juge au départ du centre : l'appel ne dépasse pas la ligne de l'avant-dernier défenseur avant le centre, il la franchit ensuite.
- Le centre ne sera choisi que s'il vaut plus que les autres options : avec des cibles, sa valeur (`LONG_BALL_WON` = 0,5) peut rester basse ; c'est à mesurer au `31f` avant de toucher à quoi que ce soit (ticket à part si besoin).

**Blocked by:** rien (le centre existe : `v2-attributs-restants/01`, livré). **Bloque :** `15f` (gagne à voir plus de centres).

**Status:** découpé (24/11/2026) en `31a` à `31f`

## Estimation

Somme des sous-tickets : `31a` 1 h, `31b` 2 h 10, `31c` 1 h 45, `31d` 2 h 05, `31e` 1 h 40, `31f` 1 h 15, soit **environ 10 h** de travail effectif. Confiance : faible (chantier neuf ; découpage à revoir après le `31a`). Temps machine, non compté : une série de 50 matchs par sous-ticket qui change le jeu (environ 45 min chacune), suite complète (environ 23 min) à chaque clôture.

## Acceptance criteria

- [ ] Sous-tickets livrés, validés expert + QC
- [ ] Centres par équipe nettement relevés vers les repères réels, sans régression des buts encaissés en transition (`31f`)

## Comments

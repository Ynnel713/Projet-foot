# 01: Centres, jeu aérien et taille

**What to build:** Phase 7 du plan V2. Le porteur sur un côté peut centrer ; un ballon aérien (centre, dégagement long, corner plus tard) est disputé par les joueurs proches de son point de chute ; le duel aérien est résolu par un tirage pondéré (D-V03, pas de vraie trajectoire 3D) :

1. **Arriver au ballon** : Taille FM (`Taille FM (cm)`, repli sur `Taille (cm)`, puis neutre) + Jumping Reach, pondérés par Bravery (aller au contact) ; Strength pour le placement au contact.
2. **Bien le jouer** : Heading (direction, puissance) pour le joueur qui l'emporte.
3. ~~Frappes lointaines par Long Shots~~ : déplacé au ticket `v2-collectif/28` (même calcul de tir, frontière Finishing / Long Shots tranchée là-bas ; recommandation de l'expert acceptée le 03/11/2026). L'issue d'une tête passe par le calcul de tir du 28.

**Attributs :** Crossing, Heading, Jumping Reach, Bravery, Taille (Long Shots : ticket `v2-collectif/28`). Les types de centres (enroulé, tendu, en retrait, au ras du sol) sont au ticket 11.

**Complément (03/11/2026, D-V03 révisée, `docs/ETUDE_HAUTEUR_V2.md`) :** le ballon a désormais une vraie hauteur (`v2-hauteur-ballon/02`) et chaque joueur une tranche de hauteur accessible (`v2-hauteur-ballon/03`). Le tirage pondéré ne réunit que les joueurs capables d'atteindre le ballon à temps (bonne position au bon instant, hauteur dans leur portée de tête). Le moteur trace un événement « saut » (joueur, instant, hauteur de pointe) ; l'écran remonte le rond du sauteur, son ombre restant au sol. Les joueurs restent à plat dans le moteur.

**Blocked by:** v2-collectif/18 (règle anti double comptage), v2-collectif/28a (calcul du tir, pour la tête), v2-hauteur-ballon/03 (hauteur du ballon et portée des joueurs).

**Bloque :** 11 ; `v2-realisme/23b` (ajouté le 10/11/2026).

**Status:** livré (23/11/2026), validé expert + QC (périmètre réduit au centre le 05/11/2026 ; jeu aérien : `v2-realisme/15a` à `15f`)

## Estimation (23/11/2026, périmètre réduit au centre)

| Poste | Durée |
|---|---|
| Analyse | 25 min |
| Développement | 45 min |
| Tests (scènes, gardes) | 35 min |
| Intégration et vérifications | 35 min |
| **Total (travail effectif)** | **2 h 20** |

Confiance : moyenne. Au-dessus du seuil de 2 h, gardé d'un seul tenant (décision, exécution et Crossing ne se mesurent qu'ensemble). Temps machine, non compté : deux séries de 50 matchs (environ 40 min chacune), suite complète (environ 17 min).

**Constantes** (validées par le propriétaire le 23/11/2026, « Validées telles quelles ») : zone du centreur dans les 35 derniers mètres (`decision.CROSS_ZONE_DEPTH_M`) et hors de la largeur de la surface (plus de 20,16 m de l'axe) ; cibles : coéquipiers de champ dans la surface adverse, hors-jeu évident exclu ; Crossing remplace Passing pour la précision et le dosage du centre, même loi et même difficulté au mètre qu'une passe en l'air (0,8) ; retombée estimée gagnée à 0,5 (`LONG_BALL_WON`, valeur existante, jusqu'au duel aérien `v2-realisme/15b`). Repères réels, cités de mémoire, à confirmer : 20 à 25 % de centres réussis, 15 à 20 centres par équipe et par match, 15 à 20 % des buts sur centre (situer la mesure, pas de calibrage ici).

**Critères chiffrés** (posés avant le code) : scène : à Crossing 90, plus de centres près de leur cible qu'à Crossing 30, jamais 0 ni 100 % ; scène : ailier dans la zone, buteur libre dans la surface, passe au sol fermée : il centre ; 50 matchs appariés : centres par équipe, part réussie, tirs nés d'un centre relevés, écarts sur buts, tirs et possession expliqués ; part des contrôles de la tête en hausse (**non mesuré ici, reporté au `v2-realisme/15a`**, décision du propriétaire du 23/11/2026 : sans puissance à 1,5 centre par équipe) ; déterminisme à graine fixée ; suite complète au compte attendu.

**Constat avant la série (23/11/2026)** : sur un match complet, la zone de centre est atteinte 84 fois, avec un coéquipier dans la surface 7 fois seulement, et le centre est joué une fois : les attaquants n'attaquent pas la surface quand l'ailier peut centrer (ticket `v2-realisme/15a`). Décision du propriétaire : « Livrer tel quel, puis 15a » (centres rares, écart noté ; 15a les fera monter).

**Point de vigilance :** la taille ne doit pas tout écraser (un 1,75 m à grande détente gagne des duels contre un 1,90 m moyen). Ordre de grandeur de l'avantage de taille dans les duels aériens réels à sourcer ; « non trouvé » sinon.

- [ ] À autres attributs égaux, un joueur de 1,95 m gagne mesurablement plus de duels aériens qu'un joueur de 1,70 m, sans jamais 100 % ni 0 %
- [ ] Jumping Reach élevé compense une partie de l'écart de taille (mesuré)
- [ ] Le gagnant du duel cadre mieux sa tête avec un Heading élevé
- [x] Crossing élevé : plus de centres atteignant un coéquipier
- [ ] Joueur sans taille renseignée : comportement neutre (taille moyenne du poste)
- [ ] Seuls les joueurs capables d'atteindre le ballon à temps disputent le duel (scène fixe : un joueur trop loin ou trop petit n'y figure pas)
- [ ] Chaque duel aérien trace un saut, visible à l'écran (rond remonté, ombre au sol)
- [x] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [x] Suite V2 verte ; V1 inchangée

Les autres critères ci-dessus (duel aérien, taille, Jumping Reach, Heading, saut à l'écran, joueurs capables d'atteindre le ballon) sont repris par `v2-realisme/15a` à `15f` depuis le découpage du 05/11/2026 (« seuls les joueurs capables d'atteindre le ballon » est déjà tenu par l'atteinte du `v2-hauteur-ballon/03a`).

## Résultats (23/11/2026)

- Code : `v2engine/decision.py` (`CROSS_ZONE_DEPTH_M`, `in_cross_zone` ; option de centre vers chaque coéquipier de champ dans la surface adverse, hors-jeu évident exclu, passe en l'air, valeur avec `LONG_BALL_WON` ; `Action.cross`) ; `v2engine/possession.py` (`cross` dans `dosage_quality`, `pass_accuracy_probability`, `pass_success_probability`, `pass_aim`, `pass_launch` : Crossing à la place de Passing, passe en l'air) ; `v2engine/match.py` (centre lancé en l'air, `CENTRE` au journal) ; banc : `centres par équipe`, `centres réussis (part)` (`scripts/v2_indicators.py`, `measure_v2.py`).
- Scènes (`tests/test_v2engine_centre.py`, 8 cas) : constante ; zone (35 derniers mètres, hors largeur de la surface, deux sens) ; ailier dans la zone, buteur libre dans la surface, passe au sol fermée par deux défenseurs : il centre ; passe au sol ouverte : la passe au sol est préférée (le centre reste envisagé) ; pas de centre depuis l'axe ni vers un coéquipier hors de la surface ; Crossing et non Passing règle la précision et le dosage d'un centre (l'ordre s'inverse sans centre) ; Crossing 90 met plus de centres à moins de 3 m de leur cible que Crossing 30, jamais 0 ni 100 % ; centre parti en l'air, noté « centre » au journal. Gardes : Crossing en transition vers son second contexte (`11`), exception de couverture retirée, scène de garde « centre » (Crossing 11 contre 99 : le jeu diverge).
- Série (50 matchs appariés, avant `5976b01`), détail `docs/INDICATEURS_V2.md` § 75 : 1,54 centre par équipe et par match (réel 15 à 20), 46,8 % gardés par l'équipe du centreur ; tirs nés d'un centre 1,3 → 2,0 % ; grosses occasions nées d'un centre 2,4 → 3,6 % (significatif) ; buts 5,18 → 4,32 (− 0,86 [− 1,78 ; + 0,06]), tirs par équipe 15,6 → 14,6 (− 1,0 [− 1,8 ; − 0,2], significatif) ; 233 indicateurs significatifs sur 2 826 (environ 141 attendus) : effet de chaîne (chaque option envisagée tire une erreur de perception, l'option « centre » décale les tirages), qui empêche de séparer la part réelle de la baisse des tirs (centre perdu à la place d'une conduite vers la surface) ; à surveiller au `15a`.
- Centres rares (décision du propriétaire du 23/11/2026, « Livrer tel quel, puis 15a ») : zone atteinte 84 fois par match, coéquipier dans la surface 7 fois.
- **Critère non mesuré** : « part des contrôles de la tête en hausse » (aucun indicateur ne lit encore la partie du corps au contrôle) ; reporté au `v2-realisme/15a` (décision du propriétaire du 23/11/2026, réserve A1 de l'expert et refus du contrôle qualité). Calcul de l'expert : sur un centre type (26 m), le ballon arrive au receveur visé vers 1,67 m, au-dessus du début de la tête d'un buteur de 1,84 m (1,51 m) : joué de la tête.
- **Baisse des tirs** (réserve A2, acceptée) : l'effet direct des centres est borné à 0,2 à 0,4 tir par équipe sur − 1,0 (1,54 centre, 0,19 tir par centre, l'option remplacée finissant en tir 30 % du temps au plus) ; le reste est du hasard (p ≈ 0,01) ou un mécanisme non identifié (aucun chemin trouvé dans le code) ; rapport tirs / centres à vérifier au `15a`.
- Déterminisme : matchs 0 et 1 rejoués, mêmes empreintes de la piste du ballon (`f9e6b7bd6544`, `605176038441`), 3 et 2 centres.
- Suite complète : 3 628 passés, 0 ignoré, 14 désélectionnés (3 619 + 8 cas + 1 scène de garde) ; V1 non touchée.
- Durée réelle : environ 1 h 50 (analyse 25, développement 30, tests 25, intégration et vérifications 30), − 21 % ; diagnostic des centres rares (deux matchs instrumentés) et recherche de la scène du critère compris. À l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : deux séries de 50 matchs (36 et 35 min), rejeu de 2 matchs, suite complète (16 min).

## Comments

- 23/11/2026, passage 1 : expert APPROVED_WITH_RESERVATIONS (empreinte `89b6b774…`). Réserves : A1, critère « part des contrôles de la tête en hausse » non mesuré ; A2, baisse des tirs expliquée par les centres pour 0,2 à 0,4 tir au plus sur − 1,0 ; A3, cibles du centre hors du filtre de Vision. Facultatif A4 (`lofted or cross` non transmis au plafond de vitesse, test qui combine deux gardes, `cross` absent du journal des décisions, pas de portée maximale du centre). QC REFUSÉ (1er refus) : même manque que A1, critère ni mesuré ni déclaré reporté. Propriétaire : A1 « Reporter au 15a », A2 « J'accepte A2 », A3 « Acter : la surface est vue » (écrit dans `docs/CARTE_ATTRIBUTS_V2.md`). Ticket, § 75 et ticket `v2-realisme/15a` mis à jour.
- 23/11/2026, passage 2 : expert APPROVED_WITH_RESERVATIONS (empreinte `d0121324…`), A3 levée, A1 et A2 acceptées par le propriétaire, A4 facultatif. QC VALIDÉ. Clôture VALIDÉ (réserves acceptées). À surveiller au 15a et au 11 : rapport centres / variation des tirs et des buts, part des centres repris de la tête, part coupée à la retombée, trajectoire flottée (2,3 s de vol, sommet 6,4 m).


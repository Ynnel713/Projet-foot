# 03a: Interception selon la hauteur : ballons en jeu

**Découpé du ticket `03` le 23/11/2026** (décision du propriétaire, 2 h 40 estimées au-delà du seuil de 2 h). Référence : `03-interception-selon-hauteur.md`, `docs/ETUDE_HAUTEUR_V2.md` section 5.

**What to build:** chaque joueur a une atteinte en hauteur, calculée depuis sa taille et sa détente (Jumping Reach) ; il ne touche un ballon en jeu (passe, ballon libre, rebond) que si le ballon passe à sa portée dans une tranche de son corps : pied, corps, tête, mains (gardien dans sa surface). Remplace la règle du ticket `v2-collectif/29` lue sur la hauteur au `02a1` (personne au-dessus de 2,5 m, tout le monde en dessous). La lecture « qui atteint le ballon en premier » (`occasion.reach_probability`) suit la même atteinte. Un seul joueur touche le ballon, le premier qui l'atteint ; pas de duel ni de saut dessiné ; la qualité du geste reste aux tickets existants. Tirs : `03b`.

**Attributs :** taille (`Taille FM (cm)`, repli : médiane du poste), Jumping Reach (détente). Premier contexte de Jumping Reach ; le second sera le duel aérien `v2-realisme/15b`, qui réutilisera la même hauteur atteinte sans bonus en plus.

**Blocked by:** `02a1`, `02a2` (livrés).

**Bloque :** `03b`, et ce que bloquait le `03` : `v2-collectif/32b`, `v2-attributs-restants/01`, `v2-attributs-restants/03a`, `v2-realisme/15a`.

**Status:** livré (23/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : moyenne. Temps machine, non compté : deux séries de 50 matchs (environ 40 min chacune), relevé des contacts sur 20 matchs (environ 15 min), suite complète (environ 17 min).

**Constantes** (validées par le propriétaire le 23/11/2026, « Validées telles quelles ») : tranches en part de la taille H d'après les proportions de Drillis et Contini (1966, reprises par Winter, *Biomechanics and Motor Control of Human Movement* : hanche 0,530 H, épaule 0,818 H) : pied jusqu'à 0,53 H, corps jusqu'à 0,82 H, tête jusqu'à H + détente ; détente de 0,35 m (Jumping Reach 1) à 0,65 m (99), linéaire (repère : environ 56 cm de saut vertical chez des footballeurs d'élite, Wisløff et al. 2004, cité de mémoire ; lien note-centimètres non trouvé) ; mains du gardien dans sa surface : 1,30 H + détente (portée debout bras tendus, source non trouvée) ; taille manquante : médiane du poste dans la base (477 tailles sur 485 joueurs de Ligue 1).

**Critères chiffrés** (posés avant le code) :
- scènes : ballon à 2,5 m au-dessus d'un défenseur de 1,70 m (Jumping Reach 20) : il passe ; repris par un joueur de 1,90 m (Jumping Reach 90) ; le gardien capte dans sa surface un ballon à 2,7 m hors de portée d'un joueur de champ ; un ballon à 0,5 m est joué du pied par le plus petit joueur de la base (1,67 m) ;
- 50 matchs : jamais de contact au-dessus de l'atteinte du joueur (par construction et relevé) ; répartition des contacts par partie du corps relevée ;
- 50 matchs appariés avant / après : interceptions, possession, passes réussies (dont longues), buts ; chaque écart significatif expliqué ;
- déterminisme : mêmes empreintes à graine fixée ; suite complète au compte attendu ; V1 inchangée.

## Acceptance criteria

- [x] Constantes des tranches proposées, sourcées ou notées « non trouvé », validées avant le code
- [x] Scènes fixes du ballon à 2,5 m, du gardien et du ballon à 0,5 m
- [x] Mesure sur 50 matchs avant/après : interceptions, possession, passes réussies, buts ; chaque écart expliqué
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [x] Déterminisme : mêmes empreintes à graine fixée
- [x] Suite complète au compte attendu ; V1 inchangée

## Résultats (23/11/2026)

- Code : `v2engine/atteinte.py` (constantes ; `height_of` : taille de la fiche ou médiane du poste ; `jump_m` : détente selon Jumping Reach ; `uses_hands` : gardien dans sa surface ; `reach_m` ; `body_part` : pied, corps, tête, mains, ou `None` au-dessus) ; `PlayerState.height_m` (posé par `match._build_players`, gardé par `movement.step`) ; `match._step_loose_ball` : contact refusé si le ballon passe au-dessus de l'atteinte du joueur à son entrée dans sa portée (remplace la règle commune de 2,5 m et le retour anticipé « en l'air pendant tout le pas ») ; `ReceptionEvent.ball_z_m` et `body_part` (trace) ; `occasion.reach_probability` : points de trajectoire sous l'atteinte du joueur, et des adversaires pour l'échéance ; `vol.AERIAL_HEIGHT_M` ne règle plus que le mode tracé. **Défaut corrigé** (`vol.step_height`) : sur une durée nulle, la hauteur valait 0 ; depuis le `02a1`, un ballon déjà au contact d'un joueur en début de pas était lu au sol (touchable à toute hauteur), et les hauteurs au contre et au gardien relevées au `02a2` étaient sous-estimées (issues inchangées).
- Scènes (`tests/test_v2engine_atteinte.py`, 11 cas) : constantes ; repli de la taille ; détente ; tranches du corps ; ballon à 0,5 m joué du pied par un joueur de 1,67 m ; mains du gardien seulement dans sa surface ; ballon à 2,5 m : passe au-dessus du défenseur de 1,70 m (Jumping Reach 20, atteinte 2,11 m), pris par le joueur de 1,90 m (Jumping Reach 90, atteinte 2,52 m) ; seul, le petit défenseur ne le touche pas ; le gardien capte dans sa surface un ballon à 2,7 m hors de portée d'un joueur de champ ; lecture d'occasion selon l'atteinte ; hauteur sur une durée nulle. Gardes adaptées : `test_v2engine_rayon_attributs` (Jumping Reach en transition vers son second contexte `v2-realisme/15b`, exceptions de couverture Jumping Reach et Taille retirées), `test_v2engine_garde_attributs` (Jumping Reach et Taille annoncés, Taille lue par son champ `height_m`, scène du long ballon du gardien : divergence entre 11 et 99).
- Série (50 matchs appariés, `bench_series`, avant : `55d2b3e`), détail `docs/INDICATEURS_V2.md` § 73 : buts 5,16 → 5,20 (+ 0,04 [− 0,87 ; + 0,95]), tirs par équipe 15,1 → 15,4, passes réussies 84,2 → 84,1 %, passes longues réussies 70,4 → 69,8 %, possession + 0,09 s, pertes de balle − 0,22 par match, dans le bruit (interceptions : pas d'indicateur direct dans le banc). Significatifs : duels d'épaule 22,7 → 24,8 par match (un ballon au-dessus d'un petit joueur file vers une course partagée) ; sorties du gardien sur passe ou centre 1,84 → 2,42 (ses mains vont au-delà de 2,5 m). 159 indicateurs significatifs sur 2 826 (environ 141 attendus).
- Contacts (20 matchs, `03a-contacts.py`) : 27 180 contrôles ; pied 99,2 % (max 0,93 m), corps 104, tête 106 (max 2,55 m), mains 1 ; **0 au-dessus de l'atteinte**.
- Déterminisme : matchs 0 et 1 rejoués, mêmes empreintes complètes (`f442b3d6…`, `b134947f…`).
- Suite complète : 3 612 passés, 0 ignoré, 14 désélectionnés (3 599 + 11 cas + 2 cas de garde) ; V1 non touchée.
- Durée réelle : environ 2 h 05 (analyse 30, développement 35, tests 30, intégration et vérifications 30), + 14 % ; garde des attributs à adapter (premier caractère de la fiche lu par un champ, scène aérienne) et défaut de `height_at` trouvé par une scène. À l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : deux séries de 50 matchs (41 et 38 min), relevé de 20 matchs (12 min), rejeu de 2 matchs, deux suites complètes (17 min chacune, la première avec 4 échecs de la garde).

## Comments

- 23/11/2026, passage 1 : expert APPROVED (empreinte `4b776175…`), aucune action obligatoire ; facultatifs A1 (hauteur lue à l'entrée dans la portée, pas au plus bas de la traversée), A2 (mains du gardien aussi sur une passe de son équipe, qu'il ne peut pas prendre en main), A3 (cas à un seul point de `reach_probability` sans filtre d'atteinte des adversaires), A4 (relevé des contacts sur 20 matchs au lieu des 50 annoncés au critère : propriété garantie par construction, 27 180 contrôles ; postes sans médiane propre au repli de 1,82 m). QC VALIDÉ (remarques non bloquantes : commentaire périmé de `match.py` au-dessus de 2,5 m, ordre des imports). Clôture VALIDÉ. À surveiller (expert) : sorties du gardien sur centre quand les centres arriveront ; A1 si le jeu aérien devient fréquent ; au `15b`, même atteinte sans bonus.

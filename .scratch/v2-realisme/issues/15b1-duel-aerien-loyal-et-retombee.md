# 15b1: Duel aérien loyal et retombée

**Chantier :** `v2-realisme` (découpe du `15b`, validée par le propriétaire le 24/11/2026). **Priorité :** P2. **Catégorie :** exécution.

**Constat vérifié :** sur un ballon aérien, le premier joueur que le ballon frôle à sa portée le prend (`match._step_loose_ball`, boucle des contacts) ; aucun duel entre deux adversaires qui sautent ensemble, aucune retombée.

**What to build:** quand le ballon arrive à la tête d'un joueur et qu'un adversaire à moins de 1 m peut aussi l'atteindre, les deux se disputent le ballon. Chacun a une hauteur effective : taille + détente (Jumping Reach ; 100 % avec élan, à 3 m/s ou plus, 85 % sans), + ou − le placement au contact (Strength, part du contact du `11b`, jusqu'à ± 6 cm). Le gagnant est tiré sur une courbe en S de l'écart des hauteurs effectives (échelle 0,18 m), bornée de 10 à 90 %. Le gagnant joue le ballon (contrôle ou tête comme aujourd'hui) ; le perdant ne peut plus le toucher avant de retomber. Retombée : tout joueur qui a sauté (ballon au-dessus de sa taille) ne peut pas agir pendant 0,2 s ; le perdant du contact (Strength) subit en plus le contact perdu du `12c` (Balance).

**Attributs :** taille, Jumping Reach (hauteur atteinte, déjà lue pour l'atteinte), Strength (part du contact, déjà lue au `11b`), Balance (après le contact, `12c`). Aucun bonus nouveau sur un attribut hors de ces rôles (`docs/CARTE_ATTRIBUTS_V2.md`).

**Constantes** (proposées et validées par le propriétaire le 24/11/2026, « oui je valide ») :
- `DUEL_RADIUS_M` = 1,0 m : un adversaire à moins de 1 m (centre à centre) du joueur que le ballon atteint ;
- `RUN_UP_MPS` = 3,0 m/s et `STANDING_JUMP_SHARE` = 0,85 : détente entière avec élan, 85 % sans (non trouvé : ordre de grandeur) ;
- `PLACEMENT_M` = 0,06 m : placement au contact, de − 6 à + 6 cm selon la part du contact (0,25 à 0,75) ;
- `DUEL_SCALE_M` = 0,18 m, bornes `DUEL_MIN` = 0,10 et `DUEL_MAX` = 0,90 ;
- `LANDING_S` = 0,2 s (non trouvé : ordre de grandeur).
Repères : 1,95 m contre 1,70 m, autres notes égales : 80 % ; 10 cm d'écart : 64 % ; 1,70 m (Jumping Reach 99) contre 1,95 m (50) : 36 %. Chiffres réels : StatsBomb HOPS (la taille explique 22 % de la variation de la capacité aérienne) ; Kim et Kim 2025 ; Stats Perform (31 % des duels sont aériens loyaux) ; avantage de taille chiffré en pourcentage de duels gagnés : non trouvé.

**Hors périmètre :** fautes du duel (`15b2`), jeu dangereux (`15b3`), qualité de la tête (`15c`), seconds ballons (`15e`), gardien (`v2-attributs-restants/03a`), Bravery (`17b`).

**Blocked by:** `15a3` (livré), `11b` (livré), `12c` (livré). **Bloque :** `15b2`, `15b3`, `15c`, `15f`.

**Status:** livré (24/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : moyenne. Hypothèses : branchement dans la boucle des contacts du ballon libre, sans toucher au journal des causes (duels tracés à part). Temps machine, non compté : série de 50 matchs appariée (environ 48 min ; avant : série « après » du `15a3`, même code), suite complète (environ 22 min).

**Critères chiffrés** (posés avant le code, 24/11/2026) : probabilité 0,80 ± 0,01 (1,95 contre 1,70 m), 0,64 ± 0,01 (10 cm), 0,36 ± 0,02 (1,70 m JR 99 contre 1,95 m JR 50), jamais hors de [0,10 ; 0,90], symétrique ; scène A/B de 400 duels par profil : le grand gagne 80 % ± 5 points, Jumping Reach 99 ramène le petit sous 50 % d'écart ; retombée : sauteur bloqué 0,2 s, perdant du contact retardé selon Balance ; série de 50 matchs : duels aériens comptés par match, gagnés selon la taille, buts et tirs sans écart significatif hors du jeu aérien (rapportés, non réglés) ; déterminisme à graine fixée ; suite complète à 3 645 passés + nouveaux cas, 0 ignoré, 14 désélectionnés.

## Tests

- Unitaires : hauteur effective (élan, placement), probabilité (repères, bornes, symétrie).
- Comportementaux : scène de centre, 1,95 m contre 1,70 m puis Jumping Reach 99 au petit ; adversaire à plus de 1 m ou incapable d'atteindre le ballon : pas de duel ; gardien : pas de duel ; retombée.
- Série : duels par match, part gagnée par le plus grand ; premier contrôle du corps après un centre surveillé (expert, `15a3`).

## Acceptance criteria

- [x] Repères de probabilité tenus, bornes et symétrie
- [x] Effets mesurés en scène A/B (taille, Jumping Reach)
- [x] Joueur sans taille : taille moyenne du poste (`atteinte.height_of`, inchangé)
- [x] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %

## Résultats (24/11/2026)

- Code : `v2engine/duel_aerien.py` (nouveau) : `effective_height_m` (taille + `atteinte.jump_m`, × 0,85 sans élan, + placement de la part du contact `duel.contact_share`), `win_probability` (courbe en S bornée), `rival` (adversaire de champ à 1 m au plus qui atteint la hauteur du ballon ; aucun duel pour un gardien dans sa surface), `resolve` (flux DUEL), `jumped`. `v2engine/match.py` : dans la boucle des contacts du ballon libre, après le hors-jeu, un ballon en l'air joué de la tête déclenche le duel ; le gagnant prend la suite (contrôle, perte, journal, réception) ; `_cannot_contest` (mêmes exclusions que le contact : passeur, écarté, contrôle raté, déséquilibré, hors-jeu à la passe) ; `_land` (retombée). Trace : `AerialDuelRecord`, liste `MatchTrace.aerial_duels`, tenue hors du journal des causes (le journal garde ses chaînes passe → contrôle). Banc : `duels aériens par match`, `gagnés par le plus grand`, `gagnés par le premier au ballon`.
- Repères : 1,95 contre 1,70 m 0,800 ; 10 cm 0,635 ; 1,70 m JR 99 contre 1,95 m JR 50 0,365 ; Strength 90 contre 40, même taille 0,66 ; sans élan contre avec élan, même taille 0,40.
- Tests (`tests/test_v2engine_duel_aerien.py`, 8 cas) : constantes ; hauteur effective ; repères, bornes, symétrie ; scène de 400 duels : le grand gagne 80 % ± 5, 64 % ± 5 face au petit à JR 99 ; pas de duel hors déclenchement (1,05 m, hauteur hors d'atteinte, gardien, coéquipier, exclus, ballon sous la tête) ; adversaire signalé hors-jeu ; retombée et Balance ; trace et déterminisme. Garde du rayon : Jumping Reach reste dans la liste de transition (capacité physique R5, pas un contexte du registre), rattachée au ticket `v2-attributs-contextes/08`.
- Série (50 matchs appariés, avant : série retenue du `15a3`, code identique à `c78fd54`), `docs/INDICATEURS_V2.md` § 79 : 7,56 duels aériens par match ; 68 % gagnés par le plus grand (tailles différentes) ; 53 % par le joueur atteint le premier ; buts 5,18 → 5,08, tirs 15,34 → 15,31, fautes 20,58 → 21,02, premier contrôle de la tête après un centre 52,9 → 51,1 % : dans le bruit. 201 indicateurs significatifs sur 2 837 (142 attendus par hasard ; séries décorrélées, comme aux `15a` et `11c`).
- Constat : duels rares (7,6 par match) : peu de ballons en l'air (1,4 centre par équipe) et défenseur qui ne vient pas au contact de l'attaquant sur son point de saut (chaque désigné vise son propre point). Hors périmètre ; piste proposée au propriétaire.
- Déterminisme : matchs 0 et 1 rejoués deux fois, mêmes empreintes de la trace complète (`0939628bb66816f0`, `c5234729b1b007e1` ; 5 et 11 duels aériens).
- Suite complète : 3 653 passés, 0 ignoré, 14 désélectionnés (3 645 + 8 cas) ; V1 non touchée.
- Durée réelle : environ 1 h 30 (analyse 30, développement 20, tests 15, intégration et vérifications 25), − 33 % sur l'estimation de 2 h 15 : mécanismes existants réutilisés tels quels (part du contact du `11b`, contact perdu du `12c`, atteinte du `03a`), analyse en grande partie faite pendant la proposition de découpe ; série « avant » reprise du `15a3`. À l'horloge de la session hors attentes machine, non chronométrée. Temps machine hors total : suite complète (21 min), une série de 50 matchs (45 min), deux matchs d'essai, rejeu de 2 matchs.

## Comments
- 24/11/2026, passage 1 : expert APPROVED (empreinte `e9807551…`, code et tests seuls ; repères recalculés à la main, symétrie et scène A/B vérifiées) ; QC VALIDÉ. Clôture VALIDÉ.
- Facultatif (expert A1) : la retombée de 0,2 s ne vaut que dans un duel ; un joueur qui saute seul n'est pas bloqué (à trancher si le `15b2` ou le `15c` touchent la tête hors duel).
- Facultatif (expert A2) : le rival est admis sur sa détente entière (`reach_m`), sa hauteur effective sans élan n'en prend que 85 % (au plus 10 cm à la marge, pénalisé par la probabilité).
- Facultatif (expert A3) : quand le rival gagne, le ballon passe en un pas à sa position (jusqu'à 1 m).
- Remarque QC : première assertion du test hors-jeu faible, complétée par la seconde.
- À surveiller (expert) : rareté des duels (7,6 par match ; défenseur au point de saut de l'attaquant, ticket à proposer) ; reprise de la mesure des longs ballons du gardien (commentaire du chapeau `15b`, réserve A1 du `03c1`).

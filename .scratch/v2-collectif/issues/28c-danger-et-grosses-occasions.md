# 28c: Danger et grosses occasions, avec ou sans tir

**Découpé du ticket 28 le 04/11/2026** (audit de granularité). Détail : `28-occasion-et-issue-du-tir.md`, points 2, 6 et 7 (partie séquence).

**What to build:**

1. **Danger de la situation** : à chaque instant de la possession, la meilleure occasion potentielle parmi les attaquants (qualité du 28a), pondérée par la probabilité que le ballon leur parvienne. Une **grosse occasion** est un pic de danger au-dessus d'un seuil, **quelle que soit l'issue**.
2. **Issue d'une séquence dangereuse sans tir** : tacle ou interception salvateur, dégagement, centre non repris.
3. **Trace** : séquence dangereuse (début, pic de danger, issue), utilisée par les modes « Moments clés » et « Résumé » (`v2-mise-en-scene/02` et `03`).

**Attributs :** aucun nouveau.

**Blocked by:** 28a.

**Bloque :** `v2-mise-en-scene/02` et `03` ; 17, 19 et 22a (le 28 est « à livrer avant 17, 19 et 22 »).

**Status:** livré (08/11/2026), validé expert + QC

## Estimation

| Poste | Estimé | Réel |
|---|---|---|
| Analyse et compréhension du code | 25 min | 35 min |
| Développement | 50 min | 45 min |
| Tests | 30 min | 20 min |
| Intégration et vérifications | 35 min | 55 min |
| **Total (travail effectif)** | **2 h 20** | **2 h 35** (+ 11 %, durée réelle estimée, non chronométrée) |

Confiance : moyenne. Hypothèses : calcul en lecture seule, sans tirage, branché après chaque pas du ballon ; aucune constante de jeu. Temps machine, hors total : empreintes avant/après (2 matchs, environ 4 min), série de 50 matchs en 8 lots, suite complète.

## Constantes (proposées le 08/11/2026, validées par délégation du propriétaire)

| Constante | Valeur | Source |
|---|---|---|
| `BIG_CHANCE_DANGER` (seuil de grosse occasion) | 0,20 : une chance sur cinq de marquer, soit le niveau d'un face-à-face à 8-9 m, gardien sur sa ligne (7 m : 0,28 ; 11 m : 0,16 ; 25 m : 0,03) | aucun chiffre réel pour la définition large. Repère : la « big chance » d'Opta, tirs seulement, vaut en moyenne environ 0,35-0,40 d'xG (de mémoire, non sourcé). Le seuil d'Opta n'est pas transposable : dans le modèle du 28a, un gardien qui sort ferme l'angle et fait baisser la chance d'un face-à-face (0,14 à 8 m, gardien à 4 m de sa ligne). À 0,30, presque aucun face-à-face ne passerait. Sondage sur 2 matchs (graine d'audit + 2 et + 3) : 6 et 16 grosses occasions à 0,20 ; 4 et 11 à 0,30 |
| `SEQUENCE_FLOOR` | moitié du seuil (0,10) : une séquence s'ouvre et se ferme à ce niveau | une séquence ne se coupe pas au moindre creux de danger |
| `REACH_LATE_S` | un attaquant en retard de r s sur le ballon libre garde exp(−r / 0,2) de chance de le toucher (0,1 s : 61 % ; 0,4 s : 14 %) | ordre de grandeur, non trouvé |
| `REACH_HORIZON_S`, `REACH_STEP_S` | trajectoire freinée suivie 3 s, par pas de 0,1 s (78 % de la course du ballon) | pas de calcul du moteur |

## Acceptance criteria

- [x] Seuil de grosse occasion proposé avec un nombre plausible par match (aucun chiffre réel pour cette définition large) et validé par le propriétaire avant le code (0,20, validé par délégation ; voir « Constantes »)
- [x] Scène contrôlée : le centre qui traverse la surface et laisse un attaquant à deux doigts du but vide est une grosse occasion sans tir ; un face-à-face stoppé par un tacle salvateur aussi ; un tir de loin sans danger ne l'est pas (`tests/test_v2engine_grosses_occasions.py`)
- [x] Les séquences dangereuses sans tir sont tracées avec leur pic de danger, leur issue et leur origine (`ChanceEvent`, `MatchTrace.chances`)
- [x] Nombre de grosses occasions par match rapporté sur 50 matchs (graine d'audit) ; indicateur ajouté au banc et défini dans `docs/INDICATEURS_V2.md` (7,7 par match)
- [x] Le calcul du danger ne change pas le jeu (empreintes de trace identiques avant et après sur les matchs 0 et 1 de la graine d'audit ; test avec le suivi neutralisé ; buts et tirs identiques entre les deux séries)
- [x] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée (deux exécutions à graine fixée : mêmes `chances`, test ; suite complète 2 576 passés, 14 désélectionnés, 13 min 41 s, attendu 2 567 + 9 nouveaux tests, `.scratch/v2-collectif/mesures/28c-suite.txt` ; aucun fichier V1 ni protégé touché)

## Réalisation

- `v2engine/occasion.py` (nouveau, lecture seule, aucun tirage) : `situation_danger` (danger d'une équipe et joueur qui le porte), `reach_probability` (course au ballon libre sur sa trajectoire freinée, qualité lue au point de contact ; ballon en l'air touchable après son point de chute ; sur une passe adverse en vol, seuls les joueurs qui l'ont lue la disputent, `BallState.readers`), `ChanceTracker` (séquences par équipe, ouvertes et fermées à 0,10, tracées si le pic atteint 0,20 ; un tir ferme la séquence et compte avec sa qualité au départ).
- `v2engine/trace.py` : `ChanceEvent` (début, pic, fin, équipe, joueur et position au pic, danger, issue, origine, tir ou non) et `MatchTrace.chances`.
- `v2engine/match.py` : le suivi est appelé après chaque pas du ballon et clos à chaque coup de sifflet de fin de période ; `_danger_origin` donne l'origine dans le vocabulaire du tir (`_pass_kind` extrait de `_received_as`, sans changement de comportement).
- Banc : `Collector.on_chance` (`scripts/v2_indicators.py`), indicateurs dans `scripts/measure_v2.py` ; définition et seuils dans `docs/INDICATEURS_V2.md`.
- Tests : `tests/test_v2engine_grosses_occasions.py` (9 tests : portée du contact, centre non repris, face-à-face et tacle, tir de loin, tir qui ferme sa séquence, course au ballon en retard, passe adverse lue ou non, danger nul pour la défense et sur ballon mort, jeu inchangé et reproductible sur 10 minutes).

## Mesure en match (50 matchs, graine d'audit 20260923 + i, 08/11/2026, 8 lots, `.scratch/v2-collectif/mesures/28c-lot*.json`, fusion `28c-fusion.py`)

| Indicateur | Valeur |
|---|---|
| Grosses occasions par match | 7,7 (5,6 à 9,4 selon les lots) |
| Sans tir | 52 % |
| Danger moyen au pic | 0,44 |
| Issues | tir 48 % (but 20 %, repoussé 8 %, capté 6 %, contré 5 %, au-dessus 4 %, claqué 3 %, à côté 1 %) ; dégagement 15 % ; ballon non repris 12 % ; danger retombé 9 % ; interception 5 % ; gardien 4 % ; ballon mort 6 % ; tacle 1 % |
| Origines | récupération 36 %, dribble 20 %, passe au sol 17 %, passe en profondeur 13 %, rebond 11 %, passe en retrait 2 % |
| Buts par match, tirs tracés par équipe (contrôle, inchangés) | 3,24 ; 22,9 |

Lecture : 7,7 par match est plausible pour la définition large (repère « big chances » d'Opta, tirs seulement, environ 3 à 5 par match, de mémoire) ; 3,7 grosses occasions par match finissent en tir. Un cinquième finit en but : 1,6 des 3,24 buts par match. La part « récupération » (36 %) vient de ballons perdus par un défenseur ou le gardien à quelques mètres de son but (sonde du match 3 : ballons libres à 3-8 m de la ligne, attaquant au contact). Le calcul est juste : il met en lumière un comportement du moteur (contrôles ratés près du but) à surveiller aux calibrations 22a et 22c, sans réglage ici.

Garde R5 : `occasion` ajouté aux modules qui lisent Pace (`tests/test_v2engine_rayon_attributs.py`, carte des attributs), la course au ballon libre utilisant la même vitesse de pointe que `anticipation.py`.

## Points à vérifier

- **Écart de cadrage** : le chantier `v2-realisme` (`spec.md`, ticket `06a`) attribue au 28c une « étape 0 », xG neutre `occasion_xg` avec une décision D-V12 réservée dans `docs/TRD_V2.md`. Ce point n'est pas dans le texte du ticket 28c : il n'est pas réalisé ici. À trancher par le propriétaire (petit ticket avant `06a`, ou rattachement au `06a`).
- À l'écran, avec `v2-mise-en-scene/02` : vérifier que le pic tracé correspond à un moment lisible (ballon libre près du but, centre au ras d'un attaquant).
- Limites assumées : pas de temps de réaction ni de trajectoire courbe dans la course au ballon libre ; la qualité d'un coéquipier du porteur est lue à sa position, pas au point de réception de la passe.

Première série (même jour), avant la règle des passes adverses lues : 11,8 par match, 69 % sans tir, 36 % de « dégagement » ; un attaquant pouvait couper toute relance adverse sans l'avoir lue. Corrigé avant la seconde série.

## Comments

- 08/11/2026, clôture : expert APPROVED_WITH_RESERVATIONS (un passage, empreinte 374a0eeb) ; QC VALIDÉ ; clôture VALIDÉ (journal `v2-collectif/28c/cloture`).
- Réserve A1 (une même action peut être coupée en deux séquences : fermeture au premier pas sous 0,10) : acceptée. Condition : la traiter ou la mesurer avant que `v2-mise-en-scene/02` et `03` lisent `MatchTrace.chances` (correctif recommandé : fermer après 0,5 à 1 s sous le plancher, tout de suite si la possession change ou si le ballon meurt).
- Réserve A2 (l'origine « récupération » mélange ballon gagné sur l'adversaire et ballon perdu par l'attaque elle-même, vocabulaire hérité du 28b) : acceptée. Condition : ne tirer aucun diagnostic des 36 % avant de séparer les deux cas (dernier toucheur adversaire ou coéquipier) ; même condition de calendrier que A1.
- Facultatif A3 (trajectoire non coupée à la sortie du terrain), A4 (interdiction de retoucher après un contrôle raté, contact d'un non-lecteur sur une passe adverse), A5 (`cut` recalculé par attaquant) : non traités, à reprendre avec A1.
- Réserves acceptées par le propriétaire : délégation permanente du 05/11/2026 (« Considère que je valide automatiquement toutes tes recommandations et celles des expert ») et demande de clôture du 08/11/2026 (« Tu peux clôturer et commit »).

# Architecture — habillage visuel animé des matchs

Découpage figé avant d'écrire la moindre ligne de logique, pour éviter les allers-retours de conception une fois le code commencé. Contexte complet : [ETAT_ACTUEL.md](ETAT_ACTUEL.md), section 6.

## Corrections du 23/09/2026 (brief "contre_attaque carrier movement") — `ANCHOR_STATIC` + `progress` mort

Bug trouvé en expliquant un GIF à Olivier (`support1` immobile dans `contre_attaque` malgré `RoleFrame.progress=0.3`) : `ANCHOR_STATIC` fixe la cible = le départ (voir `_anchor_point`), donc TOUT `progress` non nul déclaré à côté d'un `ANCHOR_STATIC` est du code mort -- `_lerp(début, fin, progress)` avec `début == fin` retourne toujours `début`.

- **Fix initial** : `contre_attaque.support1` passe de `ANCHOR_STATIC` à `ANCHOR_SCORER` (réutilisé tel quel, pas de nouvel anchor créé -- `ANCHOR_ASSIST`/`ANCHOR_SCORER` suffisaient). `support1` récupère le ballon à t=0, progresse vers la zone de tir jusqu'à la passe à `assist` (t_ratio=0.4). **Complété le même jour (voir "suite 3" ci-dessous)** : il ne s'arrête plus net après la passe, il continue d'avancer en décélérant. Tests : `tests/test_templates.py::TestContreAttaqueSupport1Carries`.
- **Audit (`TestNoDeadProgressOnStaticAnchor`)** : le même défaut a été trouvé sur 5 autres gabarits (8 cas au total) -- **tous corrigés le même jour, voir "suite 3" ci-dessous**. La liste d'exclusion (`_KNOWN_DEAD_PROGRESS_OFFENDERS`) est donc vide aujourd'hui.
- **`scripts/preview_motion.py` repensé** : applique désormais `enrich_with_background` PAR DÉFAUT (22 joueurs, plus 2-4 ronds sur un terrain vide) -- `--legacy-minimal` restaure l'ancien comportement, documenté comme outil de debug uniquement. Légende : contour doré 3px = actif, contour fin 1px = décor, couleur de remplissage = équipe (`kits.match_kit_colors`), numéro sous chaque rond (`RosterEntry.numero`), petit disque blanc = porteur du ballon. 30 fps par défaut (`--fps`).
- **GIFs de validation, emplacement CANONIQUE `docs/previews/`** (committés, pas juste générés à la demande) : `une_deux_22players.gif`, `contre_attaque_22players.gif`, `percee_individuelle_22players.gif` -- régénérés avec le pipeline complet (`template → BUILDERS → enrich_with_background → motion.interpolate`).

## Corrections du 23/09/2026 (suite 3) — continuation post-relais + audit role-level + 8 gabarits nettoyés

**Tâche 1 -- `contre_attaque.support1` continue sa course.** Après la passe (t_ratio=0.4), le progress restait figé à 0.3 jusqu'à la fin : un arrêt net, "il a avancé puis a débranché". `RoleFrame(1.0, 0.3)` → `RoleFrame(1.0, 0.4)` : il continue d'avancer en décélérant (~2 m de plus sur 60% de la séquence) au lieu de s'arrêter. **Couplage `ANCHOR_SCORER` documenté comme ASSUMÉ** dans un commentaire au-dessus du rôle (pas corrigé par un nouvel anchor -- `ANCHOR_CARRIER_FORWARD` serait du sur-engineering pour un seul cas) : la direction de `support1` dépend de où tombe `event.zone`, pas d'une direction "devant lui" indépendante -- plausible ici (buteur qui fait son appel globalement dans l'axe), mais pas généralisable tel quel.

**Tâche 2 -- audit passé de gabarit-level à role-level.** `_KNOWN_DEAD_PROGRESS_OFFENDERS` était un `frozenset[str]` de NOMS DE GABARITS : un gabarit exclu l'était ENTIER, masquant tout futur rôle mort ajouté ailleurs dans ce même gabarit. Devenu `frozenset[tuple[str, str]]` de `(gabarit, rôle)`. Angle mort démontré puis corrigé par une preuve en 2 temps (modification temporaire + revert, `git diff --quiet` → 0 après chaque fois) :
1. Régression simulée sur `penalty.support1` (un rôle qui ÉTAIT dans la liste avant la Tâche 3, ne l'est plus après) → le test échoue.
2. Rôle fictif `penalty.support3` (jamais listé) avec `ANCHOR_STATIC` + progress non nul → le test échoue aussi.

**Tâche 3 -- 8 cas corrigés** (plus de détail : commentaires au-dessus de chaque `Role` dans `templates.py`) :

| Gabarit.rôle | Avant | Après | Anchor |
|---|---|---|---|
| `construction_placee.support1` | 0.2/0.25/**0.25** | 0.2/0.25/**0.35** | `ANCHOR_STATIC` → `ANCHOR_SCORER` |
| `recuperation_haute.support1` | 0.3/0.4/**0.4** | 0.3/0.4/**0.5** | `ANCHOR_STATIC` → `ANCHOR_SCORER` |
| `recuperation_haute.support2` | 0.35/0.45/**0.45** | 0.35/0.45/**0.55** | `ANCHOR_STATIC` → `ANCHOR_SCORER` |
| `profondeur_1v1.assist` | 0.1/**0.1** | 0.15/**0.2** | `ANCHOR_STATIC` → `ANCHOR_SCORER` |
| `but_gag.support1` | 0.15/0.15/**0.15** | 0.15/0.15/**0.3** | `ANCHOR_STATIC` → `ANCHOR_SCORER` |
| `but_gag.support2` | 0.1/**0.2**/**0.2** | 0.1/**0.25**/**0.35** | `ANCHOR_STATIC` → `ANCHOR_SCORER` |
| `penalty.support1` | 0.05/0.05/0.05 (inchangé) | 0.05/0.05/0.05 (inchangé) | `ANCHOR_STATIC` → **`ANCHOR_LATERAL_SHIFT`** (nouveau) |
| `penalty.support2` | 0.05/0.05/0.05 (inchangé) | 0.05/0.05/0.05 (inchangé) | `ANCHOR_STATIC` → **`ANCHOR_LATERAL_SHIFT`** (nouveau) |

6 des 8 cas réutilisent `ANCHOR_SCORER` (même logique/mêmes réserves que `contre_attaque.support1` -- couplage assumé, documenté à chaque site). **`penalty` est le cas particulier** : le commentaire du gabarit promettait un "léger frémissement d'anticipation", mathématiquement impossible avec `ANCHOR_STATIC` à N'IMPORTE QUELLE valeur de progress. Nouvel anchor `ANCHOR_LATERAL_SHIFT` (`templates.py`) -- valeurs **corrigées une 2e fois le même jour, voir "suite 4" ci-dessous** (25 cm + progress 0.05 = 1,25 cm réels = 0,14 px, invisible en pratique malgré la correction mathématiquement réelle).

`_KNOWN_DEAD_PROGRESS_OFFENDERS` est maintenant `frozenset()` -- vide, vérifié par audit direct (0 violation sur les 12 gabarits).

**Tâche 4 -- 5 GIFs régénérés** dans `docs/previews/` avec le pipeline patché (`scripts/preview_motion.py`, non retouché ce tour) : les 3 précédents + `penalty_22players.gif` et `recuperation_haute_22players.gif` (les deux fixs les plus sensibles visuellement -- frémissement, pressing).

Tests : `tests/test_templates.py::TestContreAttaqueSupport1Carries::test_contre_attaque_support1_continues_after_the_relay` (delta post-relais > 1,5 m), `TestNoDeadProgressOnStaticAnchor` (restructuré, liste vide). **436 tests verts.**

## Corrections du 23/09/2026 (suite 4) — délai de réaction limité au background + frémissement penalty visible

**Bug de spec trouvé en analysant la trace de `contre_attaque.support1` (suite 3)** : à t_ratio=0.40, la trace via `motion.interpolate` montrait 1,50 m parcourus alors que la keyframe brute en montrait déjà 6,76 m -- écart dû à `motion._start_offset` (comportement 3, délai de réaction déterministe jusqu'à 30% de la durée), appliqué via `_is_primary_role` à TOUT rôle qui n'est ni `"scorer"` ni `"assist"`. Or la spec initiale de la phase 3.1 réservait ce délai aux joueurs **"non impliqués"**, un terme qui désignait les joueurs SANS rôle déclaré par le gabarit -- `support1`/`support2` ont une trajectoire scriptée (`Role.frames`) au même titre que `scorer`/`assist`, ils n'auraient jamais dû hériter du délai. Concrètement : un ailier qui récupère le ballon en contre-attaque et attend 2,16 s avant de bouger, ou un pressing qui démarre en retard, c'est tactiquement incohérent avec le nom même du gabarit.

- **`animation/motion.py`** : `_is_primary_role(role)` (`role in ("scorer", "assist")`) renommée `_reacts_immediately(role)` (`role is not None`) -- TOUT rôle nommé réagit désormais sans délai, seul un joueur réellement sans rôle en garde un. Aucune valeur de délai résiduel proposée pour les rôles scriptés (le brief laissait la porte ouverte à en proposer un si justifié -- pas d'argument trouvé qui contredise la lecture tactique d'Olivier, donc délai nul appliqué tel quel).
  - **Effet de bord observé, à noter** : dans l'architecture actuelle, un joueur avec `role is None` qui apparaît encore dans `Keyframe.players` (donc PAS `sequence.background`) n'existe que dans une `Sequence` construite directement par un gabarit, AVANT `enrich_with_background` -- et sa position y est de toute façon TOUJOURS figée (jamais de rôle = jamais de `RoleFrame` qui la fait varier). Le "délai pour non-impliqué" reste donc correct au sens de la spec, mais est en pratique un no-op sur toute `Sequence` réelle du pipeline actuel : après `enrich_with_background`, ces joueurs sont de toute façon retirés des keyframes et gérés par `BackgroundTrack` (drift, aucun concept de délai). Documenté, pas supprimé (toujours correct, juste inutilisé aujourd'hui).
- **`templates.py`** : `_LATERAL_SHIFT_M` relevé de 0,25 m à 1,5 m (une enjambée), `penalty.support1`/`support2` : progress relevé de 0.05 à 0.4 uniformément. Déplacement final réel : 60 cm, soit 6,88 px sur le canvas 1200×780 -- au-dessus du seuil de 5 px demandé.

Tests : `tests/test_motion.py::TestFrameStateShape::test_named_roles_react_immediately` (remplace l'ancien test qui validait le comportement inverse), `test_reacts_immediately_is_true_for_any_named_role_and_false_for_none` (preuve directe sur la fonction, indépendante de tout gabarit). **437 tests verts.**

**Confirmation demandée (suite 5, même jour)** : preuve mécanique, côté DONNÉES de `templates.py` (pas de comportement `motion.py`), qu'aucun rôle scripté ne dépendait du délai supprimé -- `tests/test_templates.py::TestNoRoleReliesOnReactionDelay`. Deux invariants : (1) un rôle porteur du ballon dès t=0 doit avoir `progress=0.0` à son premier `RoleFrame` ; (2) la séquence de `progress` d'un rôle ne doit jamais décroître (pas de saut en arrière). **2 cas trouvés, PAS des bugs** : `coup_franc.scorer` (progress=0.8) et `penalty.scorer` (progress=0.85) démarrent déjà avancés -- leur position de DÉPART n'est délibérément pas leur position de formation (le tireur est déjà debout près du ballon au coup franc/penalty). Première version : liste d'exclusion `(gabarit, rôle)` -- **rejetée par Olivier (suite 6 ci-dessous)**, remplacée par un champ structurel.

**Corrections du 23/09/2026 (suite 6) — `starts_at_restart` remplace la liste d'exclusion.** Une liste de `(gabarit, rôle)` convient pour de VRAIS bugs qu'on accepte temporairement (l'audit du progress mort, "suite 3") -- mais `coup_franc`/`penalty` ne sont pas des bugs, ce sont des cas légitimes que la règle 1 ne savait pas distinguer : whitelister le RÉSULTAT (le nom du rôle) plutôt que la CAUSE (le gabarit démarre après un coup d'envoi, pas en formation) aurait avalé en silence un futur gabarit légitime au même profil.

- **`Template.starts_at_restart: bool = False`** (nouveau champ) : `True` pour `coup_franc` et `penalty`. `corner` -- aussi un restart -- n'en a PAS besoin : son porteur à t=0 (`assist`) a déjà `progress=0.0` (le gabarit place le tireur de corner directement à son point de départ réel), donc il ne viole rien même sans le flag -- vérifié en le lui ajoutant temporairement (aucun effet, test resté vert) puis en revert.
- **`TestNoRoleReliesOnReactionDelay`** : la règle 1 devient `if not template.starts_at_restart and ...` -- plus de liste, plus d'exception codée en dur. Preuve par échec : violation temporaire injectée sur `contre_attaque.support1` (gabarit non-restart, porteur à t=0) -- échoue comme attendu, puis revert. Note : l'exemple suggéré par Olivier (`contre_attaque.scorer`) ne convenait pas pour cette preuve -- `scorer` ne possède le ballon qu'à t_ratio=1.0 dans ce gabarit, pas à t=0 -- `support1` est le porteur réel à t=0.

**438 tests verts.**

## Corrections du 23/09/2026 (bilan étape 2.2)

1. **`goal_diff_after` réellement cassé, corrigé.** Le champ existait dans `TemplateContext` mais n'était lu par AUCUNE fonction `context_score` -- pondérer par score n'avait donc jamais d'effet, quelle que soit la valeur transmise. Renommé `goal_diff_before` (c'est le rapport de force AVANT le but qui influence le style de jeu, pas après), branché sur `_urgency_factor` dans `contre_attaque`/`construction_placee`/`recuperation_haute`/`percee_individuelle`. `sequence_generator.generate_sequence` reçoit maintenant un `MatchState` (`goal_diff_before`, `minute`, `competition_type`) au lieu de toujours passer 0. Effet vérifié par un test statistique (chi² d'homogénéité, seuil table standard -- pas de scipy dans ce projet) sur 500 tirages par contexte, voir `tests/test_templates.py::TestPickTemplateReactsToScore`.
2. **`scripts/preview_templates.py` refait en scène complète** : 22 joueurs (les deux équipes, vraies positions via `pitch_layout.place_starting_xi` + `spatial.placed_player_to_normalized`) + ballon, échantillonnés à t=0/50/100% + une bande temporelle du ballon. A révélé un vrai bug de composition (le référentiel normalisé est RELATIF À L'ÉQUIPE -- x=0 toujours "son propre but" -- donc afficher les deux équipes sans miroir les superposait), corrigé.
3. **4 gabarits enrichis** (`corner`, `penalty`, `but_gag`, `recuperation_haute` -- les plus pauvres identifiés par l'audit, `recuperation_haute` n'avait que 2 keyframes/1 rôle) : tous à ≥3 keyframes et ≥3 rôles nommés désormais, avec une phase de préparation visible. Voir `tests/test_templates.py::TestTemplateRichness`.
4. **`spatial.py`** : commentaire renforcé juste au-dessus du bloc de ré-export (pas seulement dans le docstring de module) -- l'implémentation de la grille/des conversions reste dans `pitch_geometry.py`.
5. **Réponse à la question posée avant la phase 3** : les gabarits ne produisent QUE des keyframes discrets (`build_from_template` ne fait jamais d'interpolation -- son unique boucle cherche une correspondance EXACTE de `t_ratio`, sans repli intermédiaire). La seule interpolation qui existe dans ce projet vit dans `scripts/preview_templates.py` (`_sample_players_at`/`_sample_ball_at`), explicitement documentée comme un outil d'aperçu OFFLINE, pas une partie du contrat `Sequence`/`Keyframe`. **`motion.py` reste donc à juste titre supprimé -- passage en phase 3 validé.**

## Phase 3.1 — `motion.py` (créé le 23/09/2026)

`interpolate(sequence, t) -> FrameState` : interpolation continue des joueurs entre les keyframes discrets d'une `Sequence` -- consommateur pur (`templates.py`/`sequence_generator.py` non touchés). 5 comportements implémentés et testés séparément (`tests/test_motion.py`, 53 tests, dont les 3 tests obligatoires -- continuité, déterminisme, non-collision -- tous verts) :

1. **Bézier cubique ease-in-out** (mêmes points de contrôle que CSS `cubic-bezier(0.42, 0, 0.58, 1)`), résolue par Newton-Raphson -- accélère puis décélère entre deux keyframes, jamais linéaire.
2. **Vitesse max par poste** (GK 6 m/s, DC 7, MDC/MC 8, MOC/ailiers/BU 9, convertie via la longueur du terrain, 105 m). Quand un segment de gabarit exigerait une vitesse moyenne dépassant 55% du plafond (le ratio pic/moyenne mesuré empiriquement pour cette courbe de Bézier est ≈1,72 -- 55% laisse une marge de sécurité), repli sur un mouvement LINÉAIRE à vitesse constante : seule façon de garantir qu'aucun instant ne dépasse jamais le plafond, y compris quand un gabarit demande un trajet trop long pour le temps imparti.
3. **`start_offset` déterministe par joueur** (hash sha256, même principe que `events._deterministic_rng`), dans [0, 0.3×durée] -- nul pour les rôles "scorer"/"assist" (réagissent sans délai), appliqué à tous les autres (dont les rôles "support*", voir 4).
4. **Off-ball runs** : les rôles "support*" (le 3e/4e rôle des gabarits enrichis, voir "Corrections du 23/09/2026" point 3) sont traités comme des coureurs non prioritaires -- leur trajectoire cohérente avec le gabarit est déjà encodée dans `Role.frames` (`templates.py`), `motion.py` leur applique juste le décalage temporel du point 3.
5. **Évitement minimal** : répulsion latérale déterministe (pas de pathfinding) quand deux joueurs passent sous 1,5 m, quelques passes de relaxation -- marge large avant le seuil de test (jamais < 0,5 m sur 12 gabarits × 100 tirages).

**Écart initial corrigé le 23/09/2026 (voir "Corrections du 23/09/2026 (suite)" ci-dessous) : `Sequence` porte maintenant `roster`, `interpolate` ne prend plus que `(sequence, t)`.**

`FrameState.ball` est toujours `None` dans cette phase (géré par `ball.py`, phase 3.2), mais **le TYPE du champ est déjà `BallState | None`** (corrigé le 23/09/2026, "Point D" du brief -- il était par erreur typé `ball: None = None`, ce qui aurait fait échouer le type-checking dès que `ball.py` y assignerait un vrai `BallState`).

### Point B (23/09/2026, brief suivant) : segment "impossible" -- documenté, pas corrigé

Le repli linéaire (comportement 2 ci-dessus) garantit qu'aucun INSTANT d'un segment ne dépasse `v_max`, mais PAS que la distance soit couverte à temps : si `v_max × durée < distance`, le joueur reste en retard jusqu'à `elapsed = duration`, puis **saute instantanément** à la position du keyframe suivant à la transition -- vérifié avec un keyframe artificiel (tout le terrain en 0,1 s, très au-delà de `v_max`) dans `tests/test_motion.py::TestImpossibleSegment` : position toujours < 0,99 juste avant l'échéance, exactement 1,0 pile à l'échéance, avec un pic de vitesse (différence finie) de plusieurs milliers d'unités/s à cet instant précis. Documenté en tête de `motion.py` ("Limite connue et non corrigée") plutôt que corrigé : aucun des 12 gabarits actuels n'en a besoin (voir table ci-dessous), pas de raison de complexifier sans cas réel -- mais `ball.py` aura probablement la même contrainte à anticiper.

Marge réelle par gabarit (ratio vitesse moyenne exigée / `v_max`, sur le rôle/segment le plus exigeant, effectif synthétique de test) -- calculée et figée par `tests/test_templates.py::TestSegmentSpeedHeadroom` :

| Gabarit | Ratio (v exigée / v_max) |
|---|---|
| `une_deux` | **0.76** -- le plus proche du seuil critique (1.0) |
| `debordement_centre_tete` | 0.64 |
| `recuperation_haute` | 0.61 |
| `but_gag` | 0.58 |
| `corner` | 0.58 |
| `decalage_enroulee` | 0.50 |
| `percee_individuelle` | 0.44 |
| `profondeur_1v1` | 0.43 |
| `contre_attaque` | 0.35 |
| `construction_placee` | 0.27 |
| `penalty` | 0.21 |
| `coup_franc` | 0.17 |

`une_deux` est le seul au-dessus du seuil ease-safe (0,55, voir comportement 2) qui s'approche vraiment du seuil critique (1.0) -- reste 24% de marge, aucun gabarit n'est aujourd'hui "impossible".

`scripts/preview_motion.py` exporte une `Sequence` interpolée en PNG toutes les 0,1 s + un GIF animé (le plus lisible), vecteurs de vitesse et porteur du ballon affichés -- audité visuellement sur `corner` (accélération/décélération, décalage du `support1`, convergence propre du buteur vers `event.zone`), et sur `une_deux`/`contre_attaque`/`percee_individuelle` (Point C du brief du 23/09/2026, patterns aux caractéristiques différentes : échange de position, groupe en mouvement, slalom).

## Corrections du 23/09/2026 (suite) — `Sequence.roster`

L'écart assumé ci-dessus (`postes`/`player_roles` optionnels) était un contournement qui aurait dû se propager à chaque futur consommateur de `Sequence` (`ball.py`, le rendu JS...), chacun devant se souvenir de reconstruire ces dicts depuis une `Lineup`. Cause corrigée plutôt que le symptôme :

- **`animation/types.py`** : nouvelle dataclass `RosterEntry(nom, poste, role)` et nouveau champ `Sequence.roster: dict[PlayerId, RosterEntry]`. `__post_init__` gagne un 3e invariant vérifié à la construction (comme les deux existants) : chaque `PlayerId` référencé par les keyframes DOIT avoir une entrée dans `roster`, sinon `ValueError` immédiat -- une `Sequence` mal formée (compo mal transmise) ne peut plus exister, encore moins atteindre `interpolate` ou une frame 60 quelconque. `to_json()` sérialise désormais aussi `roster`.
- **`animation/templates.py`** (`build_from_template`) : remplit `roster` pour les 11 joueurs de `start_positions`, à partir de la `lineup` déjà reçue (poste + nom) et des rôles déjà résolus (`role_ids` inversé) -- aucune information nouvelle, seulement rendue explicite dans le contrat plutôt qu'implicite dans `meta['roles']` + une `Lineup` externe.
- **`animation/motion.py`** : `interpolate(sequence, t)` -- `postes`/`player_roles` ont disparu, poste et rôle sont lus directement sur `sequence.roster[player_id]`. `resolve_postes`/`resolve_player_roles` supprimées (devenues inutiles, `Sequence` est auto-descriptive).
- `numéro`/`team_side` (envisagés un temps pour `RosterEntry`) écartés : `Player` ne porte pas de numéro de maillot dans le modèle de données actuel, et seule l'équipe qui marque est suivie par une `Sequence` (`team_side` serait constant pour toute entrée, donc sans valeur informative). À ajouter le jour où un vrai besoin (numéro affiché par le rendu, affichage de l'équipe adverse) se présente -- pas avant.

Tests : `tests/test_types.py::TestRosterCompleteness` (dont `test_forgetting_to_fill_the_roster_fails_at_construction_not_at_frame_sixty`, qui prouve que l'oubli est détecté à la construction, avant même qu'`interpolate` puisse être appelé). `tests/test_motion.py` simplifié en conséquence (plus de `postes=`/`player_roles=` à construire dans les tests).

## Corrections du 23/09/2026 (suite 2) — les 22 joueurs + numéro de maillot

Une `Sequence` de gabarit ne suit que ses 2-4 joueurs actifs (buteur, passeur, support*) -- rendue telle quelle en phase 4, la scène montrerait 3 ronds bougeant sur un terrain vide, pas du Football Manager (FM montre toujours les 22, dont 18 en arrière-plan). Décision : ne PAS toucher aux gabarits (ils restent minimalistes, décrivent l'action, pas la scène) -- `sequence_generator.enrich_with_background` complète une `Sequence` déjà construite.

- **`animation/types.py`** : nouvelle dataclass `BackgroundTrack(start, drift)` et nouveau champ `Sequence.background: dict[PlayerId, BackgroundTrack] = {}` (seul champ à défaut de toute la classe -- une `Sequence` fraîche d'un gabarit est valide sans enrichissement). `RosterEntry` gagne `numero: int` et `team_side: str` ("scorer" | "opponent", jamais "home"/"away" -- inconnu à ce niveau du pipeline). `__post_init__` gagne 2 invariants : un joueur ne peut pas être suivi à la fois par les keyframes ET par `background` (sinon quelle est sa "vraie" position ?), et `roster` doit couvrir l'UNION des deux (pas seulement les keyframes comme avant).
- **`animation/templates.py`** : nouvelle fonction `numeros_by_player_id(lineup)` -- gardien=1 puis les 10 de champ triés par (groupe de poste, nom). Délibérément PAS l'index brut de `lineup.players` (ce que demandait le bilan) : cet ordre reflète l'algo de `lineup._assign_slots` (tri par note décroissante), le gardien n'y est PAS garanti en première position -- un numéro dérivé de cet ordre n'aurait "GK=1" que par coïncidence, pas de façon fiable. `build_from_template` appelle cette fonction et fixe `team_side="scorer"` pour les 11 de l'équipe qui marque.
- **`animation/sequence_generator.py`** : nouvelle fonction `enrich_with_background(sequence, opponent_lineup) -> Sequence`. Signature volontairement plus courte que celle envisagée dans le bilan (`sequence, lineup_home, lineup_away, pitch_layout_state`) : `sequence.roster`/`sequence.keyframes[0]` porte déjà tout ce qu'il faut sur l'équipe qui marque (positions de formation des 18 non-actifs = leur position figée dans les keyframes, poste/nom déjà dans `roster`) -- inutile de redemander `lineup`/`pitch_layout_state` de cette équipe, seul `opponent_lineup` (jamais vu par `generate_sequence`) manquait vraiment. Étapes : (1) identifie les actifs via `roster[id].role is not None` ; (2) les retire des `Keyframe.players` (invariant "un seul mode de suivi" ci-dessus) ; (3) place les 11 adverses (`place_starting_xi` + `placed_player_to_normalized(attacking_up=True)` + miroir en x, même principe que `scripts/preview_motion.py._away_static_points`) ; (4) calcule un `BackgroundTrack` par joueur décor des DEUX équipes (`_tactical_drift`, voir table ci-dessous) ; (5) étend `roster` avec les 11 adverses.
- **`animation/motion.py`** : `interpolate` couvre maintenant `keyframes[0].players ∪ background` dans un seul `FrameState`, tous passés ensemble par `_apply_avoidance` (22 joueurs, pas 2-4). Un joueur décor n'a ni Bézier ni vitesse plafonnée par poste : juste `start + drift × progress`, `progress` suivant la même courbe ease-in-out que les actifs (`_ease_progress`) -- l'amplitude étant déjà bornée à la construction, aucun plafond de vitesse n'est nécessaire.

### Point 2 (23/09/2026, brief suivant) : drift PAR RÔLE TACTIQUE, pas uniforme

Première version (`_drift_for`, ci-dessus) : tout le monde dérive vers le ballon, uniformément par groupe GK/DEF/MID/ATT. Olivier a raison de la rejeter -- un ailier côté opposé au ballon qui s'y précipite, ou un latéral qui monte alors que son équipe défend, ça "tique" à l'œil d'un fan de foot. Remplacée par `_tactical_drift` (poste exact, pas juste le groupe) + `_cb_line_drift` (les DC bougent en BLOC, jamais individuellement) :

| Poste | Côté ballon ? | Cible / logique | x | y |
|---|---|---|---|---|
| GK | -- | latéral suivant le ballon, x figé | 0 | ≤ 0.02, vers `ball_y` |
| DC | -- | **ligne entière** (un seul drift partagé, `_cb_line_drift`) vers le côté ballon | 0 | ≤ 0.02, vers `ball_y`, partagé par toute la ligne |
| LB/RB | même côté, équipe qui attaque (`team_side="scorer"`) | monte | 0.03-0.06, vers l'avant | ≤ 0.01, vers `ball_y` |
| LB/RB | même côté, équipe qui défend (`team_side="opponent"`) | reste, couvre sur place | 0 | ≤ 0.01, vers `ball_y` |
| LB/RB | côté opposé | rentre dans l'axe (rest defense) | 0 | ≤ 0.02, vers 0.5 (jamais vers le ballon) |
| MDC/MC/MOC | -- | rapprochement du porteur (MOC non distingué du brief) | 0.02-0.04, vers `ball_x` | ≤ 0.015, vers `ball_y` |
| AG/AD | même côté | soutien proche du porteur, dans le couloir | 0.02-0.04, vers `ball_x` | ≤ 0.01 (moins qu'un MC -- reste dans son couloir) |
| AG/AD | côté opposé | **choix seedé (50/50, par joueur)** : tient la largeur OU appel en profondeur | 0 (tient) ou 0.02-0.04 vers l'avant (appel) | ≤ 0.01, TOUJOURS en s'écartant du centre si "tient" (jamais vers le ballon) |
| BU/SA/ATT | -- | **choix seedé (50/50)** : reste haut OU appel | 0 (reste) ou 0.02-0.04 vers l'avant (appel) | 0, jamais vers le ballon |

"Vers l'avant" = `_forward_sign(team_side)` : +1 pour l'équipe qui marque (son but adverse est à x=1 dans le référentiel partagé), -1 pour l'adversaire -- jamais vers son propre but, quel que soit le côté du ballon. "Même côté"/"côté opposé" : comparaison de `_side_of(y)` (gauche/droite de `y=0.5`) entre la position de départ du joueur et celle du ballon -- une approximation grossière (un vrai "côté" tient compte de bien plus que `y`), assumée pour rester dans l'esprit "pas d'IA, juste cohérent" de la consigne. `team_side="opponent"` désigne dans ce modèle l'équipe qui ENCAISSE le but -- toujours en phase défensive sur CETTE séquence précise (le modèle ne capture qu'une seule phase de jeu) : ses latéraux ne "montent" donc jamais, même côté ballon ou non (limite assumée, pas un vrai modèle de phases de jeu).

Amplitude déterministe par joueur (hash sha256, `_deterministic_unit`, même principe que `motion._start_offset`) dans chaque fourchette, jamais aléatoire. Borne globale `_MAX_DRIFT_MAGNITUDE = 0.05` (~5% du terrain) toujours appliquée en dernier recours. Tests : `tests/test_sequence_generator.py::TestTacticalDrift` (invariants par rôle, y compris "jamais vers le ballon" pour l'ailier/latéral opposé et "jamais vers son propre but" pour BU/ailier en appel) -- le test statistique sur 100 buts et l'acceptation ≥20 joueurs (ci-dessus) restent verts avec ces nouvelles règles.

Tests : `tests/test_types.py::TestBackground` (invariants de construction), `tests/test_motion.py::TestBackgroundInterpolation` (dispatch actif/décor, borne de drift jamais dépassée), `tests/test_sequence_generator.py::TestEnrichWithBackground` -- dont le test d'acceptation du bilan (`test_acceptance_at_least_20_players_are_referenced`, toujours exactement 22 dans le cas ordinaire) et le test statistique sur 100 buts (`test_drift_statistics_over_100_goals_stay_close_to_formation_positions`, amplitude de drift toujours ≤ 5% du terrain).

## Décisions déjà prises (rappel)

- **Interface cible : Streamlit** (`app.py`), pas la PWA React.
- **Habillage, pas remplacement** : le moteur Poisson (`simulation.py`/`events.py`) reste l'unique source du résultat (score, buteur, minute, carton...). Ce chantier ajoute une couche de mouvement visuel par-dessus un résultat déjà décidé, jamais l'inverse.
- **`events.py` porte lui-même le champ `zone`** (décision du 22/09/2026, révisant l'invariant initial "jamais modifié" ci-dessous) : chaque événement (`GoalEvent`, `CardEvent`, `SubstitutionEvent`, `InjuryEvent`, `PenaltyMissedEvent`) a maintenant un champ `zone: Zone | None` (et `assist_zone` pour un but), peuplé par un générateur aléatoire LOCAL et indépendant du flux `random`/`np.random` partagé (voir `events._deterministic_rng`) -- les tirages existants (buteur, minute, carton...) restent bit-identiques, vérifié sur 1000 matchs (`tests/test_events_zone.py::TestNoRegression`). Le référentiel géométrique lui-même (`Zone`, `zone_of`, `center_of`, `zones_in_third`, `to_canvas_px`) a été promu dans `ligue1sim.pitch_geometry`, un module PARTAGÉ (ni dans `animation/`, ni dépendant d'`events.py`), pour qu'`events.py` puisse l'utiliser sans dépendre de la couche cosmétique -- voir la version corrigée de l'invariant 1 plus bas.
- **`Sequence` est LE pivot entre moteur et rendu** (décision du 22/09/2026) : un empilement de `Keyframe` déjà continus (ballon + tous les joueurs suivis, au même instant `t`), sérialisable via `Sequence.to_json()`. Conséquence directe, tranchée le même jour : **`motion.py`, `ball.py` et `render/payload.py` sont supprimés**, devenus redondants (ils produisaient en plusieurs étages exactement ce que `Sequence`/`Keyframe`/`to_json()` portent maintenant directement).
- **`sequences.py` renommé en `types.py`** (décision du 22/09/2026, à la demande d'Olivier) : le fichier ne construit aucune séquence (ça, c'est `templates.py`), il ne fait que définir la FORME du contrat (`Sequence`/`Keyframe`/`BallState`/`PlayerId`) -- son nom ne doit pas laisser croire le contraire. Un seul module porte ces dataclasses, jamais dupliquées ailleurs.
- **`animation/spatial.py` restreint** (décision du 22/09/2026) : `SpatialEvent`/`build_spatial_event` supprimés (absorbés par `templates.py`, qui utilise directement `event.zone`/`event.assist_zone`). Ne reste que le besoin résiduel réel : la conversion entre le référentiel de `pitch_layout.py` et le référentiel normalisé (`placed_player_to_normalized`, exactement inversible -- voir `tests/test_spatial.py`). Les conversions pixel et la grille de zones restent dans `pitch_geometry.py` (partagé avec `events.py`, voir plus bas) et sont RÉ-EXPORTÉES depuis `spatial.py` pour rester accessibles de là.
- **`sequence_generator.py` créé** (décision du 22/09/2026, étape 2.3 de la feuille de route) : `generate_sequence(event, lineup, pitch_layout_state, rng)` choisit un gabarit (`templates.pick_template`, via un `rng` déterministe construit à partir de `(match_id, event_index)`) et l'exécute, en ajoutant la minute réelle aux métadonnées de la `Sequence` produite. Le calage buteur/passeur est déjà garanti par `templates.build_from_template` lui-même, rien à refaire ici.
- **`scripts/preview_templates.py` créé** : audit visuel des 12 gabarits (PNG par gabarit + montage 4x3), a immédiatement révélé un vrai défaut (`but_gag` ne terminait pas sur la zone réelle du but faute d'un porteur de ballon désigné au dernier keyframe) -- corrigé le jour même. Constat de l'audit : plusieurs gabarits à 2 rôles (`corner`, `debordement_centre_tete`, `decalage_enroulee`, `profondeur_1v1`) se ressemblent visuellement (une ligne droite convergeant vers le but) sur l'effectif synthétique de test -- à réévaluer une fois de vraies positions de formation utilisées (voir `spatial.placed_player_to_normalized`), pas encore un problème confirmé.

## Décision de ce document : un sous-package dédié

Les nouveaux modules ne rejoignent **pas** la racine plate de `src/ligue1sim/` (déjà 17 modules). Ils vivent dans `src/ligue1sim/animation/`, un sous-package à part :

```
src/ligue1sim/
├── animation/              # NOUVEAU — tout ce document
│   ├── __init__.py         # orchestrateur du pipeline (point d'entrée unique)
│   ├── spatial.py           # restreint (22/09) : conversion pitch_layout <-> normalisé + ré-export pitch_geometry
│   ├── templates.py         # 12 gabarits, implémenté
│   ├── sequence_generator.py # NOUVEAU (22/09) : choix du gabarit + calage sur le résultat connu
│   ├── types.py              # renommé de sequences.py (22/09) : Sequence/Keyframe/BallState + to_json
│   └── render/
│       ├── __init__.py
│       └── component.py     # consomme Sequence directement (plus de payload.py séparé)
├── clubs.py                 # inchangé
├── events.py                 # porte le champ `zone` depuis le 22/09/2026 (voir plus haut) — tirages inchangés, vérifié
├── simulation.py              # inchangé — jamais touché (aucun tirage de score/résultat modifié)
├── pitch_geometry.py            # NOUVEAU — référentiel spatial partagé (events.py ET animation/)
├── pitch_layout.py             # inchangé — réutilisé tel quel (positions de formation)
└── ...

scripts/
├── inspect_event_zones.py   # heatmap texte des zones d'événements (events.py)
└── preview_templates.py     # NOUVEAU (22/09) : audit visuel PNG des 12 gabarits
```

**Raison** : garder une frontière nette entre le moteur (testé, calibré sur des centaines de saisons, voir `simulation.py`) et la couche cosmétique. Ça rend explicite qu'on peut supprimer tout `animation/` sans rien casser ailleurs, et ça évite qu'un futur changement moteur touche accidentellement à du code d'affichage. **Point à valider avec Olivier avant de créer les fichiers** — c'est un choix, pas une contrainte technique.

---

## Le pipeline, vue d'ensemble

```
GoalEvent (+ CardEvent / SubstitutionEvent /       ← ligue1sim.events, décidé
InjuryEvent / PenaltyMissedEvent, non couverts        par le moteur Poisson,
par templates.py pour l'instant)                      jamais modifié ici
        │
        ▼
┌─────────────────┐
│   spatial.py     │  PlacedPlayer (pitch_layout, 0-100) -> PitchPoint
│  (restreint,     │  (normalisé, 0-1) via placed_player_to_normalized --
│   implémenté)    │  seul le référentiel change, aucune notion de temps.
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│sequence_generator │  Choisit un gabarit (templates.pick_template, via un
│      .py          │  rng déterministe (match_id, event_index)) et
│  → Sequence        │  l'exécute (templates.BUILDERS) -- ajoute la minute
└────────┬─────────┘  réelle aux métadonnées de la Sequence produite.
         │
         ▼
┌─────────────────┐
│render/component.py│ st.components.v1.html — composant HTML/JS/canvas
│ → render_sequence()│ embarqué dans app.py, boucle requestAnimationFrame
└─────────────────┘  côté JS pour interpoler entre les keyframes.
```

**Changement du 22/09/2026 (en plusieurs temps) :**
1. `motion.py`/`ball.py`/`render/payload.py` supprimés. Devenus redondants dès que `Sequence` (aujourd'hui `types.py`, ex-`sequences.py`) a embarqué directement des `Keyframe` déjà continus (ballon + joueurs + `to_json()`).
2. `templates.py` construit directement des `Sequence` (12 fonctions `build_xxx`) -- **`sequences.build_sequence` n'existera donc jamais**, et `sequences.py` a été renommé `types.py` (il ne fait que définir la forme du contrat).
3. `spatial.py` restreint : `SpatialEvent`/`build_spatial_event` supprimés (absorbés par `templates.py`), ne reste que la conversion `pitch_layout` <-> normalisé (besoin résiduel réel, confirmé).
4. `sequence_generator.py` créé : porte le choix du gabarit + le calage sur le résultat connu (étape 2.3 de la feuille de route).

Le pipeline pour un BUT est donc à 3 étages réels (`spatial.py` -> `sequence_generator.py` -> `render/component.py`). Cartons/remplacements/blessures n'ont encore aucun gabarit (`templates.py` ne couvre que `GoalEvent`).

Chaque étage est une fonction pure : mêmes entrées → mêmes sorties, testable isolément sans Streamlit ni fichier Excel ouvert.

---

## Invariants (à ne jamais violer)

1. **Les tirages du moteur Poisson ne sont jamais modifiés** (révisé le 22/09/2026). `simulation.py` reste intouché. `events.py` porte désormais lui-même le champ `zone` (voir "Décisions déjà prises" plus haut), et `sequence_generator.py` choisit un gabarit, mais ces deux calculs passent TOUJOURS par un générateur aléatoire LOCAL (`events._deterministic_rng`, `sequence_generator.deterministic_rng`), jamais par le flux `random`/`np.random` partagé qui pilote le buteur/la minute/le carton — non-régression vérifiée sur 1000 matchs (`tests/test_events_zone.py`). Le référentiel géométrique (`Zone`, `zone_of`...) vit dans `ligue1sim.pitch_geometry`, un module PARTAGÉ, pas dans `animation/` : `events.py` en dépend, mais PAS d'`animation/` — supprimer tout `animation/` ne casse toujours rien ailleurs.
2. **Aucun étage ne peut changer le résultat.** Score, buteur, minute, carton : ce sont des entrées du pipeline, jamais recalculées. `sequence_generator.generate_sequence` cale d'ailleurs explicitement le buteur/le passeur sur ce que le moteur a décidé (voir `templates.build_from_template`, qui termine toujours le rôle "scorer"/"assist" exactement sur `event.zone`/`event.assist_zone`). Un bug dans `animation/` (ou dans le calcul de zone d'`events.py`) peut au pire produire un mouvement/une zone absurde à l'écran, jamais un score différent.
3. **Référentiel de coordonnées unique, normalisé** : x, y ∈ [0, 1], origine au coin **bas-gauche**, axe x orienté vers le **but adverse** (relatif au sens d'attaque, pas à un côté fixe de l'écran — même principe que `pitch_layout.attacking_up`). Vit dans `ligue1sim.pitch_geometry` (ré-exporté par `animation/spatial.py`, voir invariant 1). **Ce référentiel est différent de celui de `pitch_layout.py`** (terrain vertical, x=latéral/y=profondeur en 0-100) : la conversion entre les deux est désormais explicite et implémentée (`spatial.placed_player_to_normalized`, exactement inversible — voir `tests/test_spatial.py`), jamais une réutilisation directe des valeurs brutes. La projection finale vers des pixels canvas (1200×780 par défaut, paramétrable) est la seule responsabilité du rendu (`render/`)/des scripts d'audit visuel (`scripts/preview_templates.py`), jamais des étages de calcul — voir `pitch_geometry.to_canvas_px`.
4. **Les compositions placées sont calculées une seule fois** par match (via `pitch_layout.place_starting_xi`, converties par `spatial.placed_player_to_normalized`), puis passées en paramètre (`start_positions`) aux étages qui en ont besoin — jamais recalculées à chaque événement.
5. **Le contrat JSON est `Sequence.to_json()`, la seule chose que le JS connaît** (révisé le 22/09/2026 : porté directement par `Sequence`, `render/payload.py` supprimé — voir "Changement du 22/09/2026" plus haut). Le canvas ne doit jamais avoir besoin des dataclasses Python (`Sequence`, `Keyframe`, `BallState`...) : uniquement la forme aplatie que `to_json()` produit.
6. **Chaque joueur suivi a une position à CHAQUE `Keyframe` d'une `Sequence`**, impliqué dans l'action ou non (invariant vérifié à la construction, voir `types.py` : tous les `Keyframe.players` d'une même `Sequence` partagent exactement le même ensemble de joueurs). Un joueur non impliqué garde une position fixe (sa position de formation) plutôt que de disparaître du rendu — c'est ce que fait déjà `templates.build_from_template` pour chaque gabarit.
7. **Keyframes creux, pas un échantillonnage dense.** Quelques `Keyframe` par mouvement (pas une image par frame, 2 à 4 en pratique pour les 12 gabarits actuels) ; l'interpolation/easing se fera côté JS avec `requestAnimationFrame`, comme le ferait n'importe quelle bibliothèque d'animation. Charge JSON minimale, cohérent avec la façon dont un moteur d'animation interpole déjà nativement entre deux keyframes.

---

## Détail par module

### `ligue1sim.pitch_geometry` (module PARTAGÉ, pas dans `animation/`)

**Responsabilité** : le référentiel spatial canonique de tout le projet — implémenté, testé (`tests/test_pitch_geometry.py`, 37 tests) et déjà consommé par `events.py` en production (pas seulement par `animation/`, voir invariant 1). Volontairement en dehors d'`animation/` pour que `events.py` puisse s'en servir sans dépendre de la couche cosmétique.

```python
# Référentiel normalisé : x, y ∈ [0, 1], origine bas-gauche, x vers le but
# adverse. Indépendant de celui de pitch_layout.py (0-100, vertical).
PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0
GRID_COLUMNS = 12  # axe x, multiple de 3 pour un découpage en tiers exact
GRID_ROWS = 8       # axe y
THIRD_DEFENSIVE, THIRD_MIDDLE, THIRD_ATTACKING = "defensive", "middle", "attacking"
CANVAS_WIDTH_PX, CANVAS_HEIGHT_PX = 1200, 780

@dataclass(frozen=True)
class PitchPoint:
    x: float  # 0.0-1.0, progression vers le but adverse
    y: float  # 0.0-1.0, latéral (0 = touche basse, 1 = touche haute)

@dataclass(frozen=True)
class Zone:
    col: int  # 0..GRID_COLUMNS-1
    row: int  # 0..GRID_ROWS-1

def zone_of(x: float, y: float, *, columns=GRID_COLUMNS, rows=GRID_ROWS) -> Zone: ...
def center_of(zone: Zone, *, columns=GRID_COLUMNS, rows=GRID_ROWS) -> PitchPoint: ...
def zones_in_third(third: str, *, columns=GRID_COLUMNS, rows=GRID_ROWS) -> tuple[Zone, ...]: ...
def to_canvas_px(point: PitchPoint, *, canvas_width=CANVAS_WIDTH_PX, canvas_height=CANVAS_HEIGHT_PX) -> tuple[float, float]: ...
```

### `ligue1sim.events` — champ `zone` (implémenté, hors `animation/`)

**Responsabilité additionnelle** (22/09/2026) : chaque événement porte maintenant sa propre zone, calculée par une RNG locale indépendante (`_deterministic_rng(match_id, minute, player_id)`, hash sha256 -> `random.Random`). Règles par type, voir `tests/test_events_zone.py::TestZoneRules` et `scripts/inspect_event_zones.py` pour la vérification visuelle :

- **but (hors penalty)** → `_shot_zone` : les 3 dernières colonnes (proche surface), ligne aléatoire.
- **but sur penalty / penalty manqué** → `PENALTY_SPOT_ZONE`, fixe (point de penalty réglementaire, pas un tirage).
- **passe décisive** (`GoalEvent.assist_zone`) → `_assist_zone` : 1 à 3 colonnes en retrait de la zone de tir, dérive latérale de ±1 ligne.
- **carton / blessure** → `_uniform_pitch_zone` : n'importe où sur le terrain.
- **remplacement** → `_technical_area_zone` : proche de la ligne médiane, sur une touche (ligne 0 ou GRID_ROWS-1).

`generate_match_events` accepte un `match_id: str | None = None` (synthétisé depuis clubs+score si omis) qui alimente ce hash — non-régression stricte des tirages existants vérifiée sur 1000 matchs (`tests/test_events_zone.py::TestNoRegression`, contre `tests/fixtures/event_regression_snapshot.json`).

### `animation/spatial.py` (restreint et implémenté le 22/09/2026)

**Décision tranchée** : `SpatialEvent`/`build_spatial_event` supprimés -- leur rôle était entièrement absorbé par `templates.py` (qui utilise directement `event.zone`/`event.assist_zone`). Ne reste que le besoin résiduel réel : la conversion de référentiel, plus les ré-exports de `pitch_geometry` pour que ces noms restent accessibles depuis `spatial.py` (implémentation réelle inchangée, toujours dans `pitch_geometry.py` -- voir invariant 1, `events.py` ne doit jamais dépendre d'`animation/`).

```python
# Ré-exportés depuis pitch_geometry (implémentation là-bas, pas ici) :
# PitchPoint, Zone, zone_of, center_of, zones_in_third, to_canvas_px,
# GRID_COLUMNS, GRID_ROWS, THIRD_*, CANVAS_*_PX, PITCH_*_M

@dataclass(frozen=True)
class PitchLayoutState:
    placed_players: tuple[PlacedPlayer, ...]  # sortie de pitch_layout.place_starting_xi
    attacking_up: bool  # même valeur que celle passée à place_starting_xi

def placed_player_to_normalized(placed: PlacedPlayer, *, attacking_up: bool) -> PitchPoint: ...
def normalized_to_placed_player_xy(point: PitchPoint, *, attacking_up: bool) -> tuple[float, float]: ...
```

`placed_player_to_normalized` est une transformation purement linéaire (mise à l'échelle + inversion de l'axe de progression selon `attacking_up`), donc exactement inversible -- `normalized_to_placed_player_xy` en est l'inverse exact, testé (`tests/test_spatial.py`, 20 tests) : aller-retour exact sur des points arbitraires, et les 11 positions d'une vraie formation 4-3-3 tombent dans des zones cohérentes (gardien dans le tiers défensif, progression strictement croissante gardien → défense → milieu → attaque, ailiers de part et d'autre de l'axe). Note : même la ligne d'attaque d'une formation de coup d'envoi ne tombe jamais dans le tiers OFFENSIF une fois convertie -- `pitch_layout._line_y` arrête volontairement les lignes à 42% de profondeur pour ne pas chevaucher le dispositif adverse à l'écran, fidèle au vrai football (un attaquant démarre vers le milieu de terrain, pas déjà dans la surface adverse).

### `templates.py` (révisé et implémenté le 22/09/2026)

**Responsabilité** : 12 gabarits concrets de mise en scène d'un BUT (la diversité visuelle vient d'ici, pas du hasard -- voir tests/test_templates.py, 49 tests). Chaque gabarit est une fonction autonome `build_xxx(event: GoalEvent, lineup, start_positions) -> Sequence`, toutes construites par un même moteur générique (`build_from_template`) à partir d'un script déclaratif en pseudo-keyframes RELATIFS (position [0,1] à un instant [0,1] de la durée, interpolée entre la position de formation réelle de chaque rôle et un ancrage -- `event.zone`/`event.assist_zone`, déjà calculés par `events.py`). `pick_template(context)` sélectionne un gabarit pondéré par `weight * context_score(TemplateContext)` (minute, écart au score, poste du buteur, poste du passeur comme proxy du "type" de passe décisive).

**Changement de conception important** : ce module construit maintenant directement des `Sequence` (via `build_from_template`), là où l'archi d'origine prévoyait une forme abstraite séparée (`ChoreographyTemplate`/`PhaseKind`) suivie d'un `sequences.build_sequence` distinct pour l'instanciation. Les deux étapes ont fusionné ici -- **`sequences.build_sequence` n'existera donc probablement jamais** : chaque gabarit de `templates.py` EST la fonction de construction.

Les 12 gabarits : `contre_attaque`, `construction_placee`, `debordement_centre_tete`, `percee_individuelle`, `une_deux`, `coup_franc`, `corner`, `profondeur_1v1`, `recuperation_haute`, `decalage_enroulee`, `penalty` (cas spécial : `context_score` retourne 0 hors penalty, donc systématiquement choisi quand `context.penalty=True`), `but_gag` (rare par construction -- le moteur n'a aucune notion de "contre son camp"/déviation, ce gabarit habille un but ordinaire d'un mouvement chaotique, juste pour la variété).

**Bug trouvé par l'audit visuel (22/09/2026, `scripts/preview_templates.py`), corrigé** : `but_gag` avait un `ball_owner` à `None` sur son dernier point (pour représenter une déviation sans porteur clair) -- un owner absent retombe sur la DERNIÈRE position connue du ballon (voir `build_from_template`), donc le ballon n'atteignait jamais `event.zone`, visible immédiatement sur l'image générée. Corrigé (dernier point réattribué au rôle "scorer").

```python
ANCHOR_SCORER, ANCHOR_ASSIST, ANCHOR_STATIC = "scorer_zone", "assist_zone", "static"

@dataclass(frozen=True)
class TemplateContext:
    minute: int
    goal_diff_before: int  # AVANT le but (pas après) -- influence le style de jeu, voir _urgency_factor
    scorer_poste: str
    assist_poste: str | None  # proxy du "type" de passe décisive -- voir docstring
    penalty: bool
    competition_type: str  # "league" | "cup" | "continental"

@dataclass(frozen=True)
class RoleFrame:
    t_ratio: float
    progress: float  # 0.0 = position de départ réelle du rôle, 1.0 = ancrage de fin

@dataclass(frozen=True)
class Role:
    name: str  # "scorer"/"assist" résolus depuis l'event, tout autre nom depuis les coéquipiers restants
    end_anchor: str
    frames: tuple[RoleFrame, ...]  # mêmes t_ratio que les autres rôles actifs du même gabarit (vérifié)

@dataclass(frozen=True)
class Template:
    name: str
    weight: float
    duration: float
    roles: tuple[Role, ...]
    tags: tuple[tuple[float, str], ...]
    ball_owner: tuple[tuple[float, str | None], ...]
    context_score: Callable[[TemplateContext], float]
    ball_height: tuple[tuple[float, float], ...] = ()

TEMPLATES: dict[str, Template]  # 12 entrées
BUILDERS: dict[str, Callable[[GoalEvent, Lineup, dict[PlayerId, PitchPoint]], Sequence]]  # 12 entrées, mêmes clés

def build_from_template(template: Template, event: GoalEvent, lineup: Lineup, start_positions: dict[PlayerId, PitchPoint]) -> Sequence: ...
def pick_template(context: TemplateContext, *, rng: random.Random | None = None) -> str: ...
```

### `animation/types.py` (renommé de `sequences.py` le 22/09/2026, implémenté)

**Responsabilité** : porte l'objet PIVOT (`Sequence`) entre le moteur et le rendu (voir "Changement du 22/09/2026" plus haut) — implémenté et testé (`tests/test_types.py`, 16 tests), volontairement indépendant du reste du pipeline (aucun import de `spatial.py`/`templates.py`/`events.py`). **Remplace** l'ancien design `Phase`/`PhaseStep` (points de passage discrets) : `Sequence` contient directement des `Keyframe` déjà continus.

Renommé `sequences.py` -> `types.py` à la demande d'Olivier : le fichier ne CONSTRUIT aucune séquence (c'est `templates.py`/`sequence_generator.py` qui le font), il ne fait que définir la FORME du contrat -- son ancien nom laissait penser le contraire. Un seul module porte ces dataclasses dans tout le projet.

```python
PlayerId = int | str  # Player.id si connu, sinon son nom (même repli que events._player_seed_id)

@dataclass(frozen=True)
class BallState:
    x: float
    y: float
    z: float  # hauteur au-dessus du sol
    spin: float  # intensité relative, unité pas encore fixée
    owner_id: PlayerId | None  # None si en l'air/disputé

@dataclass(frozen=True)
class Keyframe:
    t: float  # secondes depuis le début de la Sequence
    ball: BallState
    players: dict[PlayerId, tuple[float, float]]  # position (x, y) normalisée de chaque joueur suivi
    tag: str  # étiquette libre (debug/UI), jamais interprétée par le rendu

@dataclass(frozen=True)
class Sequence:
    event_ref: str  # référence stable vers l'événement source (ligue1sim.events), pas l'objet lui-même
    keyframes: list[Keyframe]
    duration: float
    meta: dict[str, Any]

    def to_json(self) -> dict[str, Any]: ...  # implémenté -- voir docstring de la méthode pour la structure exacte
```

**Invariants vérifiés À LA CONSTRUCTION** (`__post_init__`, pas seulement documentés) : `keyframes` trié par `t` croissant ou constant (jamais décroissant) ; tous les `Keyframe.players` d'une même `Sequence` suivent EXACTEMENT le même ensemble de joueurs (pas de disparition/apparition non expliquée sur une séquence de quelques secondes). Une `Sequence` mal formée ne peut donc pas exister.

### `animation/sequence_generator.py` (créé le 22/09/2026, `MatchState` ajouté le 23/09/2026)

**Responsabilité** : assemble la `Sequence` complète d'un but déjà décidé par le moteur -- étape 2.3 de la feuille de route. Choisit un gabarit et l'exécute, en calant le résultat sur ce que le moteur a déjà décidé et en ajoutant la minute réelle aux métadonnées. Implémenté et testé (`tests/test_sequence_generator.py`, 8 tests).

```python
@dataclass(frozen=True)
class MatchState:
    goal_diff_before: int
    minute: int
    competition_type: str

def deterministic_rng(match_id: str, event_index: int) -> random.Random: ...

def generate_sequence(
    event: GoalEvent,
    lineup: Lineup,
    pitch_layout_state: PitchLayoutState,
    match_state: MatchState,
    rng: random.Random,
    *,
    match_id: str = "",
    event_index: int = 0,
) -> Sequence: ...
```

Déroulé : `spatial.placed_player_to_normalized` sur chaque `PlacedPlayer` de `pitch_layout_state` (jointure par nom avec `lineup.players` pour retrouver le `PlayerId`, `PlacedPlayer` ne portant qu'un nom) -> `templates.TemplateContext` (poste du buteur/passeur résolus depuis `lineup`, `goal_diff_before`/`competition_type` depuis `match_state`) -> `templates.pick_template(context, rng=rng)` -> `templates.BUILDERS[nom](event, lineup, start_positions)` -> `Sequence.meta` complété avec `minute`/`match_id`/`event_index`.

**Résolu le 23/09/2026** : `goal_diff_before` est maintenant un vrai paramètre (`match_state.goal_diff_before`), plus une constante à 0 -- voir "Corrections du 23/09/2026" en tête de document. Reste ouvert : QUI calcule `MatchState` (score courant, type de compétition) avant d'appeler `generate_sequence` -- pas encore `build_animation`, voir plus bas.

### `render/component.py`

**Responsabilité** : le point d'entrée Streamlit, appelé depuis `app.py` (écran de détail de match). Embarque `sequence.to_json()` dans un composant HTML/JS/canvas.

```python
def render_sequence(sequence: Sequence, *, height: int = 420) -> None: ...
```

Le template HTML/JS/canvas lui-même (boucle `requestAnimationFrame`, interpolation des keyframes avec easing) est un chantier séparé, pas couvert par ce document ni par le squelette de fichiers — il viendra avec la première implémentation réelle de `component.py`.

### `animation/__init__.py` — orchestrateur

**Responsabilité** : le point d'entrée unique du pipeline complet, appelé depuis `app.py`. Toujours un stub -- `sequence_generator.py` fait maintenant le gros du travail, il ne reste plus qu'à brancher `app.py` dessus.

```python
def build_animation(
    event: GoalEvent,
    match_events: MatchEvents,
    *,
    match_label: str,
) -> Sequence: ...
```

Reste à écrire : construire un `spatial.PitchLayoutState` pour l'équipe du buteur (via `pitch_layout.place_starting_xi` sur `match_events`) ET un `sequence_generator.MatchState` (score courant, type de compétition), puis appeler `sequence_generator.generate_sequence(event, lineup, state, match_state, rng)`. `build_animation` a accès à `match_events` et pourrait calculer `goal_diff_before` lui-même à partir des buts déjà marqués, pas encore fait.

---

## Hors scope de ce document (décisions à venir, pas maintenant)

- Les courbes d'easing précises côté rendu et les vitesses de déplacement perçues (`templates.py` fixe des durées/progressions plausibles mais approximatives, pas calibrées).
- Le template HTML/JS/canvas concret (`render/component.py`) et sa boucle de rendu.
- Comment `app.py` déclenche l'affichage (bouton "revivre ce moment", liste des événements clés d'un match, etc.).
- Persistance/cache d'une `Sequence` déjà générée (regénérer à chaque rerun Streamlit serait un gâchis, mais c'est un problème de performance à traiter une fois le pipeline fonctionnel, pas avant).
- Gabarits pour les événements hors but (carton, remplacement, blessure) -- `templates.py` ne couvre que `GoalEvent`.
- Calcul réel de `MatchState` (score courant, type de compétition) côté `build_animation` -- `sequence_generator.generate_sequence` sait déjà s'en servir (résolu le 23/09/2026).
- Re-vérifier la distinction visuelle des 12 gabarits avec de VRAIES positions de formation (`spatial.placed_player_to_normalized`) plutôt que le placement synthétique arbitraire utilisé par `scripts/preview_templates.py` -- l'audit du 22/09 a montré plusieurs gabarits à 2 rôles qui se ressemblent, à confirmer ou infirmer avec de vraies données.

## Prochaine étape

Posés, implémentés et testés : le référentiel spatial (`ligue1sim.pitch_geometry`), la zone de chaque événement du moteur (`ligue1sim.events`), l'objet pivot `Sequence`/`Keyframe`/`BallState` (`animation.types`), la conversion de référentiel (`animation.spatial`), les 12 gabarits de but -- tous enrichis à ≥3 keyframes, les 4 plus pauvres à ≥3 rôles (`animation.templates`, audités visuellement via `scripts/preview_templates.py` en scène complète à 22 joueurs), et le choix de gabarit pondéré par un vrai contexte de score + calage sur le résultat (`animation.sequence_generator`). Reste, avant que `build_animation` puisse fonctionner : construire un `PitchLayoutState` ET un `MatchState` à partir de `match_events` (score courant, type de compétition). **Question de la phase 3 tranchée le 23/09/2026** (voir "Corrections" en tête de document) : les gabarits ne produisent QUE des keyframes discrets, aucune interpolation -- `motion.py` reste supprimé à juste titre, passage en phase 3 validé.

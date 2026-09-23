# Schéma de la timeline narrative

Brief "narrative engine foundations" (23/09/2026), Tâche 1 -- document seul,
aucun code. Spécifie la structure produite par `engine/narrative.build_timeline`
(voir `engine/narrative.py` pour l'implémentation, ce document est la
référence structurelle, pas un mode d'emploi de l'API Python).

## Objet racine (`Timeline`)

| Champ | Type | Source / calcul |
|---|---|---|
| `match_id` | str | dérivé de `home_team`/`away_team`/`date` (`f"{home}-{away}-{date}"`) |
| `seed` | int | `_derive_seed(match)` -- sha256 sur `(home_team, away_team, date, home_goals, away_goals)` |
| `home_team` / `away_team` | str | `MatchResult.home_team` / `.away_team` (`Match.home`/`.away` du moteur de résultats) |
| `home_goals` / `away_goals` | int | `MatchResult.home_goals` / `.away_goals` -- **invariant absolu, jamais recalculé** |
| `home_rating` / `away_rating` | float | `MatchResult.home_lineup.rating` / `.away_lineup.rating` |
| `competition_type` | str \| None | `MatchResult.competition_type` (voir "Non inclus" -- jamais calculé par le moteur de résultats, fourni par l'appelant ou `None`) |
| `events` | list[NarrativeEvent] | voir ci-dessous, triée strictement par `minute` croissante |

## Par événement (`NarrativeEvent`)

| Champ | Type | Source / calcul |
|---|---|---|
| `minute` | int | réel (`GoalEvent.minute`) si `event_type="but"` ; sinon placé par le générateur (Tâche 4/5) |
| `event_type` | `"but"` \| `"occasion"` | `"but"` ssi l'événement correspond à un but réel de `MatchResult.goals` |
| `gabarit` | str | un des 12 noms de `animation.templates.BUILDERS`, tiré via `animation.templates.pick_template` |
| `declinaison` | str | **`"default"` pour l'instant** -- voir section dédiée ci-dessous |
| `team` | str | `home_team` ou `away_team` -- réel (`GoalEvent.club_name`) pour un but, modulé par les ratings pour une occasion (Tâche 4) |
| `main_player` | str | buteur réel (`GoalEvent.scorer`) pour un but ; joueur de champ tiré dans l'effectif de `team` pour une occasion |
| `involved_players` | tuple[str, ...] | but : `(scorer, assist)` si assist réel, sinon `(scorer,)` ; occasion : `(main_player,)`, `+ 1` joueur si le gabarit a plus d'un rôle (`Template.roles`) -- voir "Mapping vers canvas" pour la portée exacte |
| `outcome` | str | `"but"` si `event_type="but"` ; sinon tiré parmi `arret`/`hors_cadre`/`tacle`/`degagement`/`poteau` (pondéré, voir `engine/narrative.py`) |
| `start_position` | tuple[float, float] \| None | but : `center_of(GoalEvent.zone)` si zone connue, sinon `None` ; occasion : **toujours `None`** (pas de zone réelle, non inventée -- voir "Non inclus") |
| `starts_at_restart` | bool | `Template.starts_at_restart` du gabarit tiré (réutilise la convention existante de `animation.templates.Template`) |

## Invariants structurels

1. **Score final inchangé** : `home_goals`/`away_goals` de la `Timeline` sont EXACTEMENT ceux du `MatchResult` d'entrée, jamais recalculés depuis les événements.
2. **Buts aux minutes existantes** : chaque but réel (`MatchResult.goals`) apparaît dans `events` avec sa `minute`, son `main_player` (buteur) et son `gabarit` réel (penalty reste penalty) EXACTS -- aucun but ajouté, retiré, ou déplacé.
3. **Aucune occasion taguée `but`** qui ne soit pas un but réel préexistant -- `outcome="but"` ssi `event_type="but"`.
4. **Tri chronologique** : `events` est trié par `minute` croissante, tri STABLE (voir "Priorité des contraintes" ci-dessous) -- deux événements à la même minute (deux buts réels y compris) sont départagés par ordre d'apparition, jamais rejetés (brief "constraint priority", 23/09/2026 -- la distinction visuelle de deux buts à la même minute, ex. temps additionnel affiché, est un problème de rendu canvas, voir "Non inclus").
5. **Aucune répétition immédiate de gabarit ni de joueur principal SUR LES `generated_events` UNIQUEMENT** : formulée sur le couple `(gabarit, declinaison)` (pas `gabarit` seul, voir section Déclinaisons) et sur `main_player`, PLUS aucun pattern cyclique de période ≤5 sur la séquence des gabarits des `generated_events` (voir `engine/narrative._has_cyclic_pattern`). Les `existing_events` (buts réels) sont HORS PÉRIMÈTRE de cette règle -- voir "Priorité des contraintes".
6. **Écart minimum entre occasions PLACÉES** (3 minutes, voir `engine/narrative._MIN_MINUTE_GAP`) : s'applique UNIQUEMENT au placement des `generated_events` entre eux, jamais à l'écart entre deux buts réels (immuable, hors du contrôle du générateur).

## Priorité des contraintes

Brief "constraint priority" (23/09/2026) -- décision structurante validée
par le propriétaire, formalisée dans `engine/narrative.py` (voir PRIORITÉ
DES CONTRAINTES en tête de fichier) :

| # | Contrainte | Portée |
|---|---|---|
| 1 | Score final inchangé | Absolue |
| 2 | Buts existants à leur minute/buteur/gabarit exacts | Absolue |
| 3 | Anti-répétition (gabarit+déclinaison, joueur) + écart minimum | `generated_events` UNIQUEMENT |
| 4 | Le réel prime -- une répétition/proximité imposée par le réel est acceptée | `existing_events` HORS PÉRIMÈTRE des règles 3 |

Conséquence directe : `build_timeline` ne rejette plus aucun match (les
exceptions `MinuteCollisionError`/`AntiRepetitionUnsatisfiableError` du
brief précédent sont retirées -- les cas qu'elles signalaient, mesurés sur
3000 matchs de contrôle, sont désormais acceptés tels quels : ~3.6% des
matchs avec deux buts réels à la même minute, ~3.7% avec deux buts
consécutifs du même buteur, ~0.2% avec deux penalties consécutifs).

## Non inclus dans ce brief

- **Commentaire textuel** -- aucune génération de texte, ce module ne produit que la structure.
- **Vitesse de lecture** -- aucun paramètre de rythme de restitution.
- **Caméra** -- aucun paramètre de cadrage/caméra.
- **Branchement canvas** -- `build_timeline` ne construit aucune `Sequence`/`FrameState` (voir "Mapping vers canvas" pour ce qui EST déjà compatible).
- **Variation paramétrique des gabarits** -- `declinaison` existe comme champ mais vaut toujours `"default"` (brief séparé, voir section dédiée).
- **Date de match réelle** -- absente du moteur de résultats (voir `engine/narrative.py`, DETTE en tête de fichier) ; `date`/`competition_type` sont optionnels, fournis par l'appelant ou `None`.
- **Position de départ des occasions inventées** -- `start_position=None` systématiquement (pas de zone réelle à cette étape, voir tableau ci-dessus).
- **Résolution complète des rôles d'un gabarit** -- `involved_players` ne résout PAS chaque rôle (`support1`, `support2`...) vers un joueur précis comme le ferait `animation.templates.build_from_template` ; seul un second joueur générique est tiré si le gabarit a plus d'un rôle (voir "Mapping vers canvas").
- **La distinction visuelle de deux buts à la même minute** (temps additionnel affiché) est un problème de rendu canvas, à traiter dans un brief futur.

## Mapping vers canvas

Un `NarrativeEvent` porte tout ce dont `animation.templates.build_from_template`
a besoin pour produire une `Sequence` (voir `docs/canvas_json_schema.md`) --
**sauf** la résolution complète des rôles secondaires, différée à un brief
futur ("branchement du narratif au canvas") :

1. `gabarit` → `animation.templates.BUILDERS[gabarit]`, le constructeur exact.
2. `main_player`/`involved_players` → rôles `"scorer"`/`"assist"` de
   `build_from_template` (résolus depuis `GoalEvent.scorer`/`.assist` pour un
   but réel) ; les rôles génériques restants (`support1`, `support2`...) sont
   aujourd'hui comblés par `_resolve_roles` (déjà le comportement de
   `build_from_template`, pas de champ manquant côté `NarrativeEvent` -- ce
   module ne fait que fournir le `GoalEvent`/l'événement équivalent, pas les
   noms précis des rôles génériques, exactement comme `sequence_generator.generate_sequence`
   le fait déjà aujourd'hui pour un vrai but).
3. `team` → détermine quelle `Lineup` (`home_lineup`/`away_lineup` de
   `MatchResult`) sert de `lineup` à `build_from_template`.
4. `start_position` (`but` uniquement) → déjà un `event.zone`-compatible
   (`center_of` appliqué), correspond à `GoalEvent.zone`.
5. `starts_at_restart` → déjà lu depuis `Template.starts_at_restart`, aucune
   conversion nécessaire.
6. `outcome`/`event_type` → n'affectent PAS la construction de la `Sequence`
   elle-même (`build_from_template` ne distingue pas but/occasion aujourd'hui) ;
   utiles pour la narration textuelle (hors scope) et pour décider, à terme,
   si le tir doit "rentrer" ou non dans un gabarit qui le permet.

**Champ manquant pour un branchement complet** : pour une `occasion` (pas un
but réel), `build_from_template` a besoin d'un `GoalEvent`-compatible complet
(avec `zone`/`assist_zone` réels) pour positionner les joueurs -- ce module
ne les fournit pas (`start_position=None` pour les occasions, voir "Non
inclus"). Le brief "branchement canvas" devra soit inventer une zone
plausible selon le `gabarit`, soit étendre `NarrativeEvent`.

## Champ `declinaison`

Identifiant opaque (`str`), valeur par défaut `"default"` pour l'instant --
ce champ identifiera à terme les variations paramétriques d'un même gabarit
(tireur, zone, trajectoire, issue). Aujourd'hui, une seule déclinaison par
gabarit -- l'enrichissement viendra dans un brief dédié. La règle
anti-répétition s'applique au couple `(gabarit, déclinaison)`.

## Déclinaisons -- état actuel et cible

Aucune de ces déclinaisons n'est implémentée -- cahier des charges du futur
brief "variation paramétrique des gabarits", une ligne par gabarit :

| Gabarit | Déclinaisons imaginées |
|---|---|
| `contre_attaque` | passe finale courte vs longue en profondeur ; conclusion du relayeur vs du buteur initial ; contre amorcé milieu de terrain vs dans sa propre surface |
| `construction_placee` | circulation courte (une-deux serrés) vs circulation large (changement d'aile) ; tir de loin vs remise dans la surface |
| `debordement_centre_tete` | centre en retrait (cut-back) vs centre au premier poteau vs centre au second poteau ; tête plongeante vs tête en extension |
| `percee_individuelle` | dribble axial vs dribble excentré rentrant sur le pied fort ; conclusion enroulée vs frappe du plat du pied |
| `une_deux` | remise en une touche vs contrôle-remise ; conclusion immédiate vs deuxième contrôle avant le tir |
| `coup_franc` | direct lucarne, direct au-dessus, direct stoppé par le gardien, indirect (mur), contré par le mur puis remis |
| `corner` | corner rentrant vs sortant ; frappe au premier poteau vs corner brossé en retrait vs corner direct (rare mais réel) |
| `profondeur_1v1` | appel dans le dos de la ligne vs appel en soutien puis remise ; conclusion en piqué vs enroulée vs sous le gardien |
| `recuperation_haute` | interception haute vs tacle glissé récupérateur ; relais immédiat vers le but vs conduite de balle du récupérateur lui-même |
| `decalage_enroulee` | décalage côté fort (pied naturel) vs côté faible (enroulé inversé) ; frappe enroulée classique vs frappe du plat contrée déviée |
| `penalty` | frappe placée vs frappe puissante au centre vs "panenka" ; gardien parti du bon côté (arrêté) vs mauvais côté |
| `but_gag` | déviation involontaire d'un défenseur vs rebond sur le gardien vs ricochet à deux contacts successifs |

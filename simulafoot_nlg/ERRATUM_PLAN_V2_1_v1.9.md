# Erratum au PLAN V2.1 v1.9 — étape 0 du Bloc 1 (01/10/2026)

Doc seul : aucun code modifié. Le plan v1.9 vit hors dépôt ; cet erratum ne liste que ce que
la lecture du dépôt a changé (section B) et les corrections déjà identifiées qui ne dépendent
pas du dépôt (section C). Les décisions d'architecture restent à l'architecte (section D).

## A. Constats d'étape 0 (fichier — fait lu)

- `engine/models.py` — `MatchContext` (frozen) a DÉJÀ `passeur`, `receveur`, `is_home`, `gabarit`,
  `scenario_code`, `score_context` et la property `opponent_team` (None si `is_home`/`home_team`/
  `away_team` manque). Il n'a PAS `sortant`, `entrant`, `match_sequence`. `Phrase` n'a ni
  `is_fallback` ni code de variante/scénario.
- `engine/profile_engine.py:61-82` — `normalize_match_context` lit `gabarit`, ne lit NI
  `passeur`/`receveur`, NI `match_sequence`.
- `engine/conditions.py:45,50` — `PLAYER_FIELDS` = 6 champs ; `MATCH_CONTEXT_FIELDS` =
  {minute, score_context, is_home}. `gabarit`, `passeur`, `receveur` (et `sortant`, `entrant`)
  ne sont pas conditionnables. D16 non appliqué : `_resolve` lève `ValueError` sur un attribut FM
  absent ; `contient` sur `None` lève `TypeError` (l.178).
- `scripts/convert_commentary_xlsx_to_yaml.py:84-169` — `SLOTS_AUTORISES` et cooldowns : 9 codes v1.
  `SLOT_EXPRESSIONS` : joueur, club, adversaire (`context.opponent_team`), minute, passeur,
  receveur ; ni `sortant` ni `entrant`.
- `data/seed/scenarios.yml` — 9 codes : CARTON_ROUGE, BUT, PENALTY_RATE, COUP_FRANC, CONSTRUCTION,
  ARRET_GARDIEN, SITUATION_MATCH, DEBUT_MATCH, GESTE_SIGNATURE. `slots.yml` = `{}`.
- `data/simulafoot.db` — 9 scénarios, 13 variantes (DEFAUT ×9 ; SURNOM ×3 sur BUT, ARRET_GARDIEN,
  GESTE_SIGNATURE ; PENALTY ×1 sur BUT, `is_default=0`), 281 phrases, 153 conditions,
  `phrase_history` vide. Tous les poids de variante valent 1.0.
- `data/schema.sql` — 13 tables dont 11 hors `players`/`player_attributes` : la liste de reset D7bis
  (11 tables) est exacte. `phrases` n'a pas de `scenario_id` (jointure via `variants`). `variants`
  a `UNIQUE (scenario_id, code)` : la clé naturelle (code scénario, code variante) existe.
  `phrase_history` n'a pas `match_sequence`. Aucune contrainte d'unicité sur (`variant_id`, `text`).
  SQLite local 3.50.4.
- `scripts/import_seed.py` — charge exactement `scenarios.yml` + `slots.yml` (aucun glob) ; ne valide
  que « ≥ 1 variante par défaut » et `cooldown_matches` ; aucun contrôle d'unicité de texte ;
  ré-import impossible sans reset (`scenarios.code UNIQUE`). README l.24 et l.45 (« `data/seed/*.yml` »)
  sont inexacts.
- `data/import/import_players.py:71,95` — `FM26_ATTRIBUTES` est un `dict[catégorie → tuple de noms]`
  (pas un ensemble plat) ; `ATTRIBUTE_TO_CATEGORY` existe déjà.
- `pilotes_v2/` — 8 modules, 213 phrases (ambiance 24, carton_jaune 28, corner 30, defense 32,
  faute_simple 26, hors_jeu 24, remplacement 21, tir_non_cadre 28). Ensembles de slots mesurés =
  `PILOTES_METADATA` pour les 8. Cooldowns de `PILOTES_METADATA` = ceux de `PLAN_V2_EDITORIAL.md`
  pour les 8. 0 doublon de texte intra-module. Opérateurs : `>=`, `<=`, `==`, `in`, `contient`.
  AMBIANCE n'a pas de SURNOM.
- Racine `engine/narrative.py:268-304,64-80,386-399` — `NarrativeEvent.event_type` ∈ {"but",
  "occasion"} ; `gabarit` ∈ 12 valeurs (contre_attaque, construction_placee,
  debordement_centre_tete, percee_individuelle, une_deux, coup_franc, corner, profondeur_1v1,
  recuperation_haute, decalage_enroulee, penalty, but_gag) ; `outcome` : "but" pour un but ;
  arret/hors_cadre/tacle/degagement/poteau pour une occasion ; arret/poteau/hors_cadre/barre pour un
  penalty raté (occasion de gabarit penalty). `main_player` et `involved_players` sont des NOMS.
  Cartons et remplacements ne sont pas des `NarrativeEvent` : `Timeline.cards`/`.substitutions`
  (`CardEvent.card_type`, `SubstitutionEvent.player_on/off`, noms seuls).
- `pilotes_v2/tir_non_cadre.py` — 4 phrases sur 28 citent un poteau/montant (« frôle », « rase »,
  « longe », « frôle ») ; aucune ne décrit un contact.
- ARRET_GARDIEN v1 — les 38 phrases (30 DEFAUT + 8 SURNOM) sont écrites du point de vue du gardien.

## B. Corrections issues de la lecture

**E1 — Contrat et D12 : la table se lit par (event_type, gabarit, outcome).** Les `event_type`
« corner » et « coup_franc » de la v1.9 n'existent pas côté moteur : ce sont des GABARITS de buts.
Remplacer `CornerDict`/`CoupFrancDict` par des règles sur `gabarit` (`ButDict`/`OccasionDict`). Ajouter
l'outcome `barre`. La règle « `player_id == receveur_id` » est fausse pour CONSTRUCTION (slots
`joueur` + `passeur` + `receveur`, trois personnes) : règles d'acteur/passeur/receveur à re-dériver
de `SLOTS_AUTORISES`, scénario par scénario.

**E2 — Atteignabilité.** PENALTY_RATE (occasion de gabarit `penalty`) et CONSTRUCTION (but de gabarit
`construction_placee`) ont une source : ils ne sont pas inatteignables. Ambiguïté à arbitrer en D12 :
un penalty arrêté est (occasion, penalty, arret) → PENALTY_RATE ou ARRET_GARDIEN ? Sans source dans le
moteur (les occurrences hors NLG sont des scripts d'écriture `add_*.py`) : SITUATION_MATCH, DEBUT_MATCH,
GESTE_SIGNATURE. Le pool PENALTY_RATE mélange textes « arrêt » et « poteau » sans condition
d'outcome (`MatchContext` n'a pas d'`outcome`) : dette éditoriale, non bloquante.

**E3 — Acteur.** ARRET_GARDIEN : acteur = gardien, confirmé par les textes (`{joueur}` = gardien,
`{club}` = club du gardien, `{adversaire}` = club du tireur). Mais `NarrativeEvent.main_player` est le
TIREUR (`team` = équipe attaquante) : ni le gardien ni le défenseur de DEFENSE ne figurent dans
l'événement, la racine doit les tirer de `Timeline.home_lineup/away_lineup`. Le périmètre de
`proprio-conversion` s'élargit. `score_context` d'un arrêt est le score hypothétique du point de
vue du tireur (`models.py:100-113`).

**E4 — « adversaire = club » n'est pas validé.** FAUTE_SIMPLE (≥ 8 phrases : « bouscule
{adversaire} », « retient {adversaire} », « le déséquilibre ») et DEFENSE (≈ 8 : « lui résiste »,
« repousse {adversaire} d'un simple regard ») traitent `{adversaire}` comme une personne ; v1 et le smoke
test (`ADVERSAIRE = "Marseille"`) le traitent comme un club ; `SLOT_EXPRESSIONS` a une seule expression
par nom de slot. FAUTE_SIMPLE est inatteignable en V2.1 : l'impact V2.1 se limite à DEFENSE.

**E5 — Variante BUT/PENALTY : aucune règle d'éligibilité.** 15 phrases sans condition, `is_default=0`,
poids 1.0 (comme SURNOM). La docstring de `select` (étape 2) essaie les variantes non par défaut par
poids décroissant puis `id` croissant : PENALTY (id plus petit que SURNOM) serait essayée avant tout et
fournirait toujours des candidats → tout BUT serait commenté comme un penalty. `gabarit` n'est pas
conditionnable. Les tests α/D1 ne peuvent pas être spécifiés avant cette décision.

**E6 — Unicité (`variant_id`, `text`).** Non vérifiée aujourd'hui ; 0 doublon dans les 281 v1 et les
213 pilotes. À ajouter : contrôle dans `_validate_scenarios` sur (code scénario, code variante, texte)
et `CREATE UNIQUE INDEX IF NOT EXISTS ... ON phrases(variant_id, text)` dans `schema.sql`/`init_db`.

**E7 — Import et emplacement de `fallback`.** Aucun glob n'existe : le défaut de `import-seed` est fait
de chemins fixes, et README l.24/45 décrit un comportement inexistant (à corriger). Le défaut de la liste D4
doit être explicite. Emplacement retenu : dossier dédié `data/seed/fallback/` (comme `v2/`) ; la racine de
`data/seed/` mélange déjà deux schémas (`scenarios.yml` liste, `slots.yml` dict).

**E8 — poteau/barre hors V2.1.** Le pilote ne peut pas commenter un contact : aucun TIR_NON_CADRE
pour les outcomes `poteau` et `barre` en V2.1 (événement non commenté) ; scénario dédié en V2.2.

**E9 — Seuil 70 % déjà tranché** (SPEC §6, décision B2, 01/10/2026) : retiré de la liste architecte.
Restent D9 (mesure à l'exécution) et D9-pop (population).

**E10 — Mineurs.** `fm26.py` doit exposer aussi un `frozenset` aplati (`FM26_ATTRIBUTES_KNOWN`) dérivé de
la structure par catégorie. Le commentaire de `conditions.py:36-40` cite un test inexistant
(`tests/commentary/test_namespaces_attributs.py`) ; le test réel est `tests/test_conditions.py:247-251`.

## C. Corrections indépendantes du dépôt

**C1 — Test SQL D10.** Par scénario (jointure `variants`), pas par variante : « exactement 1 fallback par
scénario » (échoue à 0 et à 2). L'index unique partiel par `variant_id` est une ceinture : avec lui, un
test par variante ne peut jamais échouer. `_validate_scenarios` s'exécute avant toute insertion.

**C2 — `Phrase.is_fallback`** ajouté à `models.py` (Bloc 1) ; `update_cooldown` lève `ValueError` sur un
fallback (test Bloc 4) ; `cli` ne l'appelle pas pour un fallback (test Bloc 5).

**C3 — Ordre complet de `select`** (aligné sur SPEC §6 et la docstring de `phrase_selector`) :
1. variantes actives : non par défaut (poids décroissant, `id` croissant), puis `is_default` ;
2. par variante : (a) conditions `mandatory` (D16 : attribut FM connu mais absent → `False`) ;
   (b) cooldown strict ; récence et similarité pondèrent ; (c) α : palier spécifique, sinon palier
   générique (le « repli cooldown » est ce passage au palier générique ; le cooldown n'est jamais
   relâché) ; (d) tirage pondéré, `rng` dérivé ;
3. variante à 0 candidat → variante suivante, une seule fois chacune (garde-fou) ;
4. toutes épuisées → fallback D10 (si retenu) ;
5. WARNING si `is_default` rend 0 candidat (enrichissement : D10-warn).

**C4 — §7 cohérent** : voir section D (comptes calculés sur les lignes).

**C5 — `UNREACHABLE_SCENARIOS` en deux catégories.** Structurel (aucune source) : FAUTE_SIMPLE,
AMBIANCE, HORS_JEU (D13), SITUATION_MATCH, DEBUT_MATCH, GESTE_SIGNATURE. Différé (source existe, mapping
non fait) : vide tant que D12 n'a pas statué sur CONSTRUCTION et PENALTY_RATE (E2). Chaque entrée porte
une raison et une date de revue. Test : `mappés ∪ structurels ∪ différés == codes importés` et les
trois ensembles sont deux à deux disjoints.

**C6 — Contrat.** `event_type` déclaré par variante (pas dans la base : mypy est configuré,
`pyproject.toml`, et refuse de redéclarer un champ de `TypedDict` plus étroit). `outcome` retiré des
variantes où il répète `event_type` (but, remplacement). `Literal` vérifiés à l'exécution
(`get_type_hints` + `get_args`). Clés inconnues rejetées ; champs requis dérivés de `__required_keys__`.
`gabarit` : membre de `GABARITS` (12, `narrative.py:386-399`), consommé par `narrative_adapter` (D12).
`passeur_id != receveur_id`. `validate_event_stream` (fonction pure de `event_contract.py`, `event_id`
unique par `match_id`) appelée par `cli`.

**C7 — Hors périmètre V2.1, documenté.** Autobuts ; coup franc direct (un seul acteur alors que le
contrat impose passeur et receveur).

**C8 — `reset_seed`** : `--yes` seul (clause « export récent » supprimée) ; message recommandant
l'export DuckDB (D8rév).

## D. État des décisions (§7 révisé)

*Les 9 décisions « à trancher » ci-dessous ont été tranchées le 01/10/2026 : voir SPEC_ANTI_REPEAT.md §10,*
*« Décisions de l'architecte sur les 9 points ouverts du plan V2.1 ».*

**À acter (8)** : norm-mc ; bool-int ; match-seq-None ; match-seq-neg ; alpha (seuil 70 % déjà
tranché, E9) ; alpha-D1 (ordre C3) ; rng-par-phrase (clé `sha256(seed|code scénario|code variante|texte)`) ;
poteau-hors-V2.1 (E8).

**À trancher (9)** : D9 ; D9-pop ; D10 ; D10-warn ; D12 (table réécrite, E1/E2) ; sim-window ;
proprio-conversion (élargie, E3) ; adversaire (E4) ; penalty-variant (E5).

D10-support est actée par E7 (dossier `data/seed/fallback/`, lignes de `phrases` à `is_fallback=1`).

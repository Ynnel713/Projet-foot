# Simulafoot NLG -- commentaire de match

> Génère le commentaire d'un match à partir d'une banque de phrases (SQLite),
> d'un flux d'événements (dicts, contrat dans [SPEC_NLG_INGESTION.md](SPEC_NLG_INGESTION.md))
> et des joueurs. **Jamais de texte inventé** : une phrase vient de la banque, ou
> d'une phrase de secours -- voir [État des lieux](#état-des-lieux).

## Vue d'ensemble

| Module | Rôle |
|---|---|
| `engine/models.py` | Dataclasses partagées (`Player`, `MatchContext`, `Scenario`, `Variant`, `Phrase`, `PhraseCondition`, `PhraseSlot`, `SlotExpression`) -- aucun accès base. |
| `engine/db.py` | Connexions SQLite (WAL, FK) et DuckDB + context managers de transaction. Point d'entrée unique vers les deux bases. |
| `engine/profile_engine.py` | Normalise un dict brut (ligne SQL) en `Player`/`MatchContext` typés -- postes secondaires et preferred moves redécoupés, aucune valeur inventée. |
| `engine/scenario_engine.py` | Charge scénario -> variantes -> phrases (+ conditions/slots) depuis SQLite, en lecture seule. |
| `engine/phrase_selector.py` | `select` : cascade de variantes (SURNOM avant DEFAUT), conditions, cooldown en matchs, paliers spécifiques/génériques, rendu, phrase de secours ; retourne `SelectionResult(phrase, rendered_text)`. |
| `engine/selectivity.py` | Sélectivité des phrases (seuil 70 % des joueurs de champ), cache mémoire. |
| `engine/anti_repeat.py` | Pénalités de récence (en matchs, binaire) et de similarité (MinHash), `update_cooldown` (une transaction : historique puis signature). `match_sequence` obligatoire. |
| `engine/minhash.py` | Signature MinHash d'un texte via `hashlib` (indépendante de `PYTHONHASHSEED`). |
| `engine/template_filler.py` | Résout les `{slot}` d'une `Phrase` (expressions à points sans `eval`, dictionnaires, `SlotResolutionError`) ; rng dérivé par phrase. |
| `engine/post_process.py` | Post-traitement du texte rendu : espaces, majuscule, ponctuation finale, élision -- quatre fonctions pures enchaînées par `apply`. |
| `engine/logger.py` | `log_usage` : écrivain unique de `phrase_history`, retourne l'id inséré ; refuse les phrases de secours. |
| `data/import/import_players.py` | ETL `joueurs.xlsx` -> DuckDB -> SQLite (`players` + `player_attributes`). |
| `scripts/init_db.py` | Crée/met à jour `data/simulafoot.db` depuis `data/schema.sql` (idempotent). |
| `engine/fm26.py` | Source unique des 47 attributs FM26 (`FM26_ATTRIBUTES`, `FM26_ATTRIBUTES_KNOWN`) : lue par l'import des joueurs et par l'évaluateur de conditions. |
| `scripts/import_seed.py` | Charge la banque dans SQLite (sources listées dans [Sources de la banque](#sources-de-la-banque)) ; valide tout avant d'écrire, tout ou rien. |
| `scripts/reset_seed.py` | Vide la banque et l'historique d'usage (11 tables), **garde les joueurs** -- commande `reset-seed --yes`. |
| `scripts/convert_commentary_xlsx_to_yaml.py` | Classeur Excel de commentaire -> `data/seed/scenarios.yml` (banque v1). Porte aussi `PILOTES_METADATA`. |
| `scripts/convert_pilotes_to_yaml.py` | Modules `pilotes_v2/*.py` -> `data/seed/v2/*.yml` (un YAML par pilote). |
| `scripts/export_analytics.py` | Recopie les tables d'usage (scénarios, phrases, historique) vers `analytics.duckdb` pour analyse SQL libre. |
| `engine/event_contract.py` | Contrat des dicts d'événements (TypedDicts par famille) et leur validation (`validate_event`, `validate_event_stream`). |
| `engine/narrative_adapter.py` | `event_to_scenario` : (event_type, gabarit, outcome) → code de scénario ; scénarios non atteints déclarés avec raison. |
| `engine/event_adapters.py` | Cartons et remplacements du moteur → dicts du contrat (aucune décision de scénario). |
| `engine/player_resolver.py` | `resolve(player_id, conn)` → `Player` avec ses attributs FM26. |
| `engine/context_builder.py` | `dict_to_context` : dict d'événement → `MatchContext` (protagonistes résolus en base). |
| `cli.py` | Point d'entrée en ligne de commande (voir ci-dessous). |

## État des lieux

V2.1 est **livrée** : import de la banque (v1 + 8 pilotes + phrases de secours), sélection (`select`),
rendu des slots, post-traitement, journal d'usage, anti-répétition et intégration d'un flux d'événements
(`cli.py narrate`). Seule la **conversion racine → dicts** (le moteur de simulation nomme ses joueurs ; le NLG
attend des identifiants) reste à faire côté racine : voir [SPEC_NLG_INGESTION.md](SPEC_NLG_INGESTION.md), qui
documente aussi les limites connues (poteau / barre non commentés, `(but, corner) → CORNER`, 3 pilotes sans
source d'événement).

## Initialisation (< 10 min)

```bash
cd simulafoot_nlg
uv sync --extra dev                                    # crée .venv/, installe les dépendances
uv run python cli.py init-db                            # crée data/simulafoot.db
uv run python cli.py import-players --xlsx ../data/joueurs.xlsx   # importe les joueurs
uv run python cli.py import-seed                        # importe la banque (v1 + pilotes V2 + fallbacks, voir ci-dessous)
```

`--xlsx` accepte n'importe quel chemin vers un classeur au même format
(feuille "Infos principales", colonne A = ID) -- `../data/joueurs.xlsx`
pointe par défaut vers le fichier déjà utilisé par le reste de l'application
Simulafoot, pas de copie dupliquée.

## Format YAML d'un scénario et de `slots.yml`

Voir les commentaires en tête de chaque fichier pour l'exemple complet.
Résumé :

```yaml
# scenarios.yml
- code: BUT_PIED_DROIT              # identifiant stable, unique
  label: "But du pied droit"
  variants:
    - code: DEFAUT
      label: "Variante par défaut"
      is_default: true              # OBLIGATOIRE : >= 1 par scénario
      phrases:
        - text: "{joueur} ne s'est pas posé de question, {exclamation} !"
          cooldown_matches: 3        # OBLIGATOIRE : import refusé sans
          conditions:
            - attribute: Determination
              operator: ">="
              value: "70"
              mandatory: true        # phrase ÉCARTÉE si la condition échoue
          slots:
            - slot_name: joueur
              expression: "player.full_name"      # valeur calculée dynamiquement
            - slot_name: exclamation
              dictionary_key: exclamations_but     # pioche dans slots.yml
```

```yaml
# slots.yml
exclamations_but:
  - value: "quelle frappe !"
    weight: 1.0
  - value: "magnifique !"
    weight: 0.5
```

`scripts/import_seed.py` **refuse tout l'import** (aucune écriture, pas
d'import partiel) si :

- un scénario n'a pas de variante `is_default: true` ;
- une phrase n'a pas de `cooldown_matches` ;
- une condition vise un nom inconnu (faute de frappe : « Aggresion » ->
  « Aggression » est suggéré) -- sont valides les champs `Player`, les champs
  de `MatchContext`, les attributs FM26 et `preferred_moves` ;
- une variante contient deux fois le même texte (un index `UNIQUE` en est la
  ceinture) ;
- un même code de scénario figure dans deux fichiers.

Un `dictionary_key` référencé par un slot mais absent de `slots.yml` est
seulement loggué en avertissement (le dictionnaire peut être complété plus
tard).

Les slots que le **convertisseur** accepte pour chaque scénario sont dans
`SLOTS_AUTORISES` (`joueur`, `club`, `adversaire`, `minute`, `passeur`,
`receveur`, `sortant`, `entrant` ; `{player_name}` est refusé). `import_seed` ne
vérifie pas les noms de slots : c'est le convertisseur qui le fait.

## Sources de la banque

Il n'y a **pas de glob unique** sur `data/seed/` : `slots.yml` (un dictionnaire)
y cohabite avec `scenarios.yml` (une liste). Chaque source a son origine, et
`import_seed` les lit explicitement :

| Source | Origine | Régénérer |
|---|---|---|
| `data/seed/scenarios.yml` | **Générée** depuis le classeur `data/seed_source/banque_de_phrases_simulafoot.xlsx` (banque v1, 9 scénarios, 281 phrases). Le classeur est la source : ne pas éditer le YAML. | `python cli.py convert-commentary --xlsx data/seed_source/banque_de_phrases_simulafoot.xlsx` |
| `data/seed/v2/*.yml` | **Générés** depuis les modules `pilotes_v2/*.py` (8 pilotes, 213 phrases, un YAML par pilote). Les modules sont la source. | `python scripts/convert_pilotes_to_yaml.py` |
| `data/seed/fallback/*.yml` | **Écrits à la main** (aucun script ne les génère ni ne les efface) : une phrase de secours par scénario. | -- |
| `data/seed/slots.yml` | Écrit à la main (dictionnaires de slots). | -- |

Sans argument, `import_seed` (donc `cli.py import-seed`) charge
`scenarios.yml`, puis `v2/*.yml`, puis `fallback/*.yml`. Avec des fichiers de
scénarios **explicites** (`import_seed(db, [a.yml, b.yml])`), il ne lit aucun
fallback à moins de les passer (`fallback_path=`) : les défauts vont ensemble.

Un test échoue si `data/seed/v2/` n'est plus à jour avec les modules : après
toute modification d'un `pilotes_v2/*.py`, relancer
`python scripts/convert_pilotes_to_yaml.py` et commiter les YAML.

### `PILOTES_METADATA`

Un module `pilotes_v2/<code en minuscules>.py` expose `DEFAUT` (et parfois
`SURNOM`), des listes de `(texte, conditions)`. Ce que le module ne dit pas --
**libellé du scénario, cooldown (en matchs) et slots autorisés** -- est dans
`PILOTES_METADATA` (`scripts/convert_commentary_xlsx_to_yaml.py`), source unique
dont `SLOTS_AUTORISES` et `DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO` sont dérivés.
Ajouter un pilote = un module + une entrée ; des tests exigent la bijection
module <-> code et l'égalité stricte entre slots utilisés et slots déclarés.

### Phrases de secours (`fallback/`)

Une par scénario, rattachée à sa variante par défaut (`phrases.is_fallback = 1`).
Format : une liste de `{scenario, text}`. Elles sortent quand un scénario est à
sec ; elles n'ont **aucun slot**, aucune condition, ne sont **jamais soumises au
cooldown** ni inscrites dans `phrase_history`, et sont exclues du tirage normal.
Dès qu'un fichier de fallback est chargé, chaque scénario importé doit en avoir
exactement un (sinon l'import est refusé) ; sans fichier, l'import reste possible
avec un avertissement.

### Réimporter une banque modifiée

`import_seed` refuse un code de scénario déjà présent : pour réimporter, vider
d'abord la banque. **`reset-seed` vide aussi l'historique d'usage**
(`phrase_history`, `similarity_signatures`) : l'exporter avant si on veut le
garder.

```bash
python cli.py export-analytics     # facultatif : conserve l'historique d'usage dans DuckDB
python cli.py reset-seed --yes     # vide les 11 tables de la banque, GARDE players/player_attributes
python cli.py import-seed
```

`--yes` est obligatoire : sans lui, rien n'est supprimé.

## Règles d'usage

- **Ne jamais inventer de donnée.** Aucune valeur de joueur, aucune phrase,
  aucun scénario en dur dans le code -- tout vient de la base ou des YAML.
- **Toujours une variante par défaut** par scénario (voir ci-dessus).
- **Cooldown obligatoire** : `phrase_selector.select` refuse toute phrase sans
  ligne dans `phrase_cooldowns` (avec un WARNING) -- à l'exception des phrases
  de secours (`is_fallback`), qui n'en ont jamais.
- **Pas de code mort** : toute fonction publique a un test, y compris les
  squelettes (le test y vérifie le contrat `NotImplementedError`, en
  attendant l'implémentation réelle).

## Commandes CLI

```bash
python cli.py init-db
python cli.py import-players --xlsx data/joueurs.xlsx
python cli.py import-seed
python cli.py reset-seed --yes                                  # vide banque + historique, garde les joueurs
python cli.py select --scenario BUT --player-id 1 --match-sequence 1 [--seed 0]   # affiche la phrase rendue
python cli.py narrate --events evenements.jsonl [--dry-run]     # raconte un flux d'événements (JSON Lines ou -)
python cli.py export-analytics
```

## Checklist de validation

```bash
cd simulafoot_nlg
uv sync --extra dev
uv run python cli.py init-db
uv run python cli.py import-players --xlsx ../data/joueurs.xlsx
uv run pytest
uv run mypy --strict
uv run ruff check .
```

Attendu :
- `init-db` crée `data/simulafoot.db` sans erreur.
- `import-players` importe tous les joueurs du classeur (7563 au 28/09/2026,
  log du nombre exact + colonnes ignorées).
- `pytest` : 100 % des tests passent, couverture `engine/` > 85 % (99 % au
  28/09/2026).
- `mypy --strict` et `ruff check .` : aucune erreur.
- `python cli.py select --scenario X --player-id 1 --match-sequence 1` affiche
  une phrase rendue, ou échoue explicitement (scénario introuvable, ou à sec
  sans phrase de secours) -- jamais de texte inventé.

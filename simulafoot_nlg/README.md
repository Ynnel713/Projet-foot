# Simulafoot NLG -- squelette technique

> Ce module ne génère **aucune phrase**. Il prépare le terrain (base de
> données, modèles, ETL, points d'extension) pour la banque de phrases à
> venir. Tout module qui devra un jour "écrire du texte" lève actuellement
> `NotImplementedError` avec un message explicite -- voir la section
> [État des lieux](#état-des-lieux).

## Vue d'ensemble

| Module | Rôle |
|---|---|
| `engine/models.py` | Dataclasses partagées (`Player`, `MatchContext`, `Scenario`, `Variant`, `Phrase`, `PhraseCondition`, `PhraseSlot`, `SlotExpression`) -- aucun accès base. |
| `engine/db.py` | Connexions SQLite (WAL, FK) et DuckDB + context managers de transaction. Point d'entrée unique vers les deux bases. |
| `engine/profile_engine.py` | Normalise un dict brut (ligne SQL) en `Player`/`MatchContext` typés -- postes secondaires et preferred moves redécoupés, aucune valeur inventée. |
| `engine/scenario_engine.py` | Charge scénario -> variantes -> phrases (+ conditions/slots) depuis SQLite, en lecture seule. |
| `engine/phrase_selector.py` | **Squelette.** Sélectionnera une `Phrase` pour un (scénario, joueur, contexte) donnés. |
| `engine/anti_repeat.py` | **Squelette.** Pénalités de récence/similarité, mise à jour du cooldown. |
| `engine/template_filler.py` | **Squelette.** Résout les `{slot_name}` d'une `Phrase`. |
| `engine/post_process.py` | **Squelette.** Élision, majuscule, ponctuation, espaces. |
| `engine/logger.py` | **Squelette.** Journalise un usage de phrase (`phrase_history`). |
| `data/import/import_players.py` | ETL `joueurs.xlsx` -> DuckDB -> SQLite (`players` + `player_attributes`). |
| `scripts/init_db.py` | Crée/met à jour `data/simulafoot.db` depuis `data/schema.sql` (idempotent). |
| `scripts/import_seed.py` | Charge `data/seed/*.yml` dans SQLite, refuse tout scénario sans variante par défaut. |
| `scripts/export_analytics.py` | Recopie les tables d'usage (scénarios, phrases, historique) vers `analytics.duckdb` pour analyse SQL libre. |
| `cli.py` | Point d'entrée en ligne de commande (voir ci-dessous). |

## État des lieux

Ce qui **fonctionne réellement** aujourd'hui : le schéma, l'import des
joueurs, le chargement des scénarios/phrases depuis la base. Ce qui **n'est
pas encore implémenté** (lève `NotImplementedError`) : la sélection d'une
phrase, l'anti-répétition, le remplissage des slots, le post-traitement
linguistique, la journalisation d'usage. Chaque module concerné documente en
tête l'algorithme prévu -- c'est le point de départ de la prochaine session,
une fois la banque de phrases livrée.

## Initialisation (< 10 min)

```bash
cd simulafoot_nlg
uv sync --extra dev                                    # crée .venv/, installe les dépendances
uv run python cli.py init-db                            # crée data/simulafoot.db
uv run python cli.py import-players --xlsx ../data/joueurs.xlsx   # importe les joueurs
uv run python cli.py import-seed                        # importe data/seed/*.yml (vide au départ)
```

`--xlsx` accepte n'importe quel chemin vers un classeur au même format
(feuille "Infos principales", colonne A = ID) -- `../data/joueurs.xlsx`
pointe par défaut vers le fichier déjà utilisé par le reste de l'application
Simulafoot, pas de copie dupliquée.

## Format YAML (`data/seed/scenarios.yml` et `slots.yml`)

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
        - text: "{player_name} ne s'est pas posé de question, {exclamation} !"
          conditions:
            - attribute: Determination
              operator: ">="
              value: "70"
              mandatory: true        # phrase ÉCARTÉE si la condition échoue
          slots:
            - slot_name: player_name
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
d'import partiel) si un seul scénario n'a pas de variante `is_default: true`.
Un `dictionary_key` référencé par un slot mais absent de `slots.yml` est
seulement loggué en avertissement (le dictionnaire peut être complété plus
tard).

## Règles d'usage

- **Ne jamais inventer de donnée.** Aucune valeur de joueur, aucune phrase,
  aucun scénario en dur dans le code -- tout vient de la base ou des YAML.
- **Toujours une variante par défaut** par scénario (voir ci-dessus).
- **Cooldown obligatoire** : `phrase_selector.select` (une fois implémenté)
  devra refuser toute phrase sans ligne dans `phrase_cooldowns`, ou dont
  `cooldown_matches` est `NULL`.
- **Pas de code mort** : toute fonction publique a un test, y compris les
  squelettes (le test y vérifie le contrat `NotImplementedError`, en
  attendant l'implémentation réelle).

## Commandes CLI

```bash
python cli.py init-db
python cli.py import-players --xlsx data/joueurs.xlsx
python cli.py import-seed
python cli.py select --scenario BUT_PIED_DROIT --player-id 1   # échoue explicitement (squelette)
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
- `python cli.py select --scenario X --player-id 1` échoue explicitement
  (scénario introuvable, ou `NotImplementedError` si le scénario existe) --
  jamais de texte généré.

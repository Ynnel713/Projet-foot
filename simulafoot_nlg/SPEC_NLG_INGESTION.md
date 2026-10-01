# SPEC — contrat d'ingestion d'événements du NLG (V2.1)

Ce que la **racine** (le moteur de simulation) doit fournir au NLG pour qu'un match soit raconté, et ce
que le NLG en fait. La conversion racine → dicts est faite côté racine par `engine/nlg_ingestion.py` (B2 : `timeline_to_events`,
`write_jsonl`, un fichier JSON Lines par match ; test bout-en-bout `tests/test_nlg_end_to_end.py`, deux processus). Le NLG reste
testé avec des dicts écrits à la main (`tests/test_cli_narrate.py`). Règle côté racine : un but sans passeur sur un gabarit
corner / coup_franc / construction_placee est émis avec le gabarit `percee_individuelle` (→ scénario BUT).
Garde-fou côté NLG : `tests/test_but_gabarit_neutre.py` (aucune phrase de BUT ne conditionne ce gabarit).
Export d'un match : `scripts/export_match_to_nlg.py` (racine) → `data/nlg_inbox/NNNNNN_<match_id>.jsonl`, puis
`cli.py narrate --events` (§6). **B2 clos (01/10/2026).** Le code fait foi :
[`engine/event_contract.py`](engine/event_contract.py) (formes et validation),
[`engine/narrative_adapter.py`](engine/narrative_adapter.py) (scénario),
[`engine/event_adapters.py`](engine/event_adapters.py) (cartons, remplacements),
[`engine/player_resolver.py`](engine/player_resolver.py), [`engine/context_builder.py`](engine/context_builder.py),
[`cli.py`](cli.py) (`narrate`). Ce document ne le duplique pas : il fixe les **règles** et les **limites**.

## 1. Principes

- **Des identifiants, jamais des noms.** `player_id` = `players.id` de la base NLG = colonne `ID` du classeur
  = `Player.id` de la simulation (D14). Les événements du moteur ne portent que des noms (`CardEvent.player`,
  `SubstitutionEvent.player_on/off`, `NarrativeEvent.main_player`) : la racine les résout en id (par l'effectif
  du club ; homonymes intra-club possibles) **avant** d'appeler le NLG.
- **Le NLG n'importe jamais la racine** (collision du paquet `engine`, D15 ; venv sans `ligue1sim`).
  Tout passe par des dicts.
- **Déterminisme.** Chaque événement a un `event_id` (ordinal dans le match, **stable d'une exécution à
  l'autre**, unique par `match_id`) ; la graine de sa sélection et de son rendu est
  `match_id|match_sequence|event_id`. Aucune horloge. Deux exécutions sur deux bases identiques donnent le même
  texte (`tests/test_cli_narrate.py`).
- **`match_sequence`** : rang du match dans la séquence jouée, fourni par la racine (seule à connaître l'ordre
  des matchs). Unité du cooldown et de la fenêtre de similarité. Un même `match_id` garde le même
  `match_sequence`.

## 2. Familles d'événements (`event_type`)

| `event_type` | Acteur (`player_id`) | Champs propres |
|---|---|---|
| `but` | le buteur | `gabarit` ; `passeur_id`, `receveur_id` (optionnels) |
| `occasion` | `arret` → le **gardien** qui arrête ; `tacle` / `degagement` → le **défenseur** ; `hors_cadre` / `poteau` / `barre` → le **tireur** | `gabarit`, `outcome` ∈ arret, hors_cadre, tacle, degagement, poteau, barre |
| `carton` | le sanctionné | `outcome` ∈ yellow, direct, second_yellow |
| `remplacement` | l'**entrant** (`player_id == entrant_id`) | `sortant_id`, `entrant_id` |

`player_team` est le club **de l'acteur** ; `is_home` doit valoir `player_team == home_team`. `corner`,
`coup_franc`, `construction_placee`, `penalty`… sont des **gabarits** (12, `GABARITS`), pas des `event_type` ;
ils apparaissent sur des buts **et** des occasions.

Champs communs (tous requis ; `competition`, `journee`, `score_context` peuvent valoir `None`) :
`match_id`, `match_sequence`, `event_id`, `minute`, `player_id`, `player_team`, `home_team`, `away_team`,
`is_home`, `competition`, `journee`, `score_context` (∈ `SCORE_CONTEXT_VALUES` ou `None`).

**À la charge de la racine :** choisir le gardien (occasion `arret`) et le défenseur (`tacle`, `degagement`)
dans les compositions : le `NarrativeEvent` ne nomme que le tireur. Pour une occasion `arret`,
`score_context` est le score **hypothétique du point de vue du tireur** (`MatchContext`).

## 3. Validation

`validate_event` rejette : `event_type` inconnu, clés manquantes (dérivées de `__required_keys__`), **clés
inconnues** (une faute de frappe n'est jamais ignorée), types faux (un `bool` n'est pas un `int`),
`outcome`/`gabarit` hors `Literal` (vérifiés à l'exécution), et les incohérences : `is_home` contre
`player_team`, `player_team` hors des deux clubs, `score_context` inconnu, `match_sequence` invalide,
`passeur_id == receveur_id`, remplacement dont `player_id != entrant_id` ou `sortant_id == entrant_id`.
`validate_event_stream` ajoute : `event_id` unique par `match_id`, et un seul `match_sequence` par match.

## 4. Scénario de commentaire (D12) — `event_to_scenario`

Seul décideur du `scenario_code` ; les adaptateurs ne le choisissent jamais. Règles par priorité :

1. `poteau` / `barre` → **aucun scénario** (non commenté en V2.1 ; scénario dédié en V2.2).
2. occasion `arret` → ARRET_GARDIEN (penalty compris).
3. occasion de gabarit `penalty` → PENALTY_RATE.
4. occasion `hors_cadre` → TIR_NON_CADRE ; `tacle` / `degagement` → DEFENSE.
5. **but, quel que soit le gabarit → BUT** (le gabarit `penalty` active la variante PENALTY de BUT). Un but est un but
   (01/10/2026, révise D12) : COUP_FRANC / CONSTRUCTION / CORNER ne contiennent pas de phrase « but » ; ils n'ont plus
   d'événement source (dette V2.2, voir ci-dessous) ;
6. carton `yellow` → CARTON_JAUNE ; `direct` / `second_yellow` → CARTON_ROUGE ; remplacement → REMPLACEMENT.

**Non atteints** (déclarés avec raison, test d'exhaustivité contre les 17 scénarios importés) :
*structurels* — DEBUT_MATCH, SITUATION_MATCH, GESTE_SIGNATURE (contexte ou trait, pas un événement) ;
*différés* (inatteignables en V2.1, pas de source d'événement — D13) — FAUTE_SIMPLE, HORS_JEU, AMBIANCE ;
*dette V2.2* — COUP_FRANC, CONSTRUCTION, CORNER : ajouter des phrases « but » dans ces pools, puis rebasculer (but, gabarit) → scénario du gabarit.

## 5. Limites connues (à arbitrer, pas des bugs cachés)

- **(but, corner / coup_franc / construction_placee) → BUT** : décision du 01/10/2026. Les phrases de ces pools
  décrivent une passe (`{passeur}` → `{receveur}`), pas un but. Dette V2.2 : y ajouter des phrases « but ». Côté racine,
  `receveur_id` reste envoyé (= buteur) pour ces gabarits, et un but sans passeur y est émis en `percee_individuelle` :
  sans effet sur le scénario depuis cette décision.
- **PENALTY_RATE** : son pool mélange arrêts du gardien et poteau, sans condition d'outcome ; seul `hors_cadre`
  lui est envoyé (l'`arret` va à ARRET_GARDIEN).
- **`{adversaire}` = le club adverse.** FAUTE_SIMPLE (inatteignable) et ~8 phrases de DEFENSE le traitent comme
  une personne : réécriture éditoriale, hors V2.1.
- **Hors périmètre :** autobuts ; coup franc direct (un seul acteur alors que le contrat impose passeur et
  receveur) ; blessures (`InjuryEvent`, dette V2.2) ; prénoms à h aspiré (élision, SPEC_ANTI_REPEAT.md §10).

## 6. Utilisation

```bash
python cli.py narrate --events evenements.jsonl [--dry-run]    # JSON Lines, ou `-` pour stdin
```

Une ligne `minute' texte` par événement commenté ; l'usage de chaque phrase est enregistré (cooldown,
similarité) pour que la suite du flux le voie, sauf `--dry-run`. Une phrase de secours n'est jamais
enregistrée. Codes de sortie : `1` événement ou fichier refusé, `2` scénario à sec sans phrase de secours.

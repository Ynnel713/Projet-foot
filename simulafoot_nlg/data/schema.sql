-- Schema SQLite de simulafoot_nlg -- seule source de verite au runtime
-- ("Architecture stateless : tout l'etat vit dans les bases", voir brief).
-- Idempotent : chaque table utilise CREATE TABLE IF NOT EXISTS, executable
-- plusieurs fois sans erreur (voir scripts/init_db.py).
--
-- PRAGMA en tete, comme exige : foreign_keys ON pour que les FK ci-dessous
-- soient reellement appliquees (SQLite les ignore sinon), journal_mode WAL
-- pour des lectures concurrentes pendant qu'un import ecrit.
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;


-- =============================================================================
-- JOUEURS -- import_players.py les peuple depuis data/joueurs.xlsx (Infos
-- principales). Aucune ligne de ces 2 tables n'est jamais ecrite a la main.
-- =============================================================================

-- Un joueur, colonnes "identite" (jamais plus de 1 ligne par joueur). `id`
-- correspond a la colonne ID du classeur Excel (source de verite externe),
-- PAS un autoincrement SQLite -- deux imports successifs du meme classeur
-- doivent mettre a jour les MEMES lignes, pas en creer de nouvelles.
CREATE TABLE IF NOT EXISTS players (
    id                  INTEGER PRIMARY KEY,
    first_name          TEXT NOT NULL,
    last_name           TEXT NOT NULL,
    nationality         TEXT,
    age                 INTEGER,
    position            TEXT,
    secondary_positions TEXT,              -- postes secondaires joints par " / " (ex. "RB / DC") -- lecture via profile_engine, jamais parses en SQL
    club                TEXT,
    league              TEXT,
    market_value        REAL,              -- NULL si non numerique dans le classeur ("-", vide)
    average_rating      REAL,              -- "Note transfermrkt"
    height_cm           INTEGER,
    status              TEXT,
    role_category       TEXT,              -- "Categorie" (ex. CB_Stopper, AM_Playmaker...)
    foot                TEXT,
    fm_rating           REAL,              -- "Moyenne joueur" -- seule note utilisee par le moteur de simulation
    weak_foot           REAL,
    preferred_moves     TEXT,              -- moves joints par " ; " (format source, voir scrape_fminside_attributes.py)
    imported_at         TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Attributs FM26 en EAV (Entity-Attribute-Value) plutot qu'en 47 colonnes :
-- le meme joueur peut n'avoir qu'un sous-ensemble d'attributs importes (voir
-- l'enrichissement progressif de la base, PROJET_SIMULAFOOT.md), une colonne
-- NULL pour chacun des 47 attributs serait la norme plutot que l'exception.
-- L'EAV rend aussi l'ajout d'un 48e attribut futur indolore (aucune migration
-- de schema).
CREATE TABLE IF NOT EXISTS player_attributes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id   INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    attribute   TEXT NOT NULL,             -- nom exact (ex. "Crossing", "Aerial Reach") -- voir FM26_ATTRIBUTES
    category    TEXT NOT NULL,             -- "technique" | "gardien" | "mental" | "physique" | "coups_de_pied_arretes"
    value       INTEGER NOT NULL,          -- 0-100
    UNIQUE (player_id, attribute)
);


-- =============================================================================
-- BANQUE DE PHRASES -- vide au depart (voir data/seed/*.yml), peuplee par
-- scripts/import_seed.py. Structure prete a recevoir la banque, non remplie
-- ici (contrainte "aucun scenario en dur").
-- =============================================================================

CREATE TABLE IF NOT EXISTS scenarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,      -- ex. "BUT_PIED_DROIT" -- identifiant stable utilise par le CLI/l'appelant
    label       TEXT NOT NULL,
    description TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

-- Une Variant DOIT etre is_default=1 par Scenario -- non impose en SQL pur
-- (SQLite n'a pas d'index partiel garantissant "exactement 1 par groupe"
-- de facon portable avant 3.44), donc verifie a l'import par
-- scripts/import_seed.py (erreur explicite si aucune variante par defaut).
CREATE TABLE IF NOT EXISTS variants (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    code        TEXT NOT NULL,
    label       TEXT NOT NULL,
    is_default  INTEGER NOT NULL DEFAULT 0 CHECK (is_default IN (0, 1)),
    weight      REAL NOT NULL DEFAULT 1.0,
    is_active   INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    UNIQUE (scenario_id, code)
);

CREATE TABLE IF NOT EXISTS phrases (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id  INTEGER NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
    text        TEXT NOT NULL,             -- gabarit avec emplacements "{slot_name}"
    weight      REAL NOT NULL DEFAULT 1.0,
    is_active   INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

-- mandatory=1 : phrase_selector doit ECARTER la phrase si la condition
-- echoue (pas seulement la depriorisée) -- voir engine/models.PhraseCondition.
CREATE TABLE IF NOT EXISTS phrase_conditions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    phrase_id  INTEGER NOT NULL REFERENCES phrases(id) ON DELETE CASCADE,
    attribute  TEXT NOT NULL,              -- champ Player ou MatchContext (ex. "Determination", "minute")
    -- Doit lister EXACTEMENT les operateurs reconnus par
    -- engine/conditions.evaluate_condition/parse_condition_atoms (voir
    -- _ATOME_RE et les branches "in"/"contient" de ce module) -- 'contient'
    -- et '=' manquaient ici (bug trouve le 30/09/2026 au premier import
    -- reel des 281 phrases : 56 conditions "contient" de la banque
    -- rejetees par ce CHECK, jamais detecte avant faute d'avoir teste
    -- l'import complet contre le vrai schema).
    operator   TEXT NOT NULL CHECK (operator IN ('==', '=', '!=', '>', '>=', '<', '<=', 'in', 'contient')),
    value      TEXT NOT NULL,
    mandatory  INTEGER NOT NULL DEFAULT 1 CHECK (mandatory IN (0, 1))
);

-- Un emplacement "{slot_name}" dans phrases.text. `dictionary_key` XOR
-- `expression` (l'un pioche dans slot_dictionaries, l'autre calcule une
-- valeur dynamique, ex. "player.full_name") -- non contraint en SQL (les
-- deux formes coexisteront peut-etre), a valider par template_filler.
CREATE TABLE IF NOT EXISTS phrase_slots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    phrase_id       INTEGER NOT NULL REFERENCES phrases(id) ON DELETE CASCADE,
    slot_name       TEXT NOT NULL,
    dictionary_key  TEXT,                  -- cle dans slot_dictionaries.dictionary_key
    expression      TEXT
);

-- Valeurs possibles d'un slot nomme (ex. dictionary_key="exclamation" ->
-- plusieurs lignes "Quelle frappe !", "Magnifique !"...). Independant des
-- phrases : un meme dictionnaire peut etre reference par plusieurs
-- phrase_slots.
CREATE TABLE IF NOT EXISTS slot_dictionaries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    dictionary_key  TEXT NOT NULL,
    value           TEXT NOT NULL,
    weight          REAL NOT NULL DEFAULT 1.0,
    UNIQUE (dictionary_key, value)
);


-- =============================================================================
-- RUNTIME -- anti-repetition, historique, cooldowns. Vide au demarrage,
-- peuple au fil de l'usage reel (pas par l'import de la banque).
-- =============================================================================

-- Chaque phrase reellement generee pour un joueur/match -- source de verite
-- pour anti_repeat.recency_penalty (recence) et similarity_penalty
-- (comparaison au texte final rendu, pas au gabarit).
CREATE TABLE IF NOT EXISTS phrase_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    phrase_id   INTEGER NOT NULL REFERENCES phrases(id) ON DELETE CASCADE,
    player_id   INTEGER REFERENCES players(id) ON DELETE SET NULL,
    match_id    TEXT NOT NULL,
    -- Rang du match dans la sequence jouee (decision B du plan V2.1) : unite du
    -- cooldown (en MATCHS, voir phrase_cooldowns). Nullable pour les lignes
    -- anterieures a la colonne ; scripts/init_db.py l'ajoute par ALTER TABLE
    -- sur une base existante (definition a garder identique a celle-ci).
    match_sequence INTEGER CHECK (match_sequence >= 0),
    rendered_text TEXT NOT NULL,           -- texte final (post template_filler + post_process), pas le gabarit
    used_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Cooldown obligatoire par phrase (contrainte du brief : phrase_selector
-- refuse une phrase si aucune ligne ici, ou si cooldown_matches est NULL).
-- Une ligne par phrase (pas par phrase x joueur) : le cooldown est une
-- propriete de la PHRASE elle-meme (ex. "pas avant 5 matchs"), le calcul du
-- "dernier usage" pour un joueur donne se fait via phrase_history.
CREATE TABLE IF NOT EXISTS phrase_cooldowns (
    phrase_id       INTEGER PRIMARY KEY REFERENCES phrases(id) ON DELETE CASCADE,
    cooldown_matches INTEGER NOT NULL CHECK (cooldown_matches >= 0)
);

-- Signature MinHash (ou equivalent) du texte rendu, pour la detection de
-- similarite au-dela du simple id de phrase (deux phrases DIFFERENTES
-- peuvent produire un texte quasi identique une fois les slots remplis).
-- `signature` stocke une representation serialisee (ex. JSON de la liste de
-- hashes) -- format exact laisse a l'implementation de anti_repeat.
CREATE TABLE IF NOT EXISTS similarity_signatures (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    history_id  INTEGER NOT NULL UNIQUE REFERENCES phrase_history(id) ON DELETE CASCADE,
    signature   TEXT NOT NULL
);


-- =============================================================================
-- TAGS -- classification libre des phrases (ex. "humour", "dramatique"),
-- transverse aux scenarios/variantes.
-- =============================================================================

CREATE TABLE IF NOT EXISTS tags (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS phrase_tags (
    phrase_id   INTEGER NOT NULL REFERENCES phrases(id) ON DELETE CASCADE,
    tag_id      INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (phrase_id, tag_id)
);


-- =============================================================================
-- INDEX -- un par colonne de jointure/filtre frequent (voir engine/*_engine.py)
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_player_attributes_player_id  ON player_attributes(player_id);
CREATE INDEX IF NOT EXISTS idx_player_attributes_attribute   ON player_attributes(attribute);

CREATE INDEX IF NOT EXISTS idx_variants_scenario_id          ON variants(scenario_id);
CREATE INDEX IF NOT EXISTS idx_phrases_variant_id             ON phrases(variant_id);
CREATE INDEX IF NOT EXISTS idx_phrase_conditions_phrase_id    ON phrase_conditions(phrase_id);
CREATE INDEX IF NOT EXISTS idx_phrase_slots_phrase_id         ON phrase_slots(phrase_id);
CREATE INDEX IF NOT EXISTS idx_phrase_slots_slot_name         ON phrase_slots(slot_name);
CREATE INDEX IF NOT EXISTS idx_slot_dictionaries_key          ON slot_dictionaries(dictionary_key);

CREATE INDEX IF NOT EXISTS idx_phrase_history_phrase_id       ON phrase_history(phrase_id);
CREATE INDEX IF NOT EXISTS idx_phrase_history_player_id       ON phrase_history(player_id);
CREATE INDEX IF NOT EXISTS idx_phrase_history_match_id        ON phrase_history(match_id);

CREATE INDEX IF NOT EXISTS idx_phrase_tags_tag_id             ON phrase_tags(tag_id);

"""Modeles de donnees partages par tout le moteur.

Ce module ne fait AUCUN acces base ni fichier : il ne definit que la forme
des objets echanges entre profile_engine, scenario_engine et les squelettes
(phrase_selector, anti_repeat, template_filler, post_process). Chaque champ
optionnel vaut None par defaut -- jamais de valeur inventee pour "boucher un
trou" : c'est aux modules appelants de decider quoi faire d'un champ absent.

Correspondance avec data/schema.sql :
    Player            <- players + player_attributes (EAV)
    MatchContext       <- construit a la volee par l'appelant (pas de table
                           dediee : un contexte de match n'est pas persiste
                           tel quel, seul son usage l'est via phrase_history)
    Scenario           <- scenarios
    Variant             <- variants
    Phrase              <- phrases
    PhraseCondition     <- phrase_conditions
    PhraseSlot          <- phrase_slots
    SlotExpression      <- resultat de resolution d'un PhraseSlot (pas une
                           table : objet de travail interne a template_filler)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Player:
    """Un joueur, normalise depuis players + player_attributes.

    `attributes` : les attributs FM26 disponibles pour ce joueur, cle = nom
    exact de l'attribut (voir data.import.import_players.FM26_ATTRIBUTES),
    valeur = note 0-100. Dictionnaire potentiellement PARTIEL (un joueur peut
    n'avoir que certains attributs importes) -- ne jamais supposer que les 47
    cles sont presentes ; toujours utiliser `.get(...)`.
    """

    id: int
    first_name: str
    last_name: str
    nationality: str | None = None
    age: int | None = None
    position: str | None = None
    secondary_positions: tuple[str, ...] = ()
    club: str | None = None
    league: str | None = None
    market_value: float | None = None
    average_rating: float | None = None  # "Note transfermrkt"
    height_cm: int | None = None
    status: str | None = None
    role_category: str | None = None  # "Catégorie" (ex. CB_Stopper, AM_Playmaker...)
    foot: str | None = None
    fm_rating: float | None = None  # "Moyenne joueur" -- seule note utilisee par le moteur de simulation
    weak_foot: float | None = None
    preferred_moves: tuple[str, ...] = ()
    attributes: dict[str, int] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


#: Valeurs possibles de MatchContext.score_context -- categorise l'EFFET d'un
#: but sur le score (pas son style, voir plutot un futur "type_but" pour
#: tete/pied droit/volee...), pour permettre des conditions de phrase comme
#: "score_context == 'egalisation'" sans que l'auteur de la phrase ait besoin
#: de comparer home_score/away_score lui-meme (le classeur Excel de saisie
#: n'a pas de notion d'arithmetique sur deux colonnes -- voir
#: scripts/make_phrase_template.py). Calcule par l'appelant (le moteur de
#: simulation, qui connait le score AVANT le but), pas par ce module.
SCORE_CONTEXT_VALUES = (
    "ouverture_score",  # premier but du match, 0-0 -> 1-0/0-1
    "egalisation",  # l'equipe qui marque revient a egalite
    "prise_avantage",  # l'equipe qui marque passe devant
    "reduit_ecart",  # l'equipe qui marque reste derriere, mais reduit l'ecart
    "creuse_ecart",  # l'equipe qui marque menait deja, et l'ecart se creuse
)


@dataclass(frozen=True)
class MatchContext:
    """Contexte d'un evenement de match au moment ou une phrase doit etre
    generee (ex. un but vient d'etre marque). Construit par l'appelant (le
    moteur de simulation), jamais lu directement depuis une table -- voir
    profile_engine.normalize_match_context pour la normalisation depuis un
    dict brut (ex. une ligne d'evenement du moteur ligue1sim)."""

    match_id: str
    minute: int | None = None
    home_team: str | None = None
    away_team: str | None = None
    home_score: int | None = None
    away_score: int | None = None
    player_team: str | None = None  # club du joueur concerne par l'evenement
    is_home: bool | None = None  # le joueur joue-t-il a domicile sur ce match ?
    competition: str | None = None
    journee: int | None = None
    scenario_code: str | None = None  # ex. "BUT_PIED_DROIT" -- quel Scenario ce contexte declenche
    # None si l'evenement n'est pas un but ET n'a pas de score_context
    # POTENTIEL calculable (voir SCORE_CONTEXT_VALUES). Deux origines pour ce
    # champ, meme semantique, memes valeurs possibles (decision du
    # 30/09/2026, brief "commentaire live quali") :
    #   - BUT : score REEL apres le but (comportement d'origine, inchange).
    #   - ARRET_GARDIEN : score HYPOTHETIQUE que ce tir aurait produit s'il
    #     n'avait pas ete arrete (ex. l'arret "sauve" une egalisation) --
    #     permet des conditions de phrase comme score_context == "egalisation"
    #     sur un arret, symetriques a celles sur un but. Calcule par
    #     l'appelant (le moteur de simulation, qui connait le score AVANT le
    #     tir dans les deux cas), jamais ici. Pas de champ
    #     score_context_potentiel separe : un seul champ, une seule
    #     semantique ("effet du tir sur le score, reel ou empeche"), pas deux
    #     a tenir synchronises.
    score_context: str | None = None
    # Autre protagoniste d'un evenement a deux joueurs (COUP_FRANC,
    # CONSTRUCTION -- voir data/seed/scenarios.yml une fois la banque
    # importee). None pour tout evenement a un seul joueur (BUT,
    # CARTON_ROUGE, ARRET_GARDIEN...) : ne pas remplir "au cas ou", un champ
    # rempli a tort laisserait croire a template_filler qu'un slot
    # {passeur}/{receveur} est resolvable alors que l'evenement n'en a pas.
    # Decision du 30/09/2026 (brief "commentaire live quali", D1) : deux
    # champs optionnels sur MatchContext existant, pas de hierarchie
    # SinglePlayerEventContext/TwoPlayerEventContext (sur-ingenierie pour 2
    # scenarios sur 9) ni de dict générique `players` (perte de typage, la
    # coherence scenario <-> slots utilises se verifie a l'IMPORT de la
    # banque, voir scripts/convert_commentary_xlsx_to_yaml.py, pas au
    # runtime).
    passeur: Player | None = None
    receveur: Player | None = None
    # Gabarit narratif de l'evenement (ex. "coup_franc", "construction_placee",
    # "une_deux"...) -- copie telle quelle de NarrativeEvent.gabarit
    # (engine/narrative.py, voir _GABARIT_BASE_ZONE pour la liste complete des
    # valeurs possibles), jamais recalcule ici : le moteur de narration a deja
    # tranche le gabarit avant qu'une Phrase ne soit choisie, ce champ permet
    # juste a une condition de phrase de le lire (ex. gabarit == "coup_franc"),
    # meme principe que score_context ci-dessus. None si l'appelant ne l'a pas
    # fourni (ex. contexte construit hors du pipeline narrative.py).
    gabarit: str | None = None
    # Protagonistes d'un REMPLACEMENT (decision D3 du plan V2.1) : le joueur qui
    # sort et celui qui entre, meme principe que passeur/receveur ci-dessus
    # (None pour tout evenement qui n'est pas un remplacement, jamais rempli
    # "au cas ou"). Resolus par l'appelant (par ID, decision D14), jamais ici.
    sortant: Player | None = None
    entrant: Player | None = None
    # Rang du match dans la sequence jouee (decision B du plan V2.1) : unite du
    # cooldown, qui se compte en MATCHS (phrase_cooldowns.cooldown_matches), pas
    # en minutes ni en dates. Fourni par l'appelant (le seul a connaitre
    # l'ordre des matchs), jamais deduit ici. None si non fourni : c'est
    # anti_repeat qui decide quoi en faire.
    match_sequence: int | None = None

    @property
    def opponent_team(self) -> str | None:
        """Club adverse a celui du joueur concerne (voir `player_team`) --
        derive de home_team/away_team/is_home, jamais stocke (un champ
        stocke redondant avec is_home pourrait diverger de lui). Ajoute le
        30/09/2026 pour que le slot {adversaire} du classeur de commentaire
        ait une expression simple et directe ("context.opponent_team") a
        donner a template_filler.render -- celui-ci ne supporte qu'un
        mini-interpreteur d'attributs A POINTS (voir sa docstring), pas de
        logique conditionnelle inline du type "is_home ? away_team :
        home_team" dans une expression de PhraseSlot. None si l'un des
        champs necessaires manque."""
        if self.is_home is None or self.home_team is None or self.away_team is None:
            return None
        return self.away_team if self.is_home else self.home_team


@dataclass(frozen=True)
class Scenario:
    """Une famille de temps forts (ex. "but du pied droit"). Regroupe des
    Variant (voir plus bas) -- une Variant DOIT etre marquee is_default=1
    (contrainte imposee par scripts/import_seed.py)."""

    id: int
    code: str
    label: str
    description: str | None = None
    is_active: bool = True


@dataclass(frozen=True)
class Variant:
    """Une declinaison d'un Scenario (ex. "but du pied droit, joueur en forme"
    vs "but du pied droit, joueur revenant de blessure"). Regroupe des
    Phrase. `is_default` : au moins une Variant par Scenario doit l'etre --
    utilisee en repli quand aucune Variant plus specifique ne correspond au
    contexte."""

    id: int
    scenario_id: int
    code: str
    label: str
    is_default: bool = False
    weight: float = 1.0
    is_active: bool = True


@dataclass(frozen=True)
class Phrase:
    """Un gabarit de phrase (texte avec emplacements `{slot_name}` a
    remplir par template_filler), rattache a une Variant. Peut porter des
    PhraseCondition (filtrage) et des PhraseSlot (emplacements a resoudre)."""

    id: int
    variant_id: int
    text: str
    weight: float = 1.0
    is_active: bool = True
    conditions: tuple[PhraseCondition, ...] = ()
    slots: tuple[PhraseSlot, ...] = ()


@dataclass(frozen=True)
class PhraseCondition:
    """Condition de selection d'une Phrase (ex. attribut "Determination" >=
    70). `mandatory=True` : la Phrase est ECARTEE si la condition echoue (pas
    seulement depriorisee) -- voir phrase_selector.select."""

    id: int
    phrase_id: int
    attribute: str  # nom d'attribut Player (ex. "Determination") ou de MatchContext (ex. "minute")
    operator: str  # "==", "!=", ">", ">=", "<", "<=", "in"
    value: str  # valeur de comparaison, toujours stockee en texte (convertie a l'evaluation)
    mandatory: bool = True


@dataclass(frozen=True)
class PhraseSlot:
    """Un emplacement `{slot_name}` a l'interieur du texte d'une Phrase, a
    resoudre par template_filler.render (voir slot_dictionaries pour les
    valeurs possibles d'un slot nomme)."""

    id: int
    phrase_id: int
    slot_name: str
    dictionary_key: str | None = None  # cle dans slot_dictionaries, si le slot pioche dans un dictionnaire
    expression: str | None = None  # expression dynamique (ex. "player.full_name"), si pas un dictionnaire


@dataclass(frozen=True)
class SlotExpression:
    """Resultat de la resolution d'un PhraseSlot pour un (Player,
    MatchContext) donnes -- objet de travail interne, jamais persiste.
    `resolved_value=None` tant que template_filler.render ne l'a pas encore
    calcule (ou si la resolution a echoue -- voir post_process pour la
    gestion des slots non resolus)."""

    slot_name: str
    source: PhraseSlot
    resolved_value: str | None = None

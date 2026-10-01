"""Pilote AMBIANCE -- EN ATTENTE DE VALIDATION (voir pilotes_v2/STATUT.md).
24 phrases DEFAUT, AUCUN SURNOM (voir ci-dessous). Frequence ~3-5/match.

Registre : moins d'action, plus de contexte -- une phrase decrit un stade, pas
un geste. Pas de nom de joueur, pas de resultat (aucune phrase ne dit qu'un but
vient d'etre marque ni que l'on mene ou perd : `score_context` est hors
perimetre, decision du 01/10/2026).

QUATRE TYPES D'AMBIANCE (TYPES, parallele a DEFAUT, verifie par test) :
    fete (6) -- chants, tifos, drapeaux ;
    tension (6) -- sifflets, nerfs a vif ;
    silence (6) -- stade qui retient son souffle ;
    pression (6) -- public qui pousse ou etouffe.

CONDITIONS -- seules `is_home` et `minute` sont exprimables (D1, 01/10/2026) :
    - `is_home == true` / `== false` : {club} est la maison / l'equipe en deplacement.
      12 phrases NEUTRES n'ont aucune condition et restent vraies a domicile
      comme a l'exterieur (aucune ne dit "stade de {club}") ;
    - `minute` : debut de match (<= 10), troisieme quart (>= 60), dernier quart
      d'heure (>= 75), fin de match (>= 85).

SURNOM : non ecrit. Le scenario n'a pas de joueur ; les conditions fm_rating /
age du brief n'ont pas de porteur (evaluate_condition exige un Player). Les
SURNOM du brief ("gros derby", "petite equipe qui recoit le leader") exigent des
donnees ABSENTES du moteur : rivalite entre clubs, classement. `competition` et
`journee` existent sur MatchContext mais ne sont pas exposes aux conditions
(MATCH_CONTEXT_FIELDS). Aucune phrase ne pretend un derby ou un enjeu : ce
serait faux. A reprendre si ces donnees arrivent (dette, SPEC_ANTI_REPEAT.md).

Slots : {club} (equipe de reference), {adversaire}. 16 phrases sur 24 n'en
utilisent aucun (contexte pur, comme SITUATION_MATCH)."""

_PHRASES = [
    # --- fete ---
    ("fete", "Les chants descendent des tribunes sans interruption, les travées vibrent d'une seule voix !", []),
    ("fete", "Un tifo immense se déploie sur toute la largeur du virage, les couleurs recouvrent tout !", []),
    ("fete", "Les drapeaux s'agitent, les écharpes tournent, ça chante fort dans cette enceinte !", []),
    ("fete", "À domicile, le public de {club} chante à pleins poumons et porte son équipe en avant !",
     [("is_home", "==", "true")]),
    ("fete", "Même en déplacement, les supporters de {club} se font entendre et couvrent presque les locaux !",
     [("is_home", "==", "false")]),
    ("fete", "Dès les premières minutes, les travées sont en fusion : chants, drapeaux et tambours, rien ne manque !",
     [("minute", "<=", "10")]),
    # --- tension ---
    ("tension", "Le ton monte dans les gradins, chaque décision arbitrale réveille la colère de la foule !", []),
    ("tension", "Les nerfs sont à vif des deux côtés, le moindre contact peut tout faire basculer.", []),
    ("tension", "Les sifflets pleuvent sur la pelouse, l'atmosphère devient électrique !", []),
    ("tension", "Dans cette enceinte hostile, chaque ballon touché par {club} est accueilli par un concert de sifflets !",
     [("is_home", "==", "false")]),
    ("tension", "Les travées de {club} retiennent leur souffle à chaque duel, la crispation se lit sur tous les visages.",
     [("is_home", "==", "true")]),
    ("tension", "Dernier quart d'heure : les supporters se lèvent, la tension est à son comble !",
     [("minute", ">=", "75")]),
    # --- silence ---
    ("silence", "Un silence étrange s'installe, on entendrait presque les crampons gratter la pelouse.", []),
    ("silence", "Les tribunes se taisent d'un coup, tous les regards suivent le ballon avec une attention fiévreuse.", []),
    ("silence", "Le bruit retombe un instant, comme si tout le stade retenait son souffle.", []),
    ("silence", "Dans ce temple devenu muet, on distingue clairement les consignes de {club} depuis les bancs.",
     [("is_home", "==", "false")]),
    ("silence", "Dans un recueillement inhabituel, les tribunes de {club} observent le jeu sans un mot.",
     [("is_home", "==", "true")]),
    ("silence", "À ce stade de la partie, un silence respectueux règne autour du terrain.",
     [("minute", ">=", "60")]),
    # --- pression ---
    ("pression", "Porté par des tribunes acquises à sa cause, {club} étouffe {adversaire} sous le bruit !",
     [("is_home", "==", "true")]),
    ("pression", "Dans ce chaudron, {club} doit encaisser une pression de chaque instant venue des gradins !",
     [("is_home", "==", "false")]),
    ("pression", "La pression monte d'un cran, l'enceinte entière semble vouloir faire avancer le ballon !", []),
    ("pression", "Les murs tremblent, la clameur pèse sur chaque passe et chaque contrôle.", []),
    ("pression", "Rarement une atmosphère aura autant pesé sur une rencontre : la foule commente chaque touche de balle !", []),
    ("pression", "Dans les ultimes minutes, la clameur enfle jusqu'à ne plus former qu'un seul cri !",
     [("minute", ">=", "85")]),
]

TYPES = [type_ambiance for type_ambiance, _, _ in _PHRASES]
DEFAUT = [(texte, conditions) for _, texte, conditions in _PHRASES]
SURNOM: list[tuple[str, list[tuple[str, str, str]]]] = []

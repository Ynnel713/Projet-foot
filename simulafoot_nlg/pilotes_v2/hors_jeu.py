"""Pilote HORS-JEU -- EN ATTENTE DE VALIDATION (voir pilotes_v2/STATUT.md).
24 phrases (19 DEFAUT + 5 SURNOM), ~2-4/match. 7e scenario V2, premier de Tier 2
a conditions joueur.

Slots : {joueur} (le joueur signale hors-jeu), {adversaire}, {minute} (1 phrase).
Conditions sur le joueur signale ; aucune sur le passeur (pas de slot passeur).

Axes de conditions (donnees verifiees contre les 7563 joueurs, voir
scripts/audit_conditions_pilote.py) :
    - Position (exposee le 01/10/2026, option A, couverture 100 %) : avant-centre
      (BU, SA), ailier (AG, AD), milieu (MC, MDC, MOC) ;
    - Off the Ball >= 75 (anticipe le dos de la defense), Pace >= 80 (lance trop
      vite), Concentration <= 45 / Anticipation <= 50 (se fait piéger), fm_rating
      >= 75 (joueur surveille) ;
    - minute : <= 20 (entame), >= 80 (prise de risque en fin de match).
`Pace >= 88` du plan (24 joueurs) et `score_context == "reduit_ecart"`
(inexprimable, decision REMPLACEMENT du 01/10/2026) abandonnes. `Vision` du brief
n'est pas utilisee : le joueur signale est celui qui RECOIT, pas celui qui passe.

REGLE DES 70 % appliquee a l'ecriture : aucune condition ne matche plus de 50 % des
joueurs de champ. REGLE alpha (SPEC_ANTI_REPEAT.md, section 6) : 8 phrases DEFAUT
sans condition (42 %) forment le repli ; le sans-condition ne doit pas etre sous-dimensionne.

SURNOM : les 5 portent des archetypes deja utilises ailleurs (renard Finishing>=85 comme
TIR_NON_CADRE ; eclair Pace>=90 ; vetéran age>=34 ; pepite age<=18) + "fantome"
(Off the Ball >= 80). Ceux qui dependent de l'age sont restreints aux postes offensifs
(position) : un gardien de 36 ans ne peut pas etre hors-jeu.
Aucun mot de resultat (pas de "but annule") : on ne sait pas si le hors-jeu annule un
but ; VAR hors perimetre."""

_OFFENSIFS = "BU, SA, AG, AD, MOC, MC"

DEFAUT = [
    ("{joueur} s'élance un instant trop tôt, le drapeau de l'assistant se lève aussitôt !",
     []),
    ("Ligne défensive parfaitement alignée : {joueur} tombe dans le piège !",
     []),
    ("{minute}e minute : {joueur} croit filer au but, mais sa course n'était pas valable.",
     []),
    ("{adversaire} remonte d'un bloc et laisse {joueur} seul, bien trop seul pour que ce soit régulier !",
     []),
    ("Le sifflet retentit : {joueur} était devant le dernier défenseur au départ de la passe.",
     []),
    ("{joueur} contrôle parfaitement et s'en va seul, mais l'arbitre stoppe l'action net !",
     []),
    ("Trop impatient, {joueur} s'est placé d'une pointe de pied au-delà de la limite.",
     []),
    ("Petite erreur de timing : {joueur} arrive au mauvais moment, un souffle devant les défenseurs, et le hors-jeu est sifflé.",
     []),
    ("{joueur} réclame le ballon dans le dos de la défense, mais son appel était parti une seconde trop tôt !",
     [("Off the Ball", ">=", "75")]),
    ("Lancé à pleine vitesse, {joueur} dépasse les défenseurs d'un cheveu et se fait rattraper par le drapeau !",
     [("Pace", ">=", "80")]),
    ("Distrait un instant, {joueur} ne voit pas la défense remonter et ne comprend son erreur qu'au coup de sifflet.",
     [("Concentration", "<=", "45")]),
    ("Mal calé sur la dernière passe, {joueur} est de nouveau pris en position irrégulière.",
     [("Anticipation", "<=", "50")]),
    ("{adversaire} avait bien surveillé {joueur} : toute la défense monte d'un cran pour le piéger !",
     [("fm_rating", ">=", "75")]),
    ("{joueur} joue sur la limite en pointe et finit par la dépasser, le hors-jeu est signalé.",
     [("position", "in", "BU, SA")]),
    ("Sur son couloir, {joueur} part en éclair mais l'assistant lève son drapeau avant le centre !",
     [("position", "in", "AG, AD")]),
    ("Venu de la deuxième ligne, {joueur} perce dans l'axe mais arrive un cheveu trop tôt dans la zone !",
     [("position", "in", "MC, MDC, MOC")]),
    ("Dans la dernière ligne droite, {joueur} prend tous les risques et se fait piéger par le bloc de {adversaire} !",
     [("minute", ">=", "80")]),
    ("Dès l'entame, {joueur} teste la ligne de {adversaire}, et se fait déjà reprendre par l'assistant.",
     [("minute", "<=", "20")]),
    ("Fatigué, {joueur} manque de lucidité et retombe une nouvelle fois dans le piège du hors-jeu.",
     [("Concentration", "<=", "45"), ("minute", ">=", "70")]),
]

SURNOM = [
    ("Le renard flaire l'ouverture avant la passe, et le drapeau se lève !",
     [("Finishing", ">=", "85")]),
    ("L'éclair prend de vitesse un défenseur médusé, mais le drapeau de l'assistant est déjà levé !",
     [("Pace", ">=", "90"), ("position", "in", _OFFENSIFS + ", RB, LB")]),
    ("Le fantôme surgit dans le dos des défenseurs, mais l'assistant l'avait bien repéré !",
     [("Off the Ball", ">=", "80"), ("position", "in", _OFFENSIFS)]),
    ("Le vétéran connaît pourtant tous les pièges, mais il s'est laissé surprendre cette fois !",
     [("age", ">=", "34"), ("position", "in", _OFFENSIFS)]),
    ("La pépite s'emballe, part trop vite et se fait siffler pour avoir trop anticipé !",
     [("age", "<=", "18"), ("position", "in", _OFFENSIFS)]),
]

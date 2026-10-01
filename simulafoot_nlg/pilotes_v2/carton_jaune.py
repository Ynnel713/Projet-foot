"""Pilote CARTON_JAUNE -- EN ATTENTE DE VALIDATION (voir pilotes_v2/STATUT.md).
28 phrases (22 DEFAUT + 6 SURNOM), ~3-4/match. Dernier scenario du Tier 1.

Registre : l'avertissement est un evenement LEGER face au rouge (31 phrases
longues et dramatiques dans CARTON_ROUGE) -- phrases plus courtes, verbes
"ecope / se fait avertir / se voit presenter", jamais "voit rouge", jamais de
suspense de seconde jaune (la gestion du deuxieme jaune releve d'une V3, voir
PLAN_V2_EDITORIAL.md). Aucune phrase ne mentionne un "premier" avertissement.

Slots : {joueur}, {adversaire}, {club}, {minute} (patron de CARTON_ROUGE).

Conditions -- LECON DES SEUILS Finishing appliquee d'emblee : le plan proposait
`Aggression >= 60`, qui matche 57 % des joueurs de champ (dominante). Seuils
gradues ici : Aggression 70 (28 %), 75 (17 %), 85 (3 %), combines a un second
attribut quand le sous-texte s'y prete. Mesure contre la base : voir
scripts/audit_conditions_pilote.py (0 dominante, 0 SURNOM fantome).
`preferred_moves "Argues With Officials"` (propose par le plan) n'est PAS
utilise : 18 joueurs sur 7563 = fantome. "Winds Up Opponents" (29) et
"Dives Into Tackles" (105) le sont avec parcimonie (1 phrase chacun).
height_cm absent. score_context non utilise (decision du 01/10/2026)."""

DEFAUT = [
    ("Un pied en retard, {joueur} fauche son adversaire et récolte un carton.",
     []),
    ("Tacle par derrière : {joueur} frappe la jambe avant le ballon, la sanction tombe sans hésiter !",
     [("Aggression", ">=", "70")]),
    ("Les protestations de {joueur} deviennent trop vives, l'arbitre y met fin d'un avertissement.",
     [("Aggression", ">=", "75")]),
    ("Pour couper une contre-attaque, {joueur} retient son vis-à-vis par la manche : un jaune tactique, sans discussion.",
     [("minute", ">=", "60")]),
    ("À peine {minute} minutes écoulées et {joueur} est déjà averti, un début de partie bien chargé pour {club} !",
     [("minute", "<=", "30")]),
    ("{joueur} gagne du temps en traînant les pieds, mais la manœuvre est vue et l'antijeu sanctionné !",
     [("minute", ">=", "80")]),
    ("Main volontaire de {joueur} pour stopper la trajectoire : c'est flagrant, rien à discuter.",
     []),
    ("{joueur} balance son bras dans un duel aérien : le geste est jugé dangereux, la sanction tombe.",
     []),
    ("Agacé par une décision, {joueur} envoie le ballon au loin, ce qui lui vaut une sanction immédiate !",
     [("Composure", "<=", "45")]),
    ("Emporté par l'intensité du duel, {joueur} repousse un adversaire des deux mains et le carton sort aussitôt.",
     [("Aggression", ">=", "75")]),
    ("{joueur} met un tacle appuyé à un joueur de {adversaire}, difficile de plaider l'innocence.",
     [("Tackling", ">=", "70"), ("Aggression", ">=", "70")]),
    ("Mal inspiré, {joueur} se jette dans les pieds de son vis-à-vis et se fait sanctionner, un carton qui pourrait coûter cher !",
     [("Decisions", "<=", "45")]),
    ("{joueur} accroche un adversaire au milieu du terrain, une faute banale que l'arbitre sanctionne sans se faire prier.",
     []),
    ("Sur un tacle bien trop tardif, {joueur} s'en veut aussitôt et ne protestera pas.",
     [("Anticipation", "<=", "50")]),
    ("Le ton monte autour de l'arbitre, {joueur} s'approche trop près et reçoit un carton jaune en plein visage !",
     [("Aggression", ">=", "70")]),
    ("{joueur} stoppe du pied une relance rapide et se voit sanctionner pour avoir retardé la reprise du jeu.",
     [("minute", ">=", "70")]),
    ("Un geste de trop : {joueur} frappe le ballon une fois le jeu arrêté, carton immédiat !",
     []),
    ("{joueur} se jette en tacle glissé, touche l'adversaire et écope d'un avertissement : {club} devra se méfier jusqu'à la fin !",
     [("preferred_moves", "contient", "Dives Into Tackles")]),
    ("{joueur} réclame un penalty avec trop d'insistance, l'arbitre lui montre le carton jaune pour le calmer !",
     [("Determination", ">=", "80"), ("Aggression", ">=", "65")]),
    ("{joueur} s'écroule dans la surface, mais la comédie ne prend pas : carton pour simulation !",
     [("Flair", ">=", "75")]),
    ("Tacle à retardement de {joueur} : jaune bien mérité, personne ne dira le contraire.",
     []),
    ("{joueur} enchaîne les fautes sur le porteur de {adversaire}, ça ne pouvait pas durer !",
     [("Aggression", ">=", "80")]),
]

SURNOM = [
    ("Le boucher arrive en retard sur son vis-à-vis et reçoit un avertissement que personne ne contestera !",
     [("Aggression", ">=", "85")]),
    ("Le pitbull s'accroche à son adversaire sans jamais le lâcher : le sifflet retentit, le jaune suit.",
     [("Tackling", ">=", "75"), ("Aggression", ">=", "75")]),
    ("Le provocateur cherche encore son vis-à-vis du regard, l'arbitre sort le jaune pour le rappeler à l'ordre !",
     [("preferred_moves", "contient", "Winds Up Opponents")]),
    ("Le sage laisse traîner sa jambe une fois de trop et se retrouve avec un jaune sur les bras, presque surpris.",
     [("age", ">=", "34")]),
    ("Le tribun va réclamer auprès de l'arbitre, qui lui répond d'un carton pour contestation.",
     [("Leadership", ">=", "80")]),
    ("La pépite découvre le haut rythme de la compétition et doit se contenter d'un jaune pour la leçon !",
     [("age", "<=", "18")]),
]

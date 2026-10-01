"""Pilote CORNER -- VALIDE (voir pilotes_v2/STATUT.md). 26 phrases
(20 DEFAUT + 6 SURNOM). Audits passes : n-grammes (2 residus acceptes comme
vocabulaire football naturel -- "tout le monde et", "le gardien de
{adversaire}" --, memes criteres que "dans les pieds de" sur COUP_FRANC),
structurel (1 signal #2/#20 "PASSEUR trouve...corner", verifie : deux
denouements reellement differents, accepte comme variation legitime),
sequence (seed=42, tient -- un residu honnete releve : positions 20-21
enchainent deux phrases a dominance aerienne, mais CORNER est par nature
majoritairement aerien, contrairement a DEFENSE ou ce serait un defaut).

Slots : {passeur}, {receveur}, {adversaire} -- reutilise le patron deja
existant de COUP_FRANC/CONSTRUCTION, aucun nouveau slot introduit.
"court"/"long"/"zone" restent des variations de texte dans les phrases,
pas des slots dedies (decision confirmee avec l'utilisateur avant ecriture).
Beneficie du correctif height_cm (commit c1314a0, 93.4% de couverture) --
conditions height_cm utilisees librement, contrairement a DEFENSE qui les
evitait par precaution avant ce correctif."""

DEFAUT = [
    ("{passeur} enroule son corner directement vers le premier poteau, {receveur} dévie imperceptiblement le cuir, imparable pour {adversaire} !",
     [("Technique", ">=", "75")]),
    ("D'un corner tendu au second poteau, {passeur} trouve {receveur} totalement esseulé face au but vide !",
     [("Technique", ">=", "72")]),
    ("{passeur} joue son corner à ras de terre vers l'avant du but, {receveur} n'a qu'à pousser le ballon au fond !",
     [("Technique", ">=", "70")]),
    ("{passeur} glisse son corner en retrait pour {receveur}, démarqué à l'entrée de la surface avant que la défense ne réagisse !",
     [("Vision", ">=", "78")]),
    ("{receveur} domine le combat aérien et catapulte une tête rageuse que le gardien de {adversaire} ne peut qu'accompagner au fond !",
     [("Heading", ">=", "82")]),
    ("D'un corner excentré, {passeur} trouve la tête de {receveur}, totalement imprenable dans les airs !",
     [("Heading", ">=", "80"), ("height_cm", ">=", "185")]),
    ("{passeur} centre trop fort, le ballon traverse toute la surface sans que personne ne puisse l'intercepter !",
     []),
    ("La défense de {adversaire} repousse le premier corner, mais {receveur} récupère le ballon et reprend aussitôt !",
     [("Technique", ">=", "72")]),
    ("{passeur} brosse son corner en cloche, {receveur} glisse sa tête entre deux défenseurs de {adversaire} !",
     [("Heading", ">=", "78")]),
    ("Sur un corner joué court, {passeur} et {receveur} combinent pour prendre de vitesse le repli de {adversaire} !",
     [("Vision", ">=", "80")]),
    ("{passeur} envoie un corner trop long, le ballon file directement en touche sous les sifflets !",
     []),
    ("{receveur} anticipe le mouvement de {passeur} et s'infiltre entre les lignes pour couper la trajectoire de la tête !",
     [("Vision", ">=", "80")]),
    ("D'un corner parfaitement dosé, {passeur} offre un caviar à {receveur}, seul au point de penalty !",
     [("Technique", ">=", "78")]),
    ("{passeur} sert {receveur} au premier poteau d'un ballon piqué, imparable pour le gardien de {adversaire} !",
     [("Technique", ">=", "75")]),
    ("{adversaire} repousse le ballon de la tête en catastrophe, mais le cuir retombe idéalement dans la surface pour une seconde tentative !",
     []),
    ("{receveur} devance tout le monde et loge une tête surpuissante dans la lucarne, totalement imparable !",
     [("Heading", ">=", "85"), ("height_cm", ">=", "188")]),
    ("{passeur} varie son corner vers le second poteau, {receveur} surgit et reprend acrobatiquement !",
     [("Technique", ">=", "80")]),
    ("Sur un corner mal négocié, {passeur} envoie le ballon directement dans les gants du gardien de {adversaire} !",
     []),
    ("{receveur} gagne son duel aérien face à {adversaire} sur le corner tiré par {passeur} et cadre sa tête sans trembler !",
     [("Heading", ">=", "80"), ("Strength", ">=", "75")]),
    ("{passeur} trouve une ouverture inattendue sur son corner, {receveur} reprend du plat du pied à bout portant !",
     [("Technique", ">=", "76")]),
]

SURNOM = [
    ("Le cadreur brosse une parabole parfaite sur chaque corner, aucun gardien ne peut rien y faire !",
     [("Technique", ">=", "88")]),
    ("Le dominateur s'élève au-dessus de la mêlée sur le corner et impose sa tête sans aucune contestation !",
     [("Heading", ">=", "88"), ("height_cm", ">=", "190")]),
    ("Le lutin se glisse entre deux montagnes dans la surface et place une tête que personne n'a vue venir !",
     [("height_cm", "<=", "172"), ("Heading", ">=", "75")]),
    ("L'horloger ajuste son corner au centimètre près, directement sur le crâne de son partenaire !",
     [("Technique", ">=", "85"), ("Vision", ">=", "80")]),
    ("L'opportuniste sent le ballon repoussé avant tout le monde et reprend instantanément au fond des filets !",
     [("Vision", ">=", "82")]),
    ("Le rempart impose sa carrure sur chaque corner et dégage inlassablement le danger de la tête !",
     [("Strength", ">=", "85"), ("Heading", ">=", "78")]),
]

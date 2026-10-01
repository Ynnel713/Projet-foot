"""Pilote DEFENSE -- VALIDE (voir pilotes_v2/STATUT.md). 28 phrases
(26 DEFAUT + 6 SURNOM depuis le 01/10/2026 : les 4 dernieres DEFAUT sont des phrases
neutres de repli alpha, SPEC_ANTI_REPEAT.md section 6). Audits passes : n-grammes (0 collision apres
corrections), sequence (4 seeds testees : 42/43/44/45 -- H1 "seed
malheureux" confirmee pour la concentration aerienne observee sur seed=42
uniquement, pas un defaut du pool), structurel (0 doublon). Non importe
dans la banque reelle -- scenarios.yml et le classeur xlsx restent
inchanges tant que ce pilote n'est pas formellement bascule en production."""

DEFAUT = [
    ("{joueur} place un tacle parfaitement chronométré et récupère le ballon sans donner le moindre coup franc à {adversaire} !",
     [("Tackling", ">=", "85")]),
    ("D'une interception limpide, {joueur} coupe la trajectoire de la passe et repart aussitôt vers l'avant !",
     [("Vision", ">=", "78")]),
    ("{joueur} sort un tacle glissé désespéré à l'entrée de la surface et repousse le danger in extremis !",
     [("Tackling", ">=", "80"), ("minute", ">=", "75")]),
    ("Revenu à pleine vitesse dans son propre camp, {joueur} efface l'attaquant de {adversaire} d'une course de récupération exemplaire !",
     [("Pace", ">=", "88")]),
    ("{joueur} s'impose dans le duel aérien et dégage le ballon loin de sa surface sans aucune difficulté !",
     [("Heading", ">=", "80"), ("Strength", ">=", "75")]),
    ("D'une charge réglementaire impeccable, {joueur} déséquilibre son adversaire et récupère proprement le ballon !",
     [("Strength", ">=", "80"), ("Aggression", "<=", "50")]),
    ("{joueur} lit parfaitement la trajectoire du centre et coupe le ballon avant qu'il n'atteigne {adversaire} !",
     [("Vision", ">=", "80")]),
    ("Pris à contre-pied, {joueur} rattrape pourtant son retard par un repli défensif monumental et sauve la situation !",
     [("Pace", ">=", "85"), ("minute", ">=", "70")]),
    ("{joueur} referme l'espace dans son dos en un éclair et coupe toute passe en profondeur vers {adversaire} !",
     [("Pace", ">=", "82")]),
    ("D'un tacle à retardement savamment dosé, {joueur} cueille le ballon sans jamais toucher l'adversaire !",
     [("Tackling", ">=", "82"), ("Technique", ">=", "70")]),
    ("{joueur} s'interpose courageusement devant la frappe et dévie le ballon en corner au prix d'un contact rude !",
     [("Strength", ">=", "75")]),
    ("Dans un mouchoir de poche, {joueur} grappille le ballon des pieds de {adversaire} sans commettre la moindre faute !",
     [("Tackling", ">=", "88")]),
    ("{joueur} anticipe la remise et subtilise le ballon avant même que {adversaire} n'ait pu le contrôler !",
     [("Vision", ">=", "78"), ("Pace", ">=", "75")]),
    ("Dos au but et sous pression, {joueur} dégage en catastrophe, propre malgré l'urgence !",
     []),
    ("{joueur} s'arrache au sol pour contrer la frappe à bout portant et sauve son équipe d'un but certain !",
     [("Strength", ">=", "80")]),
    ("{joueur} garde son sang-froid et temporise jusqu'à ce que ses partenaires reviennent couvrir l'espace libre !",
     [("Technique", ">=", "72")]),
    ("D'un retour athlétique phénoménal, {joueur} rejoint l'ailier de {adversaire} et glisse un tacle salvateur par l'arrière !",
     [("Pace", ">=", "86"), ("Tackling", ">=", "75")]),
    ("{joueur} boxe littéralement le ballon d'une tête rageuse, sans se soucier du style !",
     [("Heading", ">=", "82")]),
    ("Esseulé face à deux attaquants de {adversaire}, {joueur} temporise intelligemment avant d'intervenir au bon moment !",
     [("Vision", ">=", "75"), ("Aggression", "<=", "55")]),
    ("{joueur} hausse le ton physiquement et prend le dessus dans chaque duel face aux assauts de {adversaire} !",
     [("Strength", ">=", "85"), ("Aggression", ">=", "60")]),
    ("D'une lecture précoce du jeu, {joueur} coupe la ligne de passe avant que l'idée n'ait germé dans la tête de {adversaire} !",
     [("Vision", ">=", "85")]),
    ("{joueur} se jette corps et âme devant la tentative et stoppe le cuir sur la ligne, au prix d'une égratignure !",
     [("Tackling", ">=", "78"), ("Aggression", ">=", "60")]),
    # --- repli alpha (01/10/2026) : 4 phrases NEUTRES ajoutees pour que 3 joueurs sur 4
    # (74 % sans phrase specifique) disposent d'un pool de 5, pas d'une seule phrase ---
    ("{joueur} met un tacle propre, bien dosé, et le jeu repart de l'autre côté.",
     []),
    ("{joueur} se place juste, intercepte la passe destinée à {adversaire} et relance simplement.",
     []),
    ("{joueur} dégage prudemment en touche face à {adversaire}, sans prendre le moindre risque.",
     []),
    ("{joueur} suit son vis-à-vis de près, l'accompagne vers la ligne de touche et récupère la balle.",
     []),
]

SURNOM = [
    ("Le roc ne cède pas un centimètre et repousse l'assaut de {adversaire} comme si de rien n'était !",
     [("Strength", ">=", "88")]),
    ("Le verrou interdit tout passage à {adversaire}, aucune échappée ne lui résiste !",
     [("Tackling", ">=", "90")]),
    ("Le chasseur fond sur le porteur du ballon et lui vole la possession avant qu'il n'ait pu réagir !",
     [("Pace", ">=", "90"), ("Tackling", ">=", "75")]),
    ("L'ancien couvre l'espace avec une anticipation que l'âge n'a en rien émoussée !",
     [("age", ">=", "33"), ("Vision", ">=", "80")]),
    ("Le pilier domine chaque duel aérien et repousse {adversaire} d'un simple regard !",
     [("Heading", ">=", "88"), ("Strength", ">=", "85")]),
    ("Le métronome défensif dicte le repli de son équipe avec un calme qui force le respect !",
     [("Technique", ">=", "85"), ("Vision", ">=", "82")]),
]

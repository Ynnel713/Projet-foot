"""Pilote TIR_NON_CADRE -- EN ATTENTE DE VALIDATION (voir pilotes_v2/STATUT.md).
28 phrases (22 DEFAUT + 6 SURNOM). Meme format que defense.py / corner.py.

Registre SURNOM (3 bullets, releves sur BUT/GESTE_SIGNATURE/pilotes) :
    - rythme : une seule phrase, exclamation finale, pas de nom propre ;
    - vocabulaire : "Le/L'" + surnom-metaphore + verbe d'action concret ;
    - structure : le surnom est le sujet, la phrase raconte un geste type.
Ici le geste est RATE : surnoms et seuils sont ceux deja utilises dans la
banque reelle (eclair Pace>=90, artiste Technique>=90, canonnier Shoots With
Power) ; renard est a Finishing>=85 ici (>=90 dans BUT ne matche que 8 joueurs) pour que le meme joueur garde le meme surnom
d'un scenario a l'autre.

Slots : {joueur}, {adversaire} (patron deja existant, aucun nouveau slot).
Position de tir (entree de surface / 25 m / angle ferme) et contexte
(frappe instantanee / apres controle) sont des variations de TEXTE, comme
"court/long" sur CORNER -- pas des slots dedies : le moteur ne fournit pas
ces informations aujourd'hui (a confirmer avec l'architecte).

Attributs : Finishing (82 %), Technique, Vision, Pace, Composure,
First Touch, Long Shots (tous 82 %, base FM26), minute. Un seul
SURNOM (canonnier) depend de preferred_moves (4,8 % -> cible 90 %) : il ne
se declenche donc qu'apres enrichissement, sans effet de bord avant.
height_cm volontairement absent (consigne : 4 sentinelles 152/154 encore en
base, voir STATUT.md)."""

DEFAUT = [
    ("{joueur} s'essaie de loin, sa frappe instantanée des vingt-cinq mètres s'envole largement au-dessus de la transversale !",
     []),
    ("À l'entrée de la surface, {joueur} contrôle puis arme trop vite, le ballon part dans les tribunes !",
     [("Finishing", "<=", "60"), ("Composure", "<=", "55")]),
    ("{joueur} se présente dans un angle fermé, force sa frappe et ne récolte qu'un concert de sifflets !",
     []),
    ("Servi dans l'axe, {joueur} frappe du premier ballon mais croise trop son tir, qui file à côté du second poteau !",
     [("Finishing", "<=", "65"), ("Technique", "<=", "55")]),
    ("{joueur} enroule sa frappe après un contrôle orienté, le ballon frôle le montant et sort de quelques centimètres !",
     [("Technique", ">=", "78")]),
    ("Lancé plein axe, {joueur} déclenche à pleine vitesse et voit son tir s'écraser loin du cadre !",
     [("Pace", ">=", "85")]),
    ("{joueur} reprend de volée une balle mal dégagée, mais le tir s'envole bien trop haut !",
     []),
    ("Dans l'axe et sans opposition, {joueur} manque complètement sa frappe, qui prend la direction du virage !",
     [("Finishing", "<=", "40")]),
    ("{joueur} aperçoit le gardien avancé et tente le lob, mais ajuste mal et dépasse largement la barre !",
     [("Vision", ">=", "80")]),
    ("Après avoir éliminé un défenseur de {adversaire}, {joueur} enclenche trop vite sa frappe et la décale loin de la lucarne !",
     [("Technique", ">=", "75")]),
    ("Idéalement placé aux abords des seize mètres, {joueur} cadre mal sa frappe, qui rase le poteau de très peu !",
     [("Finishing", ">=", "80")]),
    ("{joueur} déborde sur l'aile, ferme l'angle et tire, mais le ballon traverse la surface sans trouver preneur !",
     [("Pace", ">=", "82")]),
    ("Sur une frappe instantanée aux seize mètres, {joueur} voit le cuir lui échapper et mourir très loin de sa cible !",
     [("Technique", "<=", "55")]),
    ("{joueur} se laisse surprendre par le rebond et expédie le ballon dans les gradins sans même cadrer !",
     []),
    ("Pourtant bien placé, {joueur} précipite sa conclusion face au but et passe nettement à côté !",
     [("minute", ">=", "75")]),
    ("La frappe de {joueur}, déclenchée de loin, flotte longtemps avant de se perdre dans un ciel dégagé !",
     []),
    ("Dos au but, {joueur} pivote d'un coup et décoche une frappe qui ne cadre pas !",
     [("Technique", ">=", "78")]),
    ("{joueur} s'y reprend d'un angle impossible, le ballon longe le poteau et sort pour un six mètres !",
     [("Finishing", ">=", "78")]),
    ("{joueur} déclenche une frappe lourde dans l'axe, mais le cuir s'écrase derrière le but !",
     []),
    ("Après un contrôle raté, {joueur} s'empresse de frapper et ne cadre pas, pour le plus grand soulagement de {adversaire} !",
     [("Finishing", "<=", "60"), ("First Touch", "<=", "55")]),
    ("{joueur} s'offre une opportunité à vingt mètres, ajuste son tir avec soin, mais ne trouve que le filet extérieur !",
     [("Technique", ">=", "72")]),
    ("Décalé sur sa gauche, {joueur} claque une frappe puissante, mais le ballon passe au-dessus, dans un silence soudain !",
     []),
]

SURNOM = [
    ("Le mitrailleur tire de partout et envoie encore celle-là dans les nuages !",
     [("Long Shots", ">=", "60"), ("Finishing", "<=", "60")]),
    ("L'éclair arrive lancé dans la surface, tire trop vite et envoie le ballon bien au-dessus de la cage !",
     [("Pace", ">=", "90")]),
    ("Le canonnier arme une frappe de mule, mais le ballon finit sa course bien loin des buts !",
     [("preferred_moves", "contient", "Shoots With Power"), ("Finishing", "<=", "70")]),
    ("L'artiste tente un geste de haute voltige dans l'axe, mais la frappe frôle le montant !",
     [("Technique", ">=", "90")]),
    ("Le stratège repère la sortie du gardien et tente un lob inspiré, qui passe juste au-dessus !",
     [("Vision", ">=", "85")]),
    ("Le renard des surfaces se retrouve seul et rate son rendez-vous, le ballon file dans le décor !",
     [("Finishing", ">=", "85")]),
]

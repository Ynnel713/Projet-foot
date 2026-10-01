"""Pilote FAUTE_SIMPLE -- VALIDE (voir pilotes_v2/STATUT.md). 26 phrases
(20 DEFAUT + 6 SURNOM). Audits passes : n-grammes (0 collision), structurel
(1 signal, verifie faux positif -- "se" capte comme pseudo-verbe sur deux
reflexifs reellement differents, #13/#17), sequence (seed=42, tient).
Le doublon structurel reel trouve lors de la relecture (#4/#12, meme scene
"oblige de fauter faute d'option" avec vocabulaire different) est deja
corrige dans ce fichier -- #12 utilise desormais le verbe "bouscule" avec
une circonstance differente de #4."""

DEFAUT = [
    ("{joueur} accroche le maillot de son adversaire et concède une faute évidente sans la moindre contestation !",
     [("Tackling", "<=", "55")]),
    ("D'un geste réflexe, {joueur} retient son adversaire par le bras et l'arbitre siffle sans hésiter !",
     [("Aggression", ">=", "55"), ("Aggression", "<=", "75")]),
    ("{joueur} arrive une fraction de seconde trop tard sur l'intervention et fauche involontairement son vis-à-vis !",
     [("Tackling", "<=", "60")]),
    ("Pris de vitesse, {joueur} n'a d'autre choix que de stopper {adversaire} par une faute tactique assumée !",
     [("Pace", "<=", "65")]),
    ("{joueur} pousse légèrement son adversaire dans le dos pour gagner sa position, l'arbitre ne laisse rien passer !",
     [("Aggression", ">=", "50"), ("Aggression", "<=", "70")]),
    ("Sur un ballon aérien disputé, {joueur} déborde largement du jeu et écope d'un coup franc sans discussion possible !",
     [("Strength", ">=", "70")]),
    ("{joueur} se jette un peu tôt dans l'intervention et cède une faute évitable à l'entrée du milieu de terrain !",
     [("Vision", "<=", "60")]),
    ("{joueur} repousse instinctivement le ballon de la main, l'arbitre n'hésite pas à sanctionner !",
     []),
    ("{joueur} coupe la course de {adversaire} d'une légère retenue, suffisante pour faire tomber le coup de sifflet !",
     [("Aggression", ">=", "55")]),
    ("Fatigué par l'effort, {joueur} n'arrive plus à suivre le rythme et craque sur une dernière course perdue d'avance !",
     [("Pace", "<=", "60"), ("minute", ">=", "75")]),
    ("{joueur} intervient un peu fort sur le pied d'appui de {adversaire}, sans intention de nuire !",
     [("Tackling", "<=", "58")]),
    ("Dépassé par le dribble, {joueur} bouscule {adversaire} dans sa course, l'arbitre ne voit que l'infraction !",
     [("Tackling", "<=", "62"), ("Vision", "<=", "65")]),
    ("{joueur} se place devant {adversaire} et le déséquilibre d'une épaule, sans vraiment chercher le contact !",
     [("Aggression", ">=", "45"), ("Aggression", "<=", "65")]),
    ("D'une charge un peu appuyée, {joueur} déséquilibre son adversaire et l'arbitre ne tergiverse pas !",
     [("Strength", ">=", "75"), ("Aggression", "<=", "60")]),
    ("{joueur} tente sa chance sur l'interception mais touche l'homme avant le ballon !",
     [("Tackling", "<=", "65")]),
    ("Pressé par le temps, {joueur} commet une faute frustrée après avoir perdu son duel !",
     [("minute", ">=", "80"), ("Aggression", ">=", "50")]),
    ("{joueur} se fait surprendre par un une-deux et ne peut qu'accrocher {adversaire} pour l'arrêter !",
     [("Vision", "<=", "58")]),
    ("D'une main agacée, {joueur} repousse {adversaire} après une perte de balle frustrante !",
     [("Aggression", ">=", "60"), ("Aggression", "<=", "78")]),
    ("{joueur} ralentit délibérément le jeu par une faute calculée, loin de sa propre surface !",
     [("Vision", ">=", "75"), ("Aggression", "<=", "55")]),
    ("Sur une remise manquée, {joueur} retient {adversaire} par maladresse plus que par intention !",
     [("Technique", "<=", "60")]),
]

SURNOM = [
    ("Le malin sacrifie une faute tactique au bon moment, sans jamais se faire prendre en défaut par l'arbitre !",
     [("Vision", ">=", "82"), ("Aggression", "<=", "55")]),
    ("L'agacé n'accepte pas de se faire déborder et répond par une faute franche sur {adversaire} !",
     [("Aggression", ">=", "70")]),
    ("Le maladroit intervient avec dix bonnes intentions et une seule mauvaise jambe, faute inévitable !",
     [("Tackling", "<=", "50")]),
    ("Le vétéran dégaine la faute tactique avec un sens du timing qui n'appartient qu'à lui !",
     [("age", ">=", "32"), ("Vision", ">=", "80")]),
    ("Le discret tire doucement le maillot de {adversaire}, suffisamment pour casser l'élan sans se faire remarquer !",
     [("Technique", ">=", "70"), ("Aggression", "<=", "50")]),
    ("Le pressé se précipite dans un duel qu'il n'avait pas à jouer et récolte une faute qu'il aurait pu éviter !",
     [("Pace", "<=", "55")]),
]

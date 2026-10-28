# Carte des attributs V2 : le rayon propre de chaque attribut

> 25/10/2026, à la demande du propriétaire. Pour **chacun des 47 attributs** de la base (plus 5 autres colonnes) :
> - **Rayon propre** : ce qu'il pilote, et que lui seul pilote.
> - **Ne pilote pas** : la frontière avec ses voisins, pour éviter qu'un attribut en « mange » un autre.
> - **Où on le voit** : la différence visible entre un joueur moyen et un très bon.
> - **Liens** : les attributs avec lesquels il se combine, sans se confondre.
> - **État** : déjà branché, à revoir (voir [REVUE_ATTRIBUTS_V2.md](REVUE_ATTRIBUTS_V2.md)), ou à créer (phase du plan V2).
>
> Règle de fond (validée) : **physique = capacité ; mental = usage de la capacité ; technique = qualité d'exécution ; gardien = rôle spécifique.** Chaque attribut doit s'exprimer dans le comportement d'au moins une situation de jeu. Un attribut qui ne change rien de visible n'est pas branché.

---

## A. Physique : la capacité du corps (8)

| Attribut | Rayon propre | Ne pilote pas | Où on le voit (moyen contre très bon) | Liens | État |
|---|---|---|---|---|---|
| **Pace** | Vitesse maximale, et rien d'autre | quand il sprinte (mental), la montée en vitesse (Acceleration) | Sur une course lancée où les deux sprintent, le rapide prend 3-4 m sur 30 m | Acceleration (le couple « inarrêtable ») | branché ; aussi capacité dans la hauteur de ligne (ticket v2-collectif/05 : marge laissée derrière l'attaquant le plus avancé selon l'écart de vitesse, règle R5) ; à revoir (socle 02) |
| **Acceleration** | Temps pour atteindre sa vitesse max (les 5-10 premiers mètres) | la vitesse de pointe | Gagne le premier mètre : départ d'appel, sortie de dribble, retour au pressing | Pace (diesel ou sprinter court) ; Agility | branché ; à recaler sur les temps réels |
| **Agility** | Changer de direction, freiner, se retourner sans perdre de vitesse | la vitesse en ligne droite, l'équilibre au contact | Dribbleur qui crochète sans ralentir ; défenseur qui suit le crochet ; gardien qui plonge et se relève vite | Dribbling ; Balance | à créer (étape duels) |
| **Balance** | Rester debout et continuer l'action APRÈS un contact | gagner le contact (Strength) | Après une bousculade, le très bon continue sa conduite ou sa frappe ; le moyen tombe ou perd le ballon | Strength (gagner contre rester debout) | branché ; à revoir (après le contact) |
| **Strength** | Gagner le duel de contact (épaule, dos au but, protection du ballon) | rester debout (Balance), le tacle au pied (Tackling) | Point d'appui dos au but ; repousse au marquage sur corner | Balance ; Jumping Reach dans le duel aérien | branché ; à revoir (duel de contact distinct) |
| **Jumping Reach** | Hauteur atteinte en saut (s'ajoute à la taille) | la qualité de la tête une fois au contact (Heading) | Premier au ballon aérien, même face à un plus grand | Taille ; Heading ; Bravery | à créer (phase 7) |
| **Stamina** | Taille et recharge de la réserve d'énergie pendant le match | l'envie de courir (Work Rate) | À effort égal, le très bon garde ses sprints jusqu'à la 90e, le moyen ralentit à partir de la 60e-70e | **Work Rate** (lien étroit : l'envie consomme la réserve) | branché ; à revoir (réserve qui dépend de l'effort) |
| **Natural Fitness** | Récupération entre les matchs, blessures, déclin avec l'âge | rien pendant le match | Fraîcheur en début de match dans un calendrier chargé | Stamina | à créer (branchement aux compétitions, D-V10) |

## B. Mental : l'usage de la capacité et la lecture du jeu (14)

| Attribut | Rayon propre | Ne pilote pas | Où on le voit | Liens | État |
|---|---|---|---|---|---|
| **Work Rate** | Volume et intensité des efforts **sans ballon** : pressing, repli, couverture | les appels offensifs (Off the Ball), la capacité (Stamina) | Le bas fait du faux pressing à l'économie et marche au repli ; le haut presse et revient sans compter | **Stamina** ; Teamwork ; Aggression | à créer (socle 02) |
| **Off the Ball** | Volume, moment et qualité des **appels offensifs** | les efforts défensifs (Work Rate) | Le haut multiplie les appels dans le dos, au bon moment ; le bas attend le ballon dans les pieds | Work Rate (intensité de l'appel) ; Vision du passeur | branché (choix de l'espace ; respect de la ligne du hors-jeu, ticket v2-collectif/23 : 99 → 95 %, 55 → 75 %, 11 → 55 %) ; volume et intensité à créer (socle 02) |
| **Teamwork** | Discipline collective : tenir et reprendre sa place, choisir l'option qui sert l'équipe | l'envie de courir (Work Rate), le choix optimal (Decisions) | Le haut garde le bloc compact et donne au mieux placé ; le bas quitte sa zone et force seul | Positioning ; Decisions | branché pour tenir sa place (ticket v2-collectif/04 : écart toléré avant de se replacer) et pour suivre la montée de la ligne sans retard (ticket v2-collectif/23 : 99 → 0 s, 55 → 0,75 s, 11 → 1,5 s) ; l'option qui sert l'équipe reste à créer |
| **Decisions** | Choisir la bonne option au bon moment (tirer, passer, conduire, tacler, attendre) | les options vues (Vision), l'exécution (techniques) | Le bas tire alors qu'un partenaire est seul ; le haut ne force jamais | Vision ; Composure | branché ; à revoir (erreurs crédibles) |
| **Vision** | Quelles options le joueur **voit** (passes longues, entre les lignes, changements de jeu) | le choix (Decisions), la réussite (Passing) | Le haut voit la passe dans le dos de la défense ; le bas ne voit que le voisin | Passing ; Decisions | branché |
| **Anticipation** | Lire l'action avant qu'elle arrive : délai de réaction, lecture des passes et des rebonds | la vigilance dans la durée (Concentration) | Le haut démarre avant les autres et intercepte ; le bas arrive après la bataille | Concentration ; Positioning | branché ; voit le drapeau du hors-jeu et attend le sifflet (ticket v2-collectif/23 : 99 → 70 %, 55 → 45 %, 11 → 20 %) |
| **Concentration** | Garder sa vigilance tout le match : probabilité de « trous » (oubli de marquage, réaction tardive) qui augmente en fin de match et juste après un but | la qualité de lecture (Anticipation) | Le bas a des absences, surtout en fin de match et après avoir marqué ; le haut est régulier | Anticipation ; Marking ; Stamina (fatigue) | à créer (phase 6) |
| **Positioning** | Placement **défensif de zone** sans adversaire désigné : tenir la ligne, fermer les couloirs, couvrir | suivre un adversaire précis (Marking) | Le haut est toujours au bon endroit sans courir ; le bas laisse des trous entre les lignes | Marking ; Anticipation ; Teamwork | branché sans ballon (ticket v2-collectif/04 : erreur de placement dans le bloc) ; couvrir reste à créer (ticket 07) |
| **Flair** | Tendance à tenter l'inattendu (geste rare, passe aveugle, dribble au lieu de la passe simple) | la réussite du geste (Technique, Dribbling) | Le haut surprend une défense fermée et perd plus de ballons ; le bas joue simple et prévisible | Technique ; Decisions | ticket v2-cerveau-joueurs/05 |
| **Composure** | Amortir la **pression** sur toutes les actions (adversaire proche, moment clé) | la qualité de base de l'action | Sous pression, le haut garde sa précision ; le bas se précipite. Sans pression : aucune différence | Finishing ; Passing ; First Touch | branché (passe et contrôle sous pression, v2-socle/04 ; tir sans condition : dérogation A2) |
| **Determination** | Garder l'intensité et la qualité quand ça tourne mal : mené au score, fin de match, après une erreur | l'effort de base (Work Rate) | Mené 0-2 à la 80e, le haut est toujours à 100 % ; le bas baisse les bras | Work Rate ; Leadership | à créer (phase 10) |
| **Aggression** | Engagement au contact : tôt et fort, ou temporiser ; risque de faute et de carton | la qualité du geste (Tackling) | Le haut récupère haut et fait des fautes ; le bas laisse l'adversaire se retourner | Tackling ; Bravery ; Work Rate (pressing) | branché ; à revoir (socle 03) |
| **Bravery** | Accepter le contact risqué : tête dans la mêlée, contrer un tir, plonger dans les pieds | l'envie d'aller au contact au sol (Aggression) | Le haut bloque les frappes et va au duel aérien ; le bas retire la jambe | Jumping Reach ; Heading ; Aggression | à créer (phase 7) |
| **Leadership** | Effet sur les **coéquipiers** : amortit la baisse de moral après un but encaissé | son propre jeu | Une équipe avec un vrai leader décroche moins quand le match tourne mal | Determination des coéquipiers | à créer (phase 10) |

## C. Technique de champ : la qualité d'exécution (14)

| Attribut | Rayon propre | Ne pilote pas | Où on le voit | Liens | État |
|---|---|---|---|---|---|
| **First Touch** | Réception : contrôle simple, contrôle orienté, contrôle raté | le geste qui suit (Technique, Passing) | Sur un ballon rapide ou sous pression, le haut oriente en un temps ; le bas perd une seconde | Composure ; Technique | branché ; à revoir (difficulté, contrôle orienté) |
| **Passing** | Exécution de la passe : réussite selon la difficulté, et **dosage** (vitesse, dans la course) | voir l'option (Vision), centrer (Crossing) | Passes faciles : la différence est dans le dosage ; passes difficiles : écart énorme | Vision ; Technique ; Decisions | branché ; à revoir (difficulté et dosage) |
| **Technique** | Gestes **difficiles** : une touche, volée, extérieur, contrôle en pleine course | les gestes simples | Sur un geste difficile, le haut réussit, le bas joue simple ou rate | First Touch ; Flair | branché ; à revoir (gestes difficiles seulement) |
| **Dribbling** | Conduite serrée et élimination en un contre un | la vitesse (Pace), les changements de direction du corps (Agility) | Le haut élimine et attire deux défenseurs ; le bas perd le ballon au premier contact | Agility ; Balance ; Flair | à créer (étape duels) |
| **Crossing** | Précision et trajectoire des centres depuis les côtés | la passe au sol (Passing) | Le haut met le ballon dans la zone de l'attaquant ; le bas dans le premier défenseur | Heading des attaquants | à créer (phase 7) |
| **Finishing** | Placement du tir **dans la surface** : cadré et loin du gardien | la frappe de loin (Long Shots), le sang-froid (Composure) | Sur grosse occasion, le haut place, le bas tire sur le gardien | Composure ; Technique (volée) | branché ; à revoir (placement, difficulté) |
| **Long Shots** | Précision et puissance des frappes de plus de 20 m | la finition dans la surface | Le haut cadre de 25 m et oblige le bloc à sortir ; le bas tire dans les tribunes | Decisions (tenter ou non) | à créer (phase 7) |
| **Heading** | Qualité de la tête une fois au contact : direction, puissance | arriver au ballon (Jumping Reach, taille) | Le haut cadre et dégage loin ; le bas met des têtes sans direction | Jumping Reach ; Bravery | à créer (phase 7) |
| **Tackling** | Qualité du geste défensif : timing, propreté, réussite | l'envie d'engager (Aggression), le contact épaule (Strength) | Le haut récupère proprement en tentant peu ; le bas plonge trop tôt et fait faute | Aggression ; Anticipation | branché ; à revoir (socle 03, timing) |
| **Marking** | Suivre et neutraliser **un adversaire désigné** | le placement de zone (Positioning) | Le haut colle à son attaquant, même sur corner ; le bas le perd dans son dos | Concentration ; Positioning | à créer (phase 6) |
| **Corners** | Qualité des corners | les centres dans le jeu (Crossing) | Corner sur un point de chute exploitable, ou dans le premier poteau adverse | Heading des receveurs | à créer (phase 8) |
| **Free Kick Taking** | Qualité des coups francs, directs et indirects | le tir dans le jeu | Menace directe à 20-25 m, ou ballon dans le mur | Technique | à créer (phase 8) |
| **Long Throws** | Distance et précision des touches longues | — | Une touche dans le camp adverse devient quasiment un corner | Strength | à créer (phase 8) |
| **Penalty Taking** | Qualité du tir au but sur penalty | la finition dans le jeu | Peu de penalties ratés ; la lucidité vient de Composure | Composure | à créer (phase 8) |

## D. Gardien (11, plus Passing, First Touch et Technique déjà renseignés pour les gardiens)

| Attribut | Rayon propre | Ne pilote pas | Où on le voit | Liens | État |
|---|---|---|---|---|---|
| **Reflexes** | Arrêts sur tirs proches et rapides (temps de réaction court) | le placement, les face-à-face | Sort la frappe à bout portant et la déviation | Agility | branché ; à revoir (tirs proches seulement) |
| **One on Ones** | Gagner le face-à-face : moment de la sortie, fermer l'angle, rester debout | les tirs avec défenseurs devant lui | Le haut annule l'occasion franche ; le bas plonge trop tôt | Rushing Out | branché ; à revoir (face-à-face seulement) |
| **Handling** | Ce qui arrive APRÈS l'arrêt : captée ou repoussée (et où) | la chance d'arrêter | Le haut capte ; le bas repousse dans l'axe et offre une seconde occasion | Punching | branché ; à revoir (après l'arrêt) |
| **Aerial Reach** | Portée sur ballon aérien (hauteur, distance) | la décision de sortir (Command of Area) | Capte des centres loin de sa ligne | Taille ; Jumping Reach | à créer (phase 9) |
| **Command of Area** | Décider de sortir sur les centres et dominer sa surface | la portée (Aerial Reach) | Sort chercher les centres ; le bas reste collé à sa ligne | Aerial Reach ; Communication | à créer (phase 9) |
| **Communication** | Organiser la défense : effet sur le placement des défenseurs, moins de collisions | ses propres arrêts | Défense mieux placée devant un gardien qui parle | Positioning des défenseurs | à créer (phase 9) |
| **Kicking** | Dégagements longs : distance, précision | la relance à la main | Lance une contre-attaque directement sur l'attaquant | Passing | à créer (phase 9) |
| **Throwing** | Relance à la main : distance, précision | le jeu au pied | Relance rapide qui lance une contre-attaque | Decisions | à créer (phase 9) |
| **Rushing Out** (tendance) | Hauteur de placement et sorties hors de la surface (libéro) | la qualité du face-à-face | Le haut balaie derrière sa défense et permet une ligne haute, avec le risque d'être lobé | One on Ones ; Positioning de la ligne | à créer (phase 9) |
| **Punching** (tendance) | Boxer plutôt que capter sur les centres | la réussite de la sortie | Le haut éloigne le danger mais rend la possession | Handling | à créer (phase 9) |
| **Eccentricity** (tendance) | Goût du risque : dribbles dans sa surface, sorties inattendues | la qualité des gestes | Imprévisible : peut sauver ou couler son équipe | Rushing Out ; Flair | à créer (phase 9) |

## E. Autres colonnes de la base

| Colonne | Rayon propre | État |
|---|---|---|
| **Weak foot** | Précision et fréquence d'usage du mauvais pied : toute action du côté faible est plus difficile | à créer (phase 10 ; 526 valeurs manquantes) |
| **Pieds** (fort) | Côté naturel de frappe, de centre et de course | à créer (phase 10 ; vide pour 61 % des lignes) |
| **Taille** | S'ajoute à Jumping Reach et Aerial Reach dans le jeu aérien | à créer (phase 7) |
| **Preferred moves** | Habitudes qui biaisent le choix d'action (« Runs With Ball Often »…), indépendamment des notes | à créer (phase 10) |
| **Postes naturels** | Hors de son poste : pénalité sur Positioning, Decisions et Marking | à créer (phase 10) |

---

## Les liens étroits, sans confusion

Chaque paire ci-dessous se combine, mais chaque attribut garde son rayon.

| Paire | Qui fait quoi |
|---|---|
| Work Rate + Stamina | l'envie de courir consomme la réserve ; Work Rate haut et Stamina basse épuisent le joueur avant la 60e |
| Pace + Acceleration | vitesse de pointe, et temps pour y arriver |
| Strength + Balance | gagner le contact, puis rester debout après |
| Vision → Decisions → Passing | voir l'option, la choisir, la réussir |
| Anticipation + Concentration | lire l'action, et rester vigilant dans la durée |
| Positioning + Marking | tenir sa zone, et suivre un adversaire précis |
| Off the Ball + Work Rate | appels offensifs, et efforts défensifs |
| Jumping Reach + Taille → Heading | arriver au ballon, puis bien le jouer de la tête |
| Finishing + Composure + Long Shots | placer dans la surface, rester lucide sous pression, frapper de loin |
| First Touch → Technique → Dribbling | recevoir, réussir le geste difficile, éliminer |
| Aggression + Tackling | l'envie d'engager, et la qualité du geste |
| Reflexes / One on Ones / Handling | arrêt réflexe, face-à-face, puis captée ou repoussée |

## Interactions et règle anti double comptage (ticket v2-collectif/18, validé le 26/10/2026)

### La règle

| # | Règle | En simple |
|---|---|---|
| R1 | **Un effet, un attribut responsable.** Un effet est un changement mesurable de comportement ou de réussite dans une situation donnée. | Si Anticipation fait déjà démarrer plus tôt, aucun autre attribut ne donne ce même bonus. |
| R2 | **Les attributs s'enchaînent par les temps du cerveau** (perception, décision, exécution, ADR 0001), chacun avec son propre tirage. Pas de mélange « 0,8 × A + 0,2 × B » dans une même probabilité. | Vision montre la passe, Decisions la choisit, Passing la réussit : trois étapes, pas une moyenne. |
| R3 | **Un attribut modulateur n'agit que dans sa condition**, en réduisant un facteur de difficulté : Composure (pression), Concentration (fatigue, après un but), Determination (score défavorable). | Sans pression, Composure ne change rien. |
| R4 | **Les effets indirects ne visent que les coéquipiers** : Leadership, Communication. | Leadership aide la coordination, pas la précision de ses propres passes. |
| R5 | **Le physique est une capacité**, utilisée partout où le joueur se déplace ou doit arriver à temps ; ce n'est pas un bonus supplémentaire. | Pace sert à la course et au test « peut-il couper la passe ? » : c'est la même vitesse. |

**Plafond d'écart.** Entre 99 et 11, l'écart mesuré sur un indicateur reste dans la fourchette réelle quand elle est connue (test de profils, `scripts/measure_v2.py --profil`).

**Garde automatique.** `tests/test_v2engine_rayon_attributs.py` analyse l'arbre syntaxique du moteur. Il échoue si :
- un attribut est lu hors des modules de son rayon, ou avec un nom non littéral ;
- une note est lue directement dans `.attributes` hors de `attributes.py` ;
- une capacité physique (`.pace`, `.acceleration`, `.stamina`) est lue hors des modules qui en ont besoin (R5) ;
- un calcul combine des notes de plusieurs attributs hors des dérogations listées (A2, A3, A8) ;
- une entrée de la liste devient périmée (dérogation levée sans mise à jour).

Limite connue : un mélange qui passe par des variables intermédiaires n'est pas détecté ; la grille de relecture le couvre.

### Les interactions du guide

| Paire | Rôle de chacun | Combinaison | État (26/10/2026) | Branchement |
|---|---|---|---|---|
| Anticipation + Positioning | A : lire tôt ; P : être déjà au bon endroit | P place, A déclenche plus tôt | A et P branchés (P : ticket 04) ; à combiner | Tickets collectif 05, 09 |
| Vision + Decisions + Passing | V : voir ; D : choisir ; P : réussir et doser | Chaîne en trois tirages | Conforme | — |
| Off the Ball + Acceleration + Pace | OtB : quand et où faire l'appel ; Acc : le premier mètre ; Pace : la pointe | OtB choisit, le physique exécute | OtB branché ; Acc à recaler | Tickets 12, 16 |
| Work Rate + Stamina | WR : combien d'efforts ; St : la réserve | WR consomme, St limite | WR non branché | Ticket 12 |
| Teamwork + Positioning | T : vouloir tenir sa place ; P : savoir où elle est | P calcule la place, T décide d'y rester | Conforme (ticket 04, deux temps distincts dans `bloc.py`) | Ticket 09 |
| Dribbling + Flair + Decisions | F : tenter ; D : bon moment ; Dr : réussir | Tendance, choix, exécution | À créer | Étape duels, ticket 19 |
| Concentration + Anticipation | C : risque de trou d'attention ; A : qualité de lecture | C peut annuler une lecture, jamais l'améliorer | C à créer | Ticket 09 |
| Crossing + Vision + Decisions | V : voir le centre ; D : moment ; Cr : trajectoire | Chaîne | À créer | Phase 7 |
| Composure + Finishing | F : placement du tir ; C : seulement la part due à la pression | C réduit la gêne (R3) | Non conforme (dérogation A2) | Ticket du tir |
| Pace + Acceleration + Positioning | P : se placer tôt ; Acc et Pace : rattraper | P réduit le besoin de vitesse | Pace branché dans la hauteur de ligne (ticket 05, capacité seule) ; Acceleration non utilisée ; P tient sa place (ticket 04) | Repli préventif : ticket 10 |

### Audit du moteur (26/10/2026)

| # | Constat | Verdict | Suite |
|---|---|---|---|
| A1 | Tacle : réussite à 0,8 × Tackling + 0,2 × Aggression, alors qu'Aggression règle déjà la fréquence et la faute | Double comptage (R1, R2) | **Corrigé** : réussite selon Tackling seul |
| A2 | Tir : qualité à 0,8 × Finishing + 0,2 × Composure, même sans pression | Double comptage (R2, R3) | **Dérogation** jusqu'au ticket du tir (il faut d'abord une pression sur le tir, donc une nouvelle constante) |
| A3 | Porteur au tacle : Strength et Balance à égalité, Dribbling absent | Écart à la carte (Balance joue après le contact) | **Dérogation** jusqu'à l'étape duels |
| A4 | First Touch : réussite du contrôle et temps de réception. La pression du receveur joue aussi deux fois : elle rend le contrôle plus difficile (modulée par Composure) et raccourcit le temps de réception (sans Composure). Passing règle aussi deux choses : la réussite et le dosage, qui pèse sur la difficulté du contrôle | Conforme : ce sont deux facettes du contrôle orienté (et de la passe). Pour le temps de réception, la pression ne rend pas le geste plus difficile, elle oblige à jouer plus vite : ce n'est pas une difficulté, donc Composure n'a pas à l'amortir (R3) | — |
| A5 | Composure réduit la pression sur la passe et le contrôle | Conforme (R3) | — |
| A6 | Pace dans le test « peut-il couper la passe ? » | Conforme (R5) | — |
| A7 | Off the Ball choisit le meilleur espace selon la note | Conforme (qualité de l'appel) ; Decisions garde le choix du porteur | — |
| A8 | Gardien : note à 0,5 × Reflexes + 0,3 × One on Ones + 0,2 × Handling pour tous les tirs, alors que la section D réserve Reflexes aux tirs proches, One on Ones aux face-à-face, et que Handling ne règle pas l'arrêt | Mélange (R2) et écart à la carte | **Dérogation** jusqu'à la phase 9 (gardien complet), confirmée par le propriétaire le 26/10/2026 |
| A9 | Valeur d'une passe pour le porteur : la réussite compte déjà un receveur marqué (adversaire à moins de 2 m) et l'ouverture (`1 - pression`, sur 5 m) le pénalise une seconde fois | Double comptage d'une situation (R1), pas d'un attribut | **Reporté** au ticket collectif 13 (valeur future d'une passe), qui refait cette évaluation |
| A10 | Hors-jeu (ticket v2-collectif/23) : Off the Ball est lu dans `offside.py` (et non dans `off_ball.py`), Anticipation dans `match.py` (et non dans `anticipation.py`) | Conforme : ce sont deux effets nouveaux et distincts -- régler l'appel sur la ligne, voir le drapeau et attendre le sifflet -- un attribut chacun (R1). La carte et `tests/test_v2engine_rayon_attributs.py` sont étendus en conséquence | — |
| A11 | Hors-jeu : le porteur écarte les coéquipiers qu'il voit nettement au-delà de la ligne (`PASS_OFFSIDE_MARGIN_M`, 0,5 m) | Ce n'est pas un attribut : c'est l'information du joueur, comme la Vision pour la portée d'une passe. Sans ce filtre, le porteur servait délibérément un joueur cinq mètres hors-jeu (21,5 hors-jeu par match mesurés) | — |

### Grille de relecture (à cocher dans chaque ticket, vérifiée par `simulafoot-reviewer`)

1. Chaque effet ajouté a-t-il un seul attribut responsable, conforme à son rayon dans cette carte ? (R1)
2. Les attributs qui se combinent passent-ils par des tirages distincts (perception, décision, exécution), sans mélange pondéré ? (R2)
3. Un attribut modulateur n'agit-il que dans sa condition, en réduisant une difficulté ? (R3)
4. Un effet indirect ne vise-t-il que les coéquipiers ? (R4)
5. L'écart entre 99 et 11 reste-t-il dans la fourchette réelle connue, mesuré avec `--profil` ? (plafond d'écart)

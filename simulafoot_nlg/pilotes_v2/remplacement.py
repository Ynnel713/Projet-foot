"""Pilote REMPLACEMENT -- EN ATTENTE DE VALIDATION (voir pilotes_v2/STATUT.md).
21 phrases (16 DEFAUT + 5 SURNOM). Frequence ~5-8/match, d'ou un pool plus
court que les scenarios Tier 1 plus rares.

Slots : {sortant}, {entrant}, {club}, {minute} -- nouveau patron a deux
joueurs sur le modele passeur/receveur (PLAN_V2_EDITORIAL.md).

CONVENTION A VALIDER PAR L'ARCHITECTE : la grammaire de conditions
(engine/conditions.py) evalue UN seul Player, sans prefixe. Toutes les
conditions de ce pilote portent donc sur l'ENTRANT, et chaque SURNOM est
le surnom de l'entrant ("Le vétéran entre à la place de {sortant}"). Les
conditions sur le SORTANT du plan ("age(sortant) >= 32", "fm_rating(sortant)
<= 60") ne sont pas exprimables sans extension de la grammaire -- non ecrites.

score_context : volontairement NON utilise. Ses valeurs
(SCORE_CONTEXT_VALUES) decrivent l'effet d'un BUT ; "remplacement
defensif / offensif" demanderait de nouvelles valeurs (menant / mene /
egalite) calculees par le moteur. Toutes les phrases sont donc neutres vis-a-vis
du score (aucune ne dit "proteger l'avantage" ni "chercher l'egalisation") :
une telle phrase sortirait a contresens.

Decisions de l'architecte du 01/10/2026 : score_context hors perimetre (dette
v2.1, SPEC_ANTI_REPEAT.md section 5), gardiens dans vétéran/joker acceptes
(limitation documentee), option C (selecteur choisit la variante selon le
profil du remplacement) ACTEE comme architecture cible -- ce pilote reste
ecrit sous l'option A (conditions sur l'entrant), compatible avec C ; scission
en sous-variantes defensif/offensif = tache V2.1 (SPEC_ANTI_REPEAT.md, section 5).

"Retour de blessure" (demande initiale) : AUCUNE donnee en base (players.status
ne porte pas de valeur blesse/retour) -- surnom non ecrit, pas de fantome.

Attributs : age (100 %), fm_rating (100 %), Pace/Stamina/Technique/Work Rate
(82-93 %, base FM26), minute (contexte de match). Pas de height_cm."""

DEFAUT = [
    ("Changement chez {club} : {entrant} remplace {sortant} à la {minute}e minute.",
     []),
    ("{sortant} cède sa place à {entrant}, qui entre en jeu sous les applaudissements.",
     []),
    ("Dernier ajustement tactique : {entrant} succède à {sortant} pour boucler la partie.",
     [("minute", ">=", "75")]),
    ("{sortant} rejoint le banc et {entrant} s'installe sur la pelouse, prêt à peser sur le jeu.",
     []),
    ("Du sang neuf : {entrant} apporte sa vitesse à {club}, tandis que {sortant} s'efface !",
     [("Pace", ">=", "78")]),
    ("Sur le banc, {entrant} est une carte de poids : il relève {sortant} et change l'allure de la rencontre !",
     [("fm_rating", ">=", "81")]),
    ("Des jambes fraîches : {entrant} entre pour {sortant}, avec un réservoir encore plein.",
     [("Stamina", ">=", "75"), ("minute", ">=", "60")]),
    ("Le banc lance un jeune : {entrant} hérite du poste de {sortant} et tente sa chance.",
     [("age", "<=", "21")]),
    ("Pour gérer les derniers instants, l'entraîneur fait confiance à l'expérience de {entrant}, qui relève {sortant}.",
     [("age", ">=", "33"), ("minute", ">=", "70")]),
    ("Changement précoce : {sortant} s'en va après {minute} minutes de jeu, remplacé par {entrant} !",
     [("minute", "<=", "55")]),
    ("Dans le money time, {club} lance {entrant} dans la bataille pendant que {sortant} file s'asseoir.",
     [("minute", ">=", "85")]),
    ("Coup de sifflet de l'arbitre : {sortant} sort, {entrant} entre, et {club} repart avec un autre visage.",
     []),
    ("Changement de rotation : {entrant} prend le relais de {sortant}, avec pour consigne de maintenir l'équilibre.",
     []),
    ("Dès son entrée, {entrant} presse comme un forcené, {sortant} ayant déjà rejoint le banc !",
     [("Work Rate", ">=", "80")]),
    ("{entrant} débarque pour {sortant}, avec l'idée d'apporter de la fluidité dans le jeu de {club} !",
     [("Technique", ">=", "78")]),
    ("Un remaniement à bas bruit : une tape sur l'épaule, et {entrant} relève {sortant} sur le terrain.",
     []),
]

SURNOM = [
    ("Le vétéran remplace {sortant}, et sa seule présence rassure tous ses coéquipiers !",
     [("age", ">=", "34")]),
    ("La pépite fait son entrée pour {sortant} sous les regards impatients du public !",
     [("age", "<=", "18")]),
    ("L'éclair déboule pour {sortant} et met aussitôt le feu au match !",
     [("Pace", ">=", "90")]),
    ("Le poumon vient relever {sortant} et promet de courir jusqu'au coup de sifflet final !",
     [("Stamina", ">=", "85"), ("minute", ">=", "70")]),
    ("Le joker sort du banc à la place de {sortant}, un luxe que peu d'équipes peuvent s'offrir !",
     [("fm_rating", ">=", "82")]),
]

# 07: Duels : Agility, Dribbling, Balance après contact

**What to build:** `docs/CARTE_ATTRIBUTS_V2.md` renvoie Agility et Dribbling à une « étape duels » qui n'existe ni dans `docs/PLAN_V2.md` ni dans les tickets. Brancher :

- **Dribbling** : chance d'éliminer en un contre un et de garder le ballon en conduite serrée (côté porteur du duel de v2-socle/03).
- **Agility** : changer de direction, freiner, se retourner sans perdre de vitesse (porteur qui crochète, défenseur qui suit, gardien qui se relève) ; remplace le freinage commun `DECEL_MAX_MPS2` de v2-collectif/25 par un freinage modulé.
- **Balance** : rester debout et continuer l'action **après** un contact perdu (levée de la dérogation A3).

**Élargissement du 03/11/2026 (revue de réalisme, décision Q13).** Aujourd'hui l'action « dribble » ne fait que garder le ballon et avancer, sans duel un contre un (`decision.py:156`, `match.py:263`) : Dribbling n'a aucun effet. Ce ticket crée le **vrai duel un contre un**, avec des gestes variés choisis par la situation (jamais par un tirage libre) :
- **Contournement** (passer à côté du défenseur), **protection du ballon** (corps entre le ballon et l'adversaire), **crochet** (changement de direction brusque) ;
- côté défenseur, le **tacle glissé** s'ajoute au tacle debout (le geste préféré « Dives Into Tackles » en biaise la fréquence, ticket 09).
Le geste dépend de la distance au défenseur, de l'espace, de la vitesse, de la pression et de la position sur le terrain ; Decisions choisit, Flair ajoute les gestes risqués. Ce ticket est livré **avant la calibration** (`v2-collectif/22`) car il change la forme des duels.

**Attributs :** Dribbling, Agility, Balance.

**Blocked by:** `v2-collectif/33` (le duel un contre un s'insère dans la valeur factuelle de la conduite).

**Status:** découpé (04/11/2026, audit de granularité) en 07a (duel un contre un, Dribbling) et 07b (Agility et Balance). Ticket chapeau : ne pas l'implémenter tel quel ; le texte ci-dessous reste la référence de détail. Une référence à ce ticket sans lettre vaut pour tous ses morceaux.

**Point de vigilance :** Strength gagne le contact, Balance joue après : ne pas compter deux fois (v2-collectif/18).

- [ ] Dribbling élevé : plus de duels gagnés par le porteur, à défenseur égal
- [ ] Le duel un contre un existe (contournement, protection, crochet) et le tacle glissé s'ajoute au tacle debout ; chaque geste est tracé et affiché
- [ ] Test de cohérence (scènes fixes) : le crochet est plus fréquent face à un défenseur proche et lent à se retourner ; la protection est plus fréquente quand le porteur est de dos, au contact ; le tacle glissé est plus fréquent quand le porteur s'échappe
- [ ] Chaque geste apparaît au moins une fois sur 50 matchs et aucun ne domine
- [ ] Agility élevée : moins de vitesse perdue dans un changement de direction (mesuré sur les trajectoires)
- [ ] Balance élevée : plus d'actions poursuivies après un contact perdu ; dérogation A3 levée
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée

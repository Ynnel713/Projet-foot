# 07a: Le vrai duel un contre un (Dribbling)

**Découpé du ticket 07 le 04/11/2026** (audit de granularité). Détail : `07-duels-agility-dribbling.md` (élargissement du 03/11/2026, décision Q13).

**What to build:** aujourd'hui l'action « dribble » ne fait que garder le ballon et avancer (`decision.py:156`, `match.py:263`) : Dribbling n'a aucun effet. Créer le **vrai duel un contre un**, avec des gestes choisis par la situation (jamais par un tirage libre) :
- côté porteur : **contournement**, **protection du ballon**, **crochet** ; Dribbling règle la chance d'éliminer et de garder le ballon en conduite serrée (côté porteur du duel de v2-socle/03) ;
- côté défenseur : le **tacle glissé** s'ajoute au tacle debout (« Dives Into Tackles » en biaise la fréquence, ticket 09a).

Le geste dépend de la distance au défenseur, de l'espace, de la vitesse, de la pression et de la position ; Decisions choisit, Flair ajoute les gestes risqués. Livré **avant la calibration** (`v2-collectif/22a`) car il change la forme des duels.

**Attributs :** Dribbling ; Decisions et Flair (choix du geste).

**Blocked by:** `v2-collectif/33` (livré) : démarrable.

**Bloque :** 09a, 09b ; 10b (dribble du gardien) ; `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** Strength gagne le contact, Balance joue après (07b) : ne pas compter deux fois (v2-collectif/18).

## Acceptance criteria

- [ ] Dribbling élevé : plus de duels gagnés par le porteur, à défenseur égal
- [ ] Le duel un contre un existe (contournement, protection, crochet) et le tacle glissé s'ajoute au tacle debout ; chaque geste est tracé et affiché
- [ ] Test de cohérence (scènes fixes) : le crochet est plus fréquent face à un défenseur proche et lent à se retourner ; la protection est plus fréquente quand le porteur est de dos, au contact ; le tacle glissé est plus fréquent quand le porteur s'échappe
- [ ] Chaque geste apparaît au moins une fois sur 50 matchs et aucun ne domine
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
